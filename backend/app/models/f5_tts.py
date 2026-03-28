"""F5-TTS model — flow matching, zero-shot cloning, 15x realtime.

Install: pip install f5-tts
HuggingFace: SWivid/F5-TTS
"""

from __future__ import annotations

import io
import logging
import wave
from pathlib import Path

from app.models.base import GenerateRequest, GenerateResult, TTSModelBase

logger = logging.getLogger(__name__)


class F5TTSModel(TTSModelBase):
    model_id = "f5-tts"
    model_name = "F5-TTS"
    description = "Flow-matching TTS with zero-shot cloning and 15x realtime speed — MIT license"
    supports_voice_cloning = True
    supports_streaming = False
    supports_speed = False
    supported_languages = ["en", "zh", "de", "fr", "es", "pt", "hi", "ar", "ru", "ja", "ko", "nl"]
    hf_repo = "SWivid/F5-TTS"
    vram_gb_estimate = 3.0

    def __init__(self) -> None:
        self._model = None
        self._device = "cuda"

    def load(self, device: str = "cuda") -> None:
        logger.info("Loading F5-TTS on %s", device)
        self._device = device
        from f5_tts.api import F5TTS

        self._model = F5TTS(device=device)
        self._loaded = True
        logger.info("F5-TTS loaded on %s", device)

    def unload(self) -> None:
        self._model = None
        self._loaded = False
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    # Default reference audio bundled with the f5-tts package
    _DEFAULT_REF_AUDIO = (
        "/usr/local/lib/python3.12/site-packages/f5_tts/infer/examples/basic/basic_ref_en.wav"
    )
    _DEFAULT_REF_TEXT = "Some call me nature, others call me mother nature."

    def generate(self, request: GenerateRequest) -> GenerateResult:
        if not self._loaded or self._model is None:
            raise RuntimeError("F5-TTS is not loaded")

        import numpy as np

        # voice_id is a path to a reference audio file; fall back to bundled example
        ref_file = None
        ref_text = request.extra.get("ref_text", "")
        if request.voice_id and Path(request.voice_id).exists():
            ref_file = request.voice_id
        elif Path(self._DEFAULT_REF_AUDIO).exists():
            ref_file = self._DEFAULT_REF_AUDIO
            # Provide the known transcription to avoid Whisper download
            if not ref_text:
                ref_text = self._DEFAULT_REF_TEXT
        else:
            raise RuntimeError(
                "F5-TTS requires a reference audio file. "
                "Pass voice_id pointing to a WAV/MP3 file, or use a cloned voice profile."
            )

        wav, sr, _ = self._model.infer(
            ref_file=ref_file,
            ref_text=ref_text,
            gen_text=request.text,
            speed=1.0,  # F5-TTS API does not expose speed control
        )

        duration = len(wav) / sr if hasattr(wav, "__len__") else 0.0

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            # Convert float32 to int16 if needed
            if hasattr(wav, "dtype") and wav.dtype != np.int16:
                wav_int16 = (wav * 32767).astype(np.int16)
            else:
                wav_int16 = wav
            wf.writeframes(wav_int16.tobytes())
        buf.seek(0)

        return GenerateResult(
            audio_bytes=buf.getvalue(),
            sample_rate=sr,
            duration_seconds=duration,
            format="wav",
        )

    def clone_voice(self, audio_path: str, name: str = "") -> dict:  # noqa: ARG002
        """F5-TTS uses direct reference audio — no separate embedding step needed."""
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Reference audio not found: {audio_path}")
        return {"reference_audio_path": audio_path, "model": self.model_id}

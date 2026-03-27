"""Chatterbox TTS model — MIT license, emotion control, zero-shot cloning.

Install: pip install chatterbox-tts
HuggingFace: ResembleAI/chatterbox
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

from app.models.base import GenerateRequest, GenerateResult, TTSModelBase

logger = logging.getLogger(__name__)


class ChatterboxModel(TTSModelBase):
    model_id = "chatterbox"
    model_name = "Chatterbox"
    description = "Resemble AI Chatterbox — emotion control, zero-shot cloning, MIT license"
    supports_voice_cloning = True
    supports_streaming = False
    supports_speed = False
    supported_languages = ["en"]
    hf_repo = "ResembleAI/chatterbox"
    vram_gb_estimate = 5.0

    def __init__(self) -> None:
        self._model = None
        self._device = "cuda"

    def load(self, device: str = "cuda") -> None:
        logger.info("Loading Chatterbox on %s", device)
        self._device = device
        from chatterbox.tts import ChatterboxTTS

        self._model = ChatterboxTTS.from_pretrained(device=device)
        self._loaded = True
        logger.info("Chatterbox loaded on %s", device)

    def unload(self) -> None:
        self._model = None
        self._loaded = False
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    def generate(self, request: GenerateRequest) -> GenerateResult:
        if not self._loaded or self._model is None:
            raise RuntimeError("Chatterbox is not loaded")

        import torchaudio

        exaggeration = float(request.extra.get("exaggeration", 0.5))
        cfg_weight = float(request.extra.get("cfg_weight", 0.5))
        ref_audio = (
            request.voice_id if request.voice_id and Path(request.voice_id).exists() else None
        )

        wav = self._model.generate(
            request.text,
            audio_prompt_path=ref_audio,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
        )

        sr = self._model.sr
        duration = wav.shape[-1] / sr

        buf = io.BytesIO()
        torchaudio.save(buf, wav.cpu(), sr, format="wav")
        buf.seek(0)

        return GenerateResult(
            audio_bytes=buf.getvalue(),
            sample_rate=sr,
            duration_seconds=duration,
            format="wav",
        )

    def clone_voice(self, audio_path: str, name: str = "") -> dict:  # noqa: ARG002
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Reference audio not found: {audio_path}")
        return {"reference_audio_path": audio_path, "model": self.model_id}

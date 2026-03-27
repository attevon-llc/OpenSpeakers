"""CosyVoice 2.0 — 150ms latency, MOS 5.53, multi-mode TTS.

Install: pip install cosyvoice2  (or clone FunAudioLLM/CosyVoice repo)
HuggingFace: FunAudioLLM/CosyVoice2-0.5B
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

from app.models.base import GenerateRequest, GenerateResult, TTSModelBase

logger = logging.getLogger(__name__)

SAMPLE_RATE = 22050


class CosyVoice2Model(TTSModelBase):
    model_id = "cosyvoice-2"
    model_name = "CosyVoice 2.0"
    description = "FunAudioLLM CosyVoice 2.0 — 150ms latency, MOS 5.53, zero-shot + voice design"
    supports_voice_cloning = True
    supports_streaming = True
    supports_speed = False
    supported_languages = ["en", "zh", "ja", "ko", "fr", "de", "es", "pt", "ar", "ru"]
    hf_repo = "FunAudioLLM/CosyVoice2-0.5B"
    vram_gb_estimate = 5.0

    def __init__(self) -> None:
        self._model = None

    def load(self, device: str = "cuda") -> None:
        import os

        logger.info("Loading CosyVoice 2.0 on %s", device)
        from cosyvoice.cli.cosyvoice import CosyVoice2

        model_path = os.environ.get("COSYVOICE_MODEL_PATH", "FunAudioLLM/CosyVoice2-0.5B")
        self._model = CosyVoice2(model_path)
        self._loaded = True
        logger.info("CosyVoice 2.0 loaded from %s", model_path)

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
            raise RuntimeError("CosyVoice 2.0 is not loaded")

        import torch
        import torchaudio

        ref_audio = (
            request.voice_id if request.voice_id and Path(request.voice_id).exists() else None
        )
        ref_text = request.extra.get("ref_text", "")
        instruct_text = request.extra.get("instruct", "")

        all_audio = []

        if instruct_text and ref_audio:
            # Voice design mode: shape voice with natural language instruction
            for chunk in self._model.inference_instruct2(
                request.text, instruct_text, ref_audio, stream=False
            ):
                all_audio.append(chunk["tts_speech"])
        elif ref_audio:
            # Zero-shot cloning with reference
            for chunk in self._model.inference_zero_shot(
                request.text, ref_text, ref_audio, stream=False
            ):
                all_audio.append(chunk["tts_speech"])
        else:
            # Cross-lingual (uses default speaker)
            for chunk in self._model.inference_cross_lingual(request.text, None, stream=False):
                all_audio.append(chunk["tts_speech"])

        audio = torch.cat(all_audio, dim=-1)
        sr = self._model.sample_rate if hasattr(self._model, "sample_rate") else SAMPLE_RATE
        duration = audio.shape[-1] / sr

        buf = io.BytesIO()
        torchaudio.save(buf, audio.cpu(), sr, format="wav")
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

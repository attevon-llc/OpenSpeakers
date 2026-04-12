"""Dia 1.6B — multi-speaker dialogue TTS with [S1]/[S2] tags.

Unique capability: dialogue generation with alternating speakers.
Supports nonverbal sounds: (laughs), (sighs), (coughs), (clears throat), (whispers)
Install: pip install dia-tts  (or from git: nari-labs/dia)
HuggingFace: nari-labs/Dia-1.6B
"""

from __future__ import annotations

import io
import logging
import wave

from app.models.base import GenerateRequest, GenerateResult, TTSModelBase

logger = logging.getLogger(__name__)

SAMPLE_RATE = 44100


class DiaTTSModel(TTSModelBase):
    model_id = "dia-1b"
    model_name = "Dia 1.6B"
    description = (
        "Nari Labs Dia 1.6B — dialogue TTS with [S1]/[S2] speaker tags and nonverbal sounds"
    )
    supports_voice_cloning = True
    supports_streaming = False
    supports_speed = False
    supported_languages = ["en"]
    hf_repo = "nari-labs/Dia-1.6B-0626"
    vram_gb_estimate = 10.0
    supports_dialogue = True
    dialogue_format = "dia"
    help_text = (
        "Multi-speaker dialogue with [S1]/[S2] tags. Supports nonverbal sounds: "
        "(laughs), (sighs), (coughs), (clears throat), (whispers). "
        "Slow generation (~30s). English only. ~10 GB VRAM."
    )

    def __init__(self) -> None:
        self._model = None

    def load(self, device: str = "cuda") -> None:
        logger.info("Loading Dia 1.6B on %s", device)
        from dia.model import Dia

        self._model = Dia.from_pretrained("nari-labs/Dia-1.6B-0626", compute_dtype="float16")
        self._loaded = True
        logger.info("Dia 1.6B loaded")

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
            raise RuntimeError("Dia 1.6B is not loaded")

        import numpy as np

        # Dia expects text in [S1] / [S2] format for dialogue
        # If text doesn't have speaker tags, wrap it as single speaker
        text = request.text
        if not text.strip().startswith("[S"):
            text = f"[S1] {text}"

        use_torch_compile = request.extra.get("use_torch_compile", False)
        audio = self._model.generate(
            text,
            use_torch_compile=use_torch_compile,
            verbose=False,
        )

        if hasattr(audio, "numpy"):
            audio = audio.numpy()

        sr = SAMPLE_RATE
        if audio.dtype != np.int16:
            audio = (audio * 32767).astype(np.int16)

        duration = len(audio) / sr

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(audio.tobytes())
        buf.seek(0)

        return GenerateResult(
            audio_bytes=buf.getvalue(),
            sample_rate=sr,
            duration_seconds=duration,
            format="wav",
        )

    def clone_voice(self, audio_path: str, name: str = "") -> dict:  # noqa: ARG002
        """Dia uses reference audio for voice conditioning."""
        from pathlib import Path

        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Reference audio not found: {audio_path}")
        return {"reference_audio_path": audio_path, "model": self.model_id}

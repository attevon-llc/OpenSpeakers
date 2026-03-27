"""Orpheus 3B TTS — Llama backbone, emotion/intonation tags, streaming.

Install: pip install orpheus-tts
HuggingFace: canopylabs/orpheus-3b-0.1-ft
"""

from __future__ import annotations

import contextlib
import io
import logging
import wave

from app.models.base import GenerateRequest, GenerateResult, TTSModelBase

logger = logging.getLogger(__name__)

ORPHEUS_VOICES = ["zoe", "zac", "jess", "leo", "mia", "julia", "leah"]
ORPHEUS_EMOTION_TAGS = [
    "<laugh>",
    "<chuckle>",
    "<sigh>",
    "<cough>",
    "<sniffle>",
    "<groan>",
    "<yawn>",
    "<gasp>",
]
DEFAULT_VOICE = "zoe"
SAMPLE_RATE = 24000


class OrpheusTTSModel(TTSModelBase):
    model_id = "orpheus-3b"
    model_name = "Orpheus 3B"
    description = (
        "Canopy Labs Orpheus 3B — Llama-based, emotion tags, zero-shot cloning, ~200ms latency"
    )
    supports_voice_cloning = False
    supports_streaming = True
    supports_speed = False
    supported_languages = ["en"]
    hf_repo = "canopylabs/orpheus-3b-0.1-ft"
    vram_gb_estimate = 7.0

    def __init__(self) -> None:
        self._model = None

    def load(self, device: str = "cuda") -> None:
        logger.info("Loading Orpheus 3B on %s", device)
        from orpheus_tts import OrpheusModel
        from orpheus_tts.engine_class import OrpheusModel as _OModel
        from vllm import AsyncEngineArgs, AsyncLLMEngine

        # vLLM defaults to 90% GPU memory utilization (~42GB on A6000 48GB) which is
        # far more than needed for a 3B model (~6GB weights).  50% (~24GB) is generous
        # for KV cache while leaving room for other workers on the same GPU.
        def _patched_setup_engine(self_inner):
            engine_args = AsyncEngineArgs(
                model=self_inner.model_name,
                dtype=self_inner.dtype,
                gpu_memory_utilization=0.5,
            )
            return AsyncLLMEngine.from_engine_args(engine_args)

        _OModel._setup_engine = _patched_setup_engine

        self._model = OrpheusModel(model_name="canopylabs/orpheus-3b-0.1-ft")
        self._loaded = True
        logger.info("Orpheus 3B loaded (~24GB VRAM with 50%% gpu_memory_utilization)")

    def unload(self) -> None:
        if self._model is not None:
            with contextlib.suppress(Exception):
                # vLLM runs its engine in separate processes; shutdown() terminates them
                # so VRAM is freed immediately rather than waiting for GC.
                self._model.engine.shutdown()
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
            raise RuntimeError("Orpheus 3B is not loaded")

        voice = request.voice_id or DEFAULT_VOICE
        if voice not in ORPHEUS_VOICES:
            voice = DEFAULT_VOICE
        temperature = float(request.extra.get("temperature", 0.6))
        top_p = float(request.extra.get("top_p", 0.95))

        all_chunks = []
        for audio_chunk in self._model.generate_speech(
            prompt=request.text,
            voice=voice,
            temperature=temperature,
            top_p=top_p,
        ):
            all_chunks.append(audio_chunk)

        all_pcm = b"".join(all_chunks)
        num_samples = len(all_pcm) // 2
        duration = num_samples / SAMPLE_RATE

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(all_pcm)
        buf.seek(0)

        return GenerateResult(
            audio_bytes=buf.getvalue(),
            sample_rate=SAMPLE_RATE,
            duration_seconds=duration,
            format="wav",
        )

    def stream_generate(self, request: GenerateRequest):
        """Yield raw PCM16 chunks for streaming playback."""
        if not self._loaded or self._model is None:
            raise RuntimeError("Orpheus 3B is not loaded")

        voice = request.voice_id or DEFAULT_VOICE
        if voice not in ORPHEUS_VOICES:
            voice = DEFAULT_VOICE
        temperature = float(request.extra.get("temperature", 0.6))
        top_p = float(request.extra.get("top_p", 0.95))

        yield from self._model.generate_speech(
            prompt=request.text,
            voice=voice,
            temperature=temperature,
            top_p=top_p,
        )

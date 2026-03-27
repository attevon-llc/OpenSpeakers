"""Parler TTS Mini — text-description-controlled voice synthesis.

Unique capability: specify voice characteristics via natural language.
Install: pip install parler-tts
HuggingFace: parler-tts/parler-tts-mini-v1
"""

from __future__ import annotations

import logging

from app.models.base import GenerateRequest, GenerateResult, TTSModelBase

logger = logging.getLogger(__name__)

DEFAULT_DESCRIPTION = (
    "A female speaker with a slightly expressive voice delivers a clear, "
    "engaging speech at a moderate pace in a quiet room."
)

PARLER_EXAMPLE_VOICES = {
    "default-female": DEFAULT_DESCRIPTION,
    "warm-female": (
        "A warm, friendly female voice speaks in a natural, conversational tone "
        "at a comfortable pace in a quiet studio."
    ),
    "authoritative-male": (
        "A deep male voice with a serious, authoritative tone speaks slowly and "
        "clearly in a professional setting."
    ),
    "excited": (
        "An enthusiastic, energetic female speaker with high pitch and expressiveness "
        "delivers text with excitement and animation."
    ),
    "whisper": (
        "A hushed, intimate whisper from a female voice, speaking softly and "
        "quietly as if sharing a secret."
    ),
    "elderly-male": (
        "An elderly male voice, slightly gravelly and warm, speaking at a measured "
        "pace with gentle authority."
    ),
}


class ParlerTTSModel(TTSModelBase):
    model_id = "parler-tts"
    model_name = "Parler TTS Mini"
    description = (
        "Parler TTS Mini — generate any voice from a text description (no reference audio needed)"
    )
    supports_voice_cloning = False  # uses text description instead
    supports_streaming = False
    supports_speed = False
    supported_languages = ["en"]
    hf_repo = "parler-tts/parler-tts-mini-v1"
    vram_gb_estimate = 3.0

    def __init__(self) -> None:
        self._model = None
        self._tokenizer = None
        self._device = "cuda"

    def load(self, device: str = "cuda") -> None:
        import torch

        # Fall back to CPU if CUDA unavailable
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA not available — falling back to CPU for Parler TTS")
            device = "cpu"

        logger.info("Loading Parler TTS on %s", device)
        self._device = device

        from parler_tts import ParlerTTSForConditionalGeneration
        from transformers import AutoTokenizer

        self._model = ParlerTTSForConditionalGeneration.from_pretrained(
            "parler-tts/parler-tts-mini-v1"
        ).to(device)
        self._tokenizer = AutoTokenizer.from_pretrained("parler-tts/parler-tts-mini-v1")
        self._loaded = True
        logger.info("Parler TTS loaded on %s", device)

    def unload(self) -> None:
        self._model = None
        self._tokenizer = None
        self._loaded = False
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    def generate(self, request: GenerateRequest) -> GenerateResult:
        if not self._loaded or self._model is None:
            raise RuntimeError("Parler TTS is not loaded")

        import io as _io

        import soundfile as sf

        # voice_id can be a preset name or the description itself
        description = request.extra.get("description")
        if not description:
            if request.voice_id and request.voice_id in PARLER_EXAMPLE_VOICES:
                description = PARLER_EXAMPLE_VOICES[request.voice_id]
            elif request.voice_id and not request.voice_id.endswith((".wav", ".mp3", ".flac")):
                # Treat voice_id as a raw description string
                description = request.voice_id
            else:
                description = DEFAULT_DESCRIPTION

        input_ids = self._tokenizer(description, return_tensors="pt").input_ids.to(self._device)
        prompt_ids = self._tokenizer(request.text, return_tensors="pt").input_ids.to(self._device)

        generation = self._model.generate(
            input_ids=input_ids,
            prompt_input_ids=prompt_ids,
        )
        audio_arr = generation.cpu().numpy().squeeze()
        sr = self._model.config.sampling_rate
        duration = len(audio_arr) / sr

        buf = _io.BytesIO()
        sf.write(buf, audio_arr, sr, format="WAV")
        buf.seek(0)

        return GenerateResult(
            audio_bytes=buf.getvalue(),
            sample_rate=sr,
            duration_seconds=duration,
            format="wav",
        )

    @classmethod
    def get_example_voices(cls) -> dict[str, str]:
        return PARLER_EXAMPLE_VOICES

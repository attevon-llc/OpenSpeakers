"""OpenAI-compatible TTS API endpoint.

Allows apps using the OpenAI Python SDK (openai.audio.speech.create) to
point at this server instead of api.openai.com with zero code changes.

Usage:
    from openai import OpenAI
    client = OpenAI(base_url="http://localhost:8080/v1", api_key="not-needed")
    audio = client.audio.speech.create(model="tts-1", voice="alloy", input="Hello!")
    audio.stream_to_file("out.mp3")
"""

from __future__ import annotations

import asyncio
import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db.models import JobStatus, TTSJob
from app.tasks.tts_tasks import generate_tts

logger = logging.getLogger(__name__)

router = APIRouter(tags=["openai-compat"])

# Map OpenAI tier names to our model IDs
MODEL_MAP: dict[str, str] = {
    "tts-1": "kokoro",
    "tts-1-hd": "orpheus-3b",
    "tts-1-nano": "f5-tts",
}

# Map OpenAI voice names to (model_id, voice_id)
VOICE_MAP: dict[str, tuple[str, str | None]] = {
    "alloy": ("kokoro", "en-female-1"),
    "echo": ("kokoro", "en-male-1"),
    "fable": ("kokoro", "en-female-2"),
    "onyx": ("kokoro", "en-male-2"),
    "nova": ("f5-tts", None),
    "shimmer": ("kokoro", "en-female-3"),
}

FORMAT_TO_MEDIA_TYPE = {
    "mp3": "audio/mpeg",
    "opus": "audio/opus",
    "aac": "audio/aac",
    "flac": "audio/flac",
    "wav": "audio/wav",
    "pcm": "audio/pcm",
}

QUEUE_MAP: dict[str, str] = {
    "kokoro": "tts.kokoro",
    "fish-speech-s2": "tts.fish-speech",
    "qwen3-tts": "tts.qwen3",
    "orpheus-3b": "tts.orpheus",
    "f5-tts": "tts.f5-tts",
    "chatterbox": "tts.f5-tts",
    "cosyvoice-2": "tts.f5-tts",
}


def _parse_keep_alive(value: str | int | None) -> int | None:
    """Parse Ollama-style keep_alive value to integer seconds.

    Accepts:
      None          → None (server default idle timeout)
      -1 or "-1"    → -1 (indefinite)
       0 or "0"     → 0 (clear TTL)
      "5m"          → 300
      "1h"          → 3600
      "30s" or "30" → 30
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value
    value = str(value).strip()
    try:
        return int(value)
    except ValueError:
        pass
    suffixes = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    if value and value[-1].lower() in suffixes:
        try:
            return int(value[:-1]) * suffixes[value[-1].lower()]
        except ValueError:
            pass
    return None


class OpenAISpeechRequest(BaseModel):
    model: str = "tts-1"
    input: str = Field(..., min_length=1, max_length=4096)
    voice: str = "alloy"
    response_format: str = "mp3"
    speed: float = Field(1.0, ge=0.25, le=4.0)
    keep_alive: str | int | None = Field(
        None,
        description=(
            "Ollama-style keep_alive. "
            '"-1" = keep indefinitely, "0" = unload after, '
            '"5m" / "1h" = duration string, null = server default.'
        ),
    )


@router.post("/v1/audio/speech")
async def openai_speech(req: OpenAISpeechRequest, db: Session = Depends(get_db)):
    """OpenAI-compatible TTS endpoint. Blocks until audio is ready."""
    # Resolve model
    model_id = MODEL_MAP.get(req.model, req.model)

    # Resolve voice
    voice_id: str | None = None
    if req.voice in VOICE_MAP:
        mapped_model, mapped_voice = VOICE_MAP[req.voice]
        if req.model in MODEL_MAP:  # only override for tier names
            model_id = mapped_model
        voice_id = mapped_voice
    else:
        voice_id = req.voice  # pass-through as direct voice_id

    # Clamp speed to our supported range
    speed = max(0.5, min(2.0, req.speed))

    # output_format: pcm → wav for our system
    output_format = "wav" if req.response_format == "pcm" else req.response_format
    if output_format not in ("wav", "mp3", "ogg"):
        output_format = "mp3"  # default for unsupported formats (opus, aac, flac)

    keep_alive_seconds = _parse_keep_alive(req.keep_alive)

    # Create job
    job = TTSJob(
        model_id=model_id,
        text=req.input,
        voice_id=voice_id,
        parameters={
            "speed": speed,
            "language": "en",
            "output_format": output_format,
            "extra": {},
            "keep_alive": keep_alive_seconds,
        },
        status=JobStatus.PENDING,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    queue = QUEUE_MAP.get(model_id, "tts")
    generate_tts.apply_async(args=[str(job.id)], queue=queue)

    # Poll asynchronously until done (max 5 minutes). Uses asyncio.sleep so we don't
    # block the FastAPI event loop — other requests can be served during the wait.
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        await asyncio.sleep(0.5)
        db.refresh(job)
        if job.status == JobStatus.COMPLETE:
            break
        if job.status in (JobStatus.FAILED, JobStatus.CANCELLED):
            # Log full error server-side, return a sanitised message to the client.
            logger.warning("OpenAI-compat job %s failed: %s", job.id, job.error_message)
            raise HTTPException(500, detail="Speech generation failed")

    if job.status != JobStatus.COMPLETE:
        raise HTTPException(504, detail="Generation timed out")

    from pathlib import Path

    if not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(500, detail="Audio file not found")

    media_type = FORMAT_TO_MEDIA_TYPE.get(req.response_format, "audio/mpeg")
    ext = Path(job.output_path).suffix
    return FileResponse(
        path=job.output_path,
        media_type=media_type,
        filename=f"speech{ext}",
    )


@router.get("/v1/models")
def openai_list_models():
    """OpenAI-compatible model list."""
    from app.models.manager import ModelManager

    manager = ModelManager.get_instance()
    models = [
        {"id": "tts-1", "object": "model", "owned_by": "openspeakers"},
        {"id": "tts-1-hd", "object": "model", "owned_by": "openspeakers"},
        *[
            {"id": mid, "object": "model", "owned_by": "openspeakers"}
            for mid in manager.registered_ids
        ],
    ]
    return {"object": "list", "data": models}

"""Voice profile endpoints (cloned voices)."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.db.models import VoiceProfile
from app.schemas.voices import (
    BuiltinVoice,
    VoiceListResponse,
    VoiceProfileResponse,
    VoiceProfileUpdate,
)
from app.tasks.tts_tasks import clone_voice

router = APIRouter(prefix="/voices", tags=["voices"])

# Models that run on dedicated worker queues instead of the default "tts" queue
QUEUE_MAP: dict[str, str] = {
    "fish-speech-s2": "tts.fish-speech",
    "qwen3-tts": "tts.qwen3",
    "orpheus-3b": "tts.orpheus",
    "f5-tts": "tts.f5-tts",
    "chatterbox": "tts.f5-tts",
    "cosyvoice-2": "tts.f5-tts",
    "xtts-v2": "tts.xtts",
    "dia-1b": "tts.dia",
    "bark": "tts.bark",
}

# Max reference audio duration in seconds (enforced upstream by the task)
MAX_REFERENCE_AUDIO_MB = 50


@router.get("", response_model=VoiceListResponse)
def list_voices(
    model_id: str | None = None,
    db: Session = Depends(get_db),
) -> VoiceListResponse:
    """List all saved voice profiles."""
    q = db.query(VoiceProfile)
    if model_id:
        q = q.filter(VoiceProfile.model_id == model_id)
    profiles = q.order_by(VoiceProfile.created_at.desc()).all()
    return VoiceListResponse(
        voices=[VoiceProfileResponse.model_validate(p) for p in profiles],
        total=len(profiles),
    )


@router.post("", response_model=VoiceProfileResponse, status_code=201)
async def create_voice_profile(
    name: str = Form(...),
    model_id: str = Form(...),
    reference_audio: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> VoiceProfileResponse:
    """Upload reference audio and create a voice profile.

    The voice embedding is generated asynchronously via a Celery task.
    """
    # Validate file type — accept all common audio containers (ffmpeg handles decoding)
    ALLOWED_TYPES = {
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/flac",
        "audio/x-flac",
        "audio/ogg",
        "audio/opus",
        "audio/mp4",
        "audio/x-m4a",
        "audio/aac",
        "video/mp4",  # browsers sometimes report M4A as video/mp4
    }
    content_type = (reference_audio.content_type or "").split(";")[0].strip()
    if content_type and content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported audio type: {content_type}. Use WAV, MP3, FLAC, M4A, or OGG.",
        )

    # Save reference audio
    voice_id = uuid.uuid4()
    audio_dir = Path(settings.AUDIO_OUTPUT_DIR) / "voices"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Whitelist extensions. The filename is user-controlled — taking only the
    # suffix via Path() and checking it against a known list means we can't
    # accidentally write an .exe or hit a case-difference issue in downstream
    # tools. The stored filename uses a generated UUID so the original basename
    # never reaches disk.
    ALLOWED_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".opus", ".aac", ".mp4", ".webm"}
    ext = Path(reference_audio.filename or "ref.wav").suffix.lower()
    if not ext or ext not in ALLOWED_EXTS:
        ext = ".wav"
    ref_path = audio_dir / f"{voice_id}{ext}"

    with ref_path.open("wb") as f:
        shutil.copyfileobj(reference_audio.file, f)

    # Check file size
    size_mb = ref_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_REFERENCE_AUDIO_MB:
        ref_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large: {size_mb:.1f} MB > {MAX_REFERENCE_AUDIO_MB} MB",
        )

    # Create DB record
    profile = VoiceProfile(
        id=voice_id,
        name=name,
        model_id=model_id,
        reference_audio_path=str(ref_path),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # Dispatch embedding generation task (model-specific queue routing)
    queue = QUEUE_MAP.get(model_id, "tts")
    clone_voice.apply_async(args=[str(profile.id)], queue=queue)

    return VoiceProfileResponse.model_validate(profile)


# NOTE: /builtin/{model_id} must come BEFORE /{voice_id} to avoid route conflicts
@router.get("/builtin/{model_id}", response_model=list[BuiltinVoice])
def list_builtin_voices(model_id: str) -> list[BuiltinVoice]:
    """List built-in voices for a specific model."""
    from app.models.manager import ModelManager

    manager = ModelManager.get_instance()
    if model_id not in manager.registered_ids:
        raise HTTPException(status_code=404, detail=f"Model {model_id!r} not found")

    builtin: list[BuiltinVoice] = []

    if model_id == "vibevoice":
        from app.models.vibevoice import BUILTIN_VOICES

        for voice_id, slug in BUILTIN_VOICES.items():
            parts = voice_id.split("-")
            lang = parts[0] if parts else "en"
            gender = "female" if "woman" in slug else "male"
            builtin.append(
                BuiltinVoice(
                    id=voice_id,
                    name=voice_id,
                    language=lang,
                    gender=gender,
                    model_id=model_id,
                )
            )

    elif model_id == "kokoro":
        from app.models.kokoro import KOKORO_VOICES

        for voice_id in KOKORO_VOICES:
            parts = voice_id.split("-")
            lang = parts[0] if parts else "en"
            gender = parts[1] if len(parts) > 1 else None
            builtin.append(
                BuiltinVoice(
                    id=voice_id,
                    name=voice_id,
                    language=lang,
                    gender=gender,
                    model_id=model_id,
                )
            )

    return builtin


@router.get("/{voice_id}", response_model=VoiceProfileResponse)
def get_voice_profile(voice_id: uuid.UUID, db: Session = Depends(get_db)) -> VoiceProfileResponse:
    """Get a single voice profile by ID."""
    profile = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    return VoiceProfileResponse.model_validate(profile)


@router.patch("/{voice_id}", response_model=VoiceProfileResponse)
def update_voice_profile(
    voice_id: uuid.UUID,
    update: VoiceProfileUpdate,
    db: Session = Depends(get_db),
) -> VoiceProfileResponse:
    """Update name, description, or tags on a voice profile."""
    profile = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")

    if update.name is not None:
        profile.name = update.name
    if update.description is not None:
        profile.description = update.description
    if update.tags is not None:
        profile.tags = update.tags

    db.commit()
    db.refresh(profile)
    return VoiceProfileResponse.model_validate(profile)


@router.get("/{voice_id}/audio")
def get_voice_audio(voice_id: uuid.UUID, db: Session = Depends(get_db)) -> FileResponse:
    """Return the reference audio file for a voice profile."""
    profile = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")

    ref_path = Path(profile.reference_audio_path)
    if not ref_path.exists():
        raise HTTPException(status_code=404, detail="Reference audio file not found on disk")

    ext = ref_path.suffix.lower()
    media_types = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
    }
    media_type = media_types.get(ext, "audio/wav")

    return FileResponse(
        path=str(ref_path),
        media_type=media_type,
        filename=f"voice_{voice_id}{ext}",
    )


@router.delete("/{voice_id}", status_code=204)
def delete_voice_profile(voice_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """Delete a voice profile and its associated files."""
    profile = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")

    # Delete files
    for path_attr in ("reference_audio_path", "embedding_path"):
        path_str = getattr(profile, path_attr, None)
        if path_str:
            Path(path_str).unlink(missing_ok=True)

    db.delete(profile)
    db.commit()

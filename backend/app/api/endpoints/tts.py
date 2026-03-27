"""TTS generation endpoints."""

from __future__ import annotations

import io
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db.models import JobStatus, TTSJob
from app.schemas.tts import (
    BatchGenerateRequest,
    BatchGenerateResponse,
    BatchStatusResponse,
    GenerateRequest,
    GenerateResponse,
    JobListResponse,
    JobResponse,
)
from app.tasks.tts_tasks import generate_tts

router = APIRouter(prefix="/tts", tags=["tts"])

# Models that run on dedicated worker queues instead of the default "tts" queue
QUEUE_MAP: dict[str, str] = {
    # Dedicated queues — each maps to its own worker container
    "kokoro": "tts.kokoro",  # always-on standby; dedicated so it never waits behind VibeVoice
    "fish-speech-s2": "tts.fish-speech",
    "qwen3-tts": "tts.qwen3",
    "orpheus-3b": "tts.orpheus",
    "f5-tts": "tts.f5-tts",
    "chatterbox": "tts.f5-tts",
    "cosyvoice-2": "tts.f5-tts",
    "parler-tts": "tts.f5-tts",
    "dia-1b": "tts.dia",
    # Future models
    "xtts-v2": "tts.xtts",
    "bark": "tts.bark",
    # Default (no entry) → "tts" queue → main worker (VibeVoice 0.5B / 1.5B)
}


@router.post("/generate", response_model=GenerateResponse, status_code=202)
def create_tts_job(request: GenerateRequest, db: Session = Depends(get_db)) -> GenerateResponse:
    """Submit a TTS generation request.

    Returns immediately with a job_id. Poll /tts/jobs/{job_id} for status.
    """
    # Create job record
    job = TTSJob(
        model_id=request.model_id,
        text=request.text,
        voice_id=request.voice_id,
        voice_profile_id=uuid.UUID(request.voice_id) if _is_uuid(request.voice_id) else None,
        parameters={
            "speed": request.speed,
            "pitch": request.pitch,
            "language": request.language,
            "output_format": request.output_format,
            "extra": request.extra,
            "keep_alive": request.keep_alive,
        },
        status=JobStatus.PENDING,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch to Celery worker (model-specific queue routing)
    queue = QUEUE_MAP.get(request.model_id, "tts")
    generate_tts.apply_async(args=[str(job.id)], queue=queue)

    return GenerateResponse(job_id=job.id, status=JobStatus.PENDING)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> JobResponse:
    """Get the status and result of a TTS job."""
    job = db.query(TTSJob).filter(TTSJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@router.get("/jobs/{job_id}/audio")
def get_job_audio(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """Download the generated audio file for a completed job."""
    job = db.query(TTSJob).filter(TTSJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETE:
        raise HTTPException(status_code=409, detail=f"Job is {job.status.value}, not complete")
    if not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    ext = Path(job.output_path).suffix.lower()
    media_types = {".wav": "audio/wav", ".mp3": "audio/mpeg", ".ogg": "audio/ogg"}
    media_type = media_types.get(ext, "audio/wav")
    filename = f"tts_{job_id}{ext}"

    return FileResponse(
        path=job.output_path,
        media_type=media_type,
        filename=filename,
    )


@router.get("/jobs", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    model_id: str | None = Query(None),
    status: JobStatus | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
) -> JobListResponse:
    """List recent TTS jobs, newest first."""
    q = db.query(TTSJob)
    if model_id:
        q = q.filter(TTSJob.model_id == model_id)
    if status:
        q = q.filter(TTSJob.status == status)
    if search:
        q = q.filter(TTSJob.text.ilike(f"%{search}%"))

    total = q.count()
    jobs = (
        q.order_by(TTSJob.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    )

    return JobListResponse(
        jobs=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/jobs/{job_id}", status_code=204)
def cancel_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """Cancel a pending or running TTS job."""
    job = db.query(TTSJob).filter(TTSJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in (JobStatus.PENDING, JobStatus.RUNNING):
        raise HTTPException(
            status_code=409, detail=f"Cannot cancel job with status: {job.status.value}"
        )
    if job.celery_task_id:
        from app.core.celery import celery_app

        celery_app.control.revoke(job.celery_task_id, terminate=True, signal="SIGTERM")
    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.now(UTC)
    db.commit()


@router.post("/batch", response_model=BatchGenerateResponse, status_code=202)
def batch_generate(
    request: BatchGenerateRequest, db: Session = Depends(get_db)
) -> BatchGenerateResponse:
    """Submit multiple TTS lines as a batch."""
    import uuid as uuid_module

    batch_id = uuid_module.uuid4()
    job_ids = []
    for line in request.lines:
        line = line.strip()
        if not line:
            continue
        job = TTSJob(
            model_id=request.model_id,
            text=line,
            voice_id=request.voice_id,
            batch_id=batch_id,
            parameters={
                "speed": request.speed,
                "language": request.language,
                "output_format": request.output_format,
                "extra": request.extra,
            },
            status=JobStatus.PENDING,
        )
        db.add(job)
        db.flush()
        queue = QUEUE_MAP.get(request.model_id, "tts")
        generate_tts.apply_async(args=[str(job.id)], queue=queue)
        job_ids.append(job.id)
    db.commit()
    return BatchGenerateResponse(batch_id=batch_id, job_ids=job_ids, total=len(job_ids))


@router.get("/batches/{batch_id}", response_model=BatchStatusResponse)
def get_batch(batch_id: uuid.UUID, db: Session = Depends(get_db)) -> BatchStatusResponse:
    """Get the status of all jobs in a batch."""
    jobs = db.query(TTSJob).filter(TTSJob.batch_id == batch_id).all()
    if not jobs:
        raise HTTPException(status_code=404, detail="Batch not found")

    status_counts: dict[str, int] = {}
    for job in jobs:
        key = job.status.value
        status_counts[key] = status_counts.get(key, 0) + 1

    return BatchStatusResponse(
        batch_id=batch_id,
        total=len(jobs),
        status_counts=status_counts,
        jobs=[JobResponse.model_validate(j) for j in jobs],
    )


@router.get("/batches/{batch_id}/zip")
def get_batch_zip(batch_id: uuid.UUID, db: Session = Depends(get_db)) -> StreamingResponse:
    """Download a ZIP archive of all completed audio files in a batch."""
    jobs = (
        db.query(TTSJob)
        .filter(TTSJob.batch_id == batch_id, TTSJob.status == JobStatus.COMPLETE)
        .all()
    )
    if not jobs:
        raise HTTPException(status_code=404, detail="No completed jobs found in batch")

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, job in enumerate(jobs, 1):
            if job.output_path and Path(job.output_path).exists():
                ext = Path(job.output_path).suffix
                zf.write(job.output_path, arcname=f"{i:03d}_{job.id}{ext}")
    zip_buf.seek(0)

    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=batch_{batch_id}.zip"},
    )


def _is_uuid(value: str | None) -> bool:
    if not value:
        return False
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

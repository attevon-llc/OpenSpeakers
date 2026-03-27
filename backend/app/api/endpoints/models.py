"""Model listing and status endpoints."""

from __future__ import annotations

import math

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from app.models.manager import ModelManager
from app.schemas.models import ModelInfo

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[ModelInfo])
def list_models() -> list[ModelInfo]:
    """List all registered TTS models and their current status."""
    manager = ModelManager.get_instance()
    return [ModelInfo(**m) for m in manager.list_models()]


@router.get("/{model_id}", response_model=ModelInfo)
def get_model(model_id: str) -> ModelInfo:
    """Get info and status for a specific model."""
    manager = ModelManager.get_instance()
    if model_id not in manager.registered_ids:
        raise HTTPException(status_code=404, detail=f"Model {model_id!r} not found")
    return ModelInfo(**manager.get_status(model_id))


class ModelLoadRequest(BaseModel):
    keep_alive: int | None = Field(
        None,
        description=(
            "Seconds to keep model in GPU VRAM. "
            "-1 = indefinite, 0 = clear TTL (use idle timeout), None = server default."
        ),
    )


@router.post("/{model_id}/load", response_model=ModelInfo)
def load_model(
    model_id: str,
    req: ModelLoadRequest = Body(default_factory=ModelLoadRequest),
) -> ModelInfo:
    """Pre-warm a model into GPU VRAM.

    Useful for 'wake' operations before a burst of requests.
    Set keep_alive=-1 to keep the model loaded indefinitely.
    """
    manager = ModelManager.get_instance()
    if model_id not in manager.registered_ids:
        raise HTTPException(status_code=404, detail=f"Model {model_id!r} not found")
    try:
        manager.load_model(model_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if req.keep_alive is not None:
        manager.set_keep_alive(model_id, req.keep_alive)

    status = manager.get_status(model_id)
    remaining = status.get("keep_alive_seconds_remaining")
    if remaining == math.inf:
        status["keep_alive_seconds_remaining"] = -1  # JSON-serialisable sentinel
    return ModelInfo(**status)


@router.delete("/{model_id}/load", status_code=204)
def unload_model(model_id: str) -> None:
    """Force-unload a model from GPU VRAM (ignores standby / keep_alive)."""
    manager = ModelManager.get_instance()
    if model_id not in manager.registered_ids:
        raise HTTPException(status_code=404, detail=f"Model {model_id!r} not found")
    if manager.current_model_id == model_id:
        manager.unload_all(respect_standby=False)

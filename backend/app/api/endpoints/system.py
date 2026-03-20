"""System health and info endpoints."""
from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter

from app.core.config import settings
from app.models.manager import ModelManager

router = APIRouter(tags=["system"])


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@router.get("/api/system/info")
def system_info() -> dict:
    manager = ModelManager.get_instance()

    gpu_info: dict = {}
    try:
        import torch
        if torch.cuda.is_available():
            device_id = settings.GPU_DEVICE_ID
            gpu_info = {
                "available": True,
                "device_id": device_id,
                "device_name": torch.cuda.get_device_name(device_id),
                "vram_total_gb": round(torch.cuda.get_device_properties(device_id).total_memory / 1e9, 1),
                "vram_used_gb": round(torch.cuda.memory_allocated(device_id) / 1e9, 2),
                "vram_reserved_gb": round(torch.cuda.memory_reserved(device_id) / 1e9, 2),
            }
        else:
            gpu_info = {"available": False}
    except ImportError:
        gpu_info = {"available": False, "note": "torch not installed in API container"}

    audio_dir = Path(settings.AUDIO_OUTPUT_DIR)
    disk_usage: dict = {}
    if audio_dir.exists():
        total, used, free = shutil.disk_usage(audio_dir)
        disk_usage = {
            "total_gb": round(total / 1e9, 1),
            "used_gb": round(used / 1e9, 1),
            "free_gb": round(free / 1e9, 1),
        }

    return {
        "current_model": manager.current_model_id,
        "registered_models": manager.registered_ids,
        "gpu": gpu_info,
        "disk": disk_usage,
        "audio_output_dir": str(audio_dir),
        "model_cache_dir": settings.MODEL_CACHE_DIR,
    }

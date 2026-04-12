"""System health and info endpoints."""

from __future__ import annotations

import shutil
import subprocess
import threading
import time
from pathlib import Path

from fastapi import APIRouter

from app.core.config import settings
from app.models.manager import ModelManager

router = APIRouter(tags=["system"])

# nvidia-smi cache — 1 second TTL. The /ws/gpu stream polls at 1 Hz, and the
# /api/system/info endpoint is called on every settings-page render; hitting the
# subprocess on every call blocks the FastAPI event loop for ~50–100 ms per call
# and wastes CPU. A short cache deduplicates simultaneous callers without making
# the dashboard feel stale.
_NVIDIA_SMI_TTL_S = 1.0
_nvidia_smi_cache: dict[int, tuple[float, dict]] = {}
_nvidia_smi_lock = threading.Lock()


def _parse_nvidia_smi(stdout: str) -> dict:
    parts = [p.strip() for p in stdout.strip().split(",")]
    if len(parts) < 7:
        return {}
    try:
        return {
            "utilization_pct": int(parts[0]),
            "temperature_c": int(parts[1]),
            "power_draw_w": float(parts[2]),
            "power_limit_w": float(parts[3]),
            "fan_speed_pct": int(parts[4]) if parts[4] != "[N/A]" else None,
            "memory_used_mb": int(parts[5]),
            "memory_total_mb": int(parts[6]),
        }
    except (ValueError, IndexError):
        return {}


def _get_nvidia_smi_stats(device_id: int) -> dict:
    """Get GPU stats via nvidia-smi, cached for `_NVIDIA_SMI_TTL_S` seconds."""
    now = time.monotonic()
    with _nvidia_smi_lock:
        cached = _nvidia_smi_cache.get(device_id)
        if cached and now - cached[0] < _NVIDIA_SMI_TTL_S:
            return cached[1]

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,temperature.gpu,power.draw,power.limit,fan.speed,memory.used,memory.total",
                "--format=csv,noheader,nounits",
                f"--id={device_id}",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {}

    stats = _parse_nvidia_smi(result.stdout) if result.returncode == 0 else {}
    with _nvidia_smi_lock:
        _nvidia_smi_cache[device_id] = (now, stats)
    return stats


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


def _get_pynvml_info(device_id: int) -> dict:
    """Query GPU info via pynvml (works without torch in the container)."""
    try:
        import pynvml

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
        name = pynvml.nvmlDeviceGetName(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        try:
            power_draw = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
            power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000.0
        except pynvml.NVMLError:
            power_draw = power_limit = 0.0
        try:
            fan = pynvml.nvmlDeviceGetFanSpeed(handle)
        except pynvml.NVMLError:
            fan = None
        return {
            "available": True,
            "device_id": device_id,
            "device_name": name if isinstance(name, str) else name.decode(),
            "vram_total_gb": round(mem.total / 1e9, 1),
            "vram_used_gb": round(mem.used / 1e9, 2),
            "vram_reserved_gb": None,
            "nvidia_smi": {
                "utilization_pct": util.gpu,
                "temperature_c": temp,
                "power_draw_w": round(power_draw, 1),
                "power_limit_w": round(power_limit, 1),
                "fan_speed_pct": fan,
                "memory_used_mb": mem.used // (1024 * 1024),
                "memory_total_mb": mem.total // (1024 * 1024),
            },
        }
    except Exception:
        return {}


@router.get("/api/system/info")
def system_info() -> dict:
    manager = ModelManager.get_instance()

    device_id = settings.GPU_DEVICE_ID
    gpu_info: dict = {}

    # Try pynvml first (available in API container without torch)
    gpu_info = _get_pynvml_info(device_id)

    # Fallback: torch (worker containers only)
    if not gpu_info:
        try:
            import torch

            if torch.cuda.is_available():
                gpu_info = {
                    "available": True,
                    "device_id": device_id,
                    "device_name": torch.cuda.get_device_name(device_id),
                    "vram_total_gb": round(
                        torch.cuda.get_device_properties(device_id).total_memory / 1e9, 1
                    ),
                    "vram_used_gb": round(torch.cuda.memory_allocated(device_id) / 1e9, 2),
                    "vram_reserved_gb": round(torch.cuda.memory_reserved(device_id) / 1e9, 2),
                }
                gpu_info["nvidia_smi"] = _get_nvidia_smi_stats(device_id)
            else:
                gpu_info = {"available": False}
        except ImportError:
            gpu_info = {"available": False, "note": "No GPU stats available"}

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

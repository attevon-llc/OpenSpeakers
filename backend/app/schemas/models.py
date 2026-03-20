from __future__ import annotations

from pydantic import BaseModel


class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    supports_voice_cloning: bool
    supports_streaming: bool
    supported_languages: list[str]
    hf_repo: str
    vram_gb_estimate: float
    is_loaded: bool
    status: str  # "loaded" | "available" | "loading" | "unknown"

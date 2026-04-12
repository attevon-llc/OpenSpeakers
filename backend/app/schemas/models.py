from __future__ import annotations

from pydantic import BaseModel


class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    supports_voice_cloning: bool
    supports_streaming: bool
    supports_speed: bool = False
    supports_pitch: bool = False
    supports_dialogue: bool = False
    dialogue_format: str = ""
    help_text: str = ""
    supported_languages: list[str]
    hf_repo: str
    vram_gb_estimate: float
    is_loaded: bool
    status: str  # "loaded" | "available" | "loading" | "unknown"
    standby: bool = False  # if True, model stays loaded between requests
    keep_alive_seconds_remaining: float | None = None  # None = no TTL set; -1 or inf = indefinite

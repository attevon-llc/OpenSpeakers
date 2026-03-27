from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class VoiceProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    model_id: str = Field(..., description="Which model this voice is for")


class VoiceProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_id: str
    reference_audio_path: str
    embedding_path: str | None
    extra_info: dict | None
    description: str | None = None
    tags: list = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


class VoiceProfileUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = None
    tags: list[str] | None = None


class VoiceListResponse(BaseModel):
    voices: list[VoiceProfileResponse]
    total: int


class BuiltinVoice(BaseModel):
    """A built-in (non-cloned) voice shipped with a model."""

    id: str
    name: str
    language: str
    gender: str | None = None
    model_id: str

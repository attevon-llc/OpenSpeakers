from __future__ import annotations

from fastapi import APIRouter

from app.api.endpoints import models, system, tts, voices

api_router = APIRouter(prefix="/api")

api_router.include_router(tts.router)
api_router.include_router(models.router)
api_router.include_router(voices.router)

"""Model Manager — singleton that owns GPU model lifecycle.

Only one model is loaded at a time (unless standby models are configured).
When a new model is requested the current model is unloaded, GPU cache is
cleared, and the new model is loaded.

Models are automatically unloaded after an idle timeout (default 60s) to
free GPU VRAM for other workers sharing the same GPU.  Models with
``standby: true`` in configs/models.yaml are exempt from idle unloading
and from the post-task unload in tts_tasks.py.

Usage (inside a Celery task):
    manager = ModelManager.get_instance()
    model = manager.load_model("vibevoice")
    result = model.generate(request)
"""

from __future__ import annotations

import logging
import math
import os
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.base import TTSModelBase

logger = logging.getLogger(__name__)

# Idle timeout in seconds before auto-unloading a model from GPU
MODEL_IDLE_TIMEOUT = int(os.environ.get("MODEL_IDLE_TIMEOUT", "60"))

# Path to models.yaml config (searched relative to project root)
_MODELS_CONFIG_PATHS = [
    Path("/app/configs/models.yaml"),  # inside Docker container
    Path(__file__).resolve().parents[3] / "configs" / "models.yaml",  # dev
]


def _load_standby_config() -> dict[str, bool]:
    """Read configs/models.yaml and return {model_id: standby_flag}."""
    try:
        import yaml
    except ImportError:
        logger.debug("PyYAML not installed — standby config unavailable")
        return {}

    for cfg_path in _MODELS_CONFIG_PATHS:
        if cfg_path.exists():
            try:
                with open(cfg_path) as f:
                    data = yaml.safe_load(f) or {}
                models = data.get("models", {})
                result: dict[str, bool] = {}
                for model_id, cfg in models.items():
                    if isinstance(cfg, dict):
                        result[model_id] = bool(cfg.get("standby", False))
                logger.info(
                    "Loaded standby config from %s: %s",
                    cfg_path,
                    {k: v for k, v in result.items() if v},
                )
                return result
            except Exception:
                logger.exception("Failed to parse %s", cfg_path)
    return {}


class ModelManager:
    """Singleton model manager for single-GPU hot-swap with idle unload."""

    _instance: ModelManager | None = None
    _singleton_lock = threading.Lock()

    def __init__(self) -> None:
        self._load_lock = threading.Lock()
        self.current_model_id: str | None = None
        self.current_model: TTSModelBase | None = None
        self._loading_model_id: str | None = None
        self._last_used: float = 0.0
        # >0 while a task is actively generating — idle timer must not unload
        self._in_use: int = 0
        # Registry: model_id -> class (not instance)
        self._registry: dict[str, type[TTSModelBase]] = {}
        self._device: str = "cuda"
        # Standby config: model_id -> True if model should stay loaded
        self._standby: dict[str, bool] = _load_standby_config()
        # Per-model keep_alive TTL: model_id → monotonic expiry timestamp
        # Special values: math.inf = indefinite, absent/expired = use idle timer
        self._keep_alive_until: dict[str, float] = {}
        self._register_defaults()
        self._apply_standby_flags()
        self._start_idle_timer()

    @classmethod
    def get_instance(cls) -> ModelManager:
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # -- Registration -------------------------------------------------------

    def _register_defaults(self) -> None:
        """Register all known model implementations."""
        try:
            from app.models.vibevoice import VibeVoiceModel

            self.register("vibevoice", VibeVoiceModel)
        except ImportError:
            logger.debug("VibeVoice dependencies not installed")

        try:
            from app.models.vibevoice_1p5b import VibeVoice1p5BModel

            self.register("vibevoice-1.5b", VibeVoice1p5BModel)
        except ImportError:
            logger.debug("VibeVoice 1.5B dependencies not installed")

        try:
            from app.models.fish_speech import FishSpeechModel

            self.register("fish-speech-s2", FishSpeechModel)
        except ImportError:
            logger.debug("Fish Speech dependencies not installed")

        try:
            from app.models.kokoro import KokoroModel

            self.register("kokoro", KokoroModel)
        except ImportError:
            logger.debug("Kokoro dependencies not installed")

        try:
            from app.models.qwen3_tts import Qwen3TTSModel

            self.register("qwen3-tts", Qwen3TTSModel)
        except ImportError:
            logger.debug("Qwen3 TTS dependencies not installed")

        try:
            from app.models.f5_tts import F5TTSModel

            self.register("f5-tts", F5TTSModel)
        except ImportError:
            logger.debug("F5-TTS dependencies not installed")

        try:
            from app.models.chatterbox import ChatterboxModel

            self.register("chatterbox", ChatterboxModel)
        except ImportError:
            logger.debug("Chatterbox dependencies not installed")

        try:
            from app.models.orpheus import OrpheusTTSModel

            self.register("orpheus-3b", OrpheusTTSModel)
        except ImportError:
            logger.debug("Orpheus 3B dependencies not installed")

        try:
            from app.models.cosyvoice import CosyVoice2Model

            self.register("cosyvoice-2", CosyVoice2Model)
        except ImportError:
            logger.debug("CosyVoice 2.0 dependencies not installed")

        try:
            from app.models.parler_tts import ParlerTTSModel

            self.register("parler-tts", ParlerTTSModel)
        except ImportError:
            logger.debug("Parler TTS dependencies not installed")

        try:
            from app.models.dia_tts import DiaTTSModel

            self.register("dia-1b", DiaTTSModel)
        except ImportError:
            logger.debug("Dia 1.6B dependencies not installed")

    def _apply_standby_flags(self) -> None:
        """Set the ``standby`` attribute on registered model classes from config."""
        for model_id, is_standby in self._standby.items():
            if model_id in self._registry and is_standby:
                # Set on the class so every new instance inherits the flag
                self._registry[model_id].standby = True
                logger.info("Model %s marked as standby", model_id)

    def register(self, model_id: str, model_class: type[TTSModelBase]) -> None:
        self._registry[model_id] = model_class
        logger.info("Registered model: %s", model_id)

    # -- Standby helpers ----------------------------------------------------

    def is_standby(self, model_id: str) -> bool:
        """Return True if model_id is configured as a standby model."""
        return self._standby.get(model_id, False)

    def get_standby_models(self) -> list[str]:
        """Return list of model IDs configured as standby."""
        return [mid for mid, flag in self._standby.items() if flag]

    # -- Keep-alive / TTL ---------------------------------------------------

    def set_keep_alive(self, model_id: str, seconds: int | None) -> None:
        """Set a per-model keep_alive TTL (Ollama-style semantics).

        seconds:
          None → clear any TTL; model falls back to the global idle timeout
             0 → clear TTL (unload as soon as the next idle check fires)
            -1 → keep indefinitely (never idle-unload)
            >0 → keep loaded for N seconds after this call
        """
        if seconds is None or seconds == 0:
            self._keep_alive_until.pop(model_id, None)
            logger.debug("keep_alive cleared for %s (will use idle timeout)", model_id)
        elif seconds < 0:
            self._keep_alive_until[model_id] = math.inf
            logger.info("keep_alive set to INDEFINITE for %s", model_id)
        else:
            expiry = time.monotonic() + seconds
            self._keep_alive_until[model_id] = expiry
            logger.info(
                "keep_alive set for %s: %ds (expires in %.0fs)",
                model_id,
                seconds,
                seconds,
            )

    def _is_keep_alive_active(self, model_id: str | None) -> bool:
        """Return True if the model has an unexpired keep_alive TTL."""
        if model_id is None:
            return False
        expiry = self._keep_alive_until.get(model_id)
        if expiry is None:
            return False
        return expiry == math.inf or time.monotonic() < expiry

    def get_keep_alive_remaining(self, model_id: str) -> float | None:
        """Return seconds remaining on keep_alive TTL, or None if not set.

        Returns math.inf if keep_alive is indefinite.
        Returns a negative number if the TTL has expired.
        """
        expiry = self._keep_alive_until.get(model_id)
        if expiry is None:
            return None
        if expiry == math.inf:
            return math.inf
        return expiry - time.monotonic()

    # -- Model loading ------------------------------------------------------

    def load_model(self, model_id: str, device: str | None = None) -> TTSModelBase:
        """Load model_id, unloading the current model if different.

        Thread-safe via _load_lock (Celery uses concurrency=1 but we protect anyway).
        Returns the loaded model instance.

        If the current model has ``standby=True``, it is kept loaded — the new model
        is loaded alongside it (assumes enough VRAM).  Non-standby models are always
        unloaded before loading a different model.
        """
        device = device or self._device

        with self._load_lock:
            self._last_used = time.monotonic()

            if self.current_model_id == model_id and self.current_model is not None:
                logger.debug("Model %s already loaded", model_id)
                return self.current_model

            if model_id not in self._registry:
                raise ValueError(f"Unknown model: {model_id!r}. Available: {list(self._registry)}")

            # Unload current model — unless it is a standby model
            if self.current_model is not None:
                if self.is_standby(self.current_model_id):
                    logger.info(
                        "Keeping standby model %s loaded (%.1f GB); loading %s alongside",
                        self.current_model_id,
                        getattr(self.current_model, "vram_gb_estimate", 0),
                        model_id,
                    )
                    # We intentionally do NOT unload. The standby model stays in VRAM.
                    # Clear current pointer so the new model becomes "current".
                else:
                    self._unload_current()

            # Load new model
            logger.info("Loading model %s on device %s", model_id, device)
            self._loading_model_id = model_id
            model_class = self._registry[model_id]
            model = model_class()
            model.load(device=device)
            self.current_model = model
            self.current_model_id = model_id
            self._loading_model_id = None
            self._last_used = time.monotonic()
            logger.info("Model %s loaded successfully", model_id)
            return model

    def _unload_current(self) -> None:
        """Unload the current model and free GPU memory."""
        if self.current_model is None:
            return
        model_id = self.current_model_id
        logger.info("Unloading model %s", model_id)
        try:
            self.current_model.unload()
        except Exception:
            logger.exception("Error unloading model %s", model_id)
        finally:
            self.current_model = None
            self.current_model_id = None
            # Clear any keep_alive TTL for this model on unload
            self._keep_alive_until.pop(model_id, None)
            self._clear_gpu_cache()

    def _clear_gpu_cache(self) -> None:
        try:
            import gc

            gc.collect()
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.debug("GPU cache cleared (gc.collect + empty_cache)")
        except ImportError:
            pass

    def mark_in_use(self) -> None:
        """Call before starting inference — prevents idle timer from unloading mid-generation."""
        self._in_use += 1
        self._last_used = time.monotonic()

    def mark_done(self) -> None:
        """Call after inference completes — refreshes last-used time so idle countdown restarts."""
        self._in_use = max(0, self._in_use - 1)
        self._last_used = time.monotonic()

    def unload_all(self, *, respect_standby: bool = True) -> None:
        """Unload all loaded models.

        If *respect_standby* is True (the default), standby models are kept loaded,
        and models with an active keep_alive TTL are kept loaded.
        Pass ``respect_standby=False`` to force-unload everything (e.g. on shutdown).
        """
        with self._load_lock:
            if self.current_model is not None and respect_standby:
                model_id = self.current_model_id
                if self.is_standby(model_id):
                    logger.info("Keeping standby model %s loaded after task", model_id)
                    return
                if self._is_keep_alive_active(model_id):
                    remaining = self.get_keep_alive_remaining(model_id)
                    logger.info(
                        "Keeping model %s loaded (keep_alive active, %.0fs remaining)",
                        model_id,
                        remaining if remaining != math.inf else -1,
                    )
                    return
            self._unload_current()

    # -- Idle auto-unload ---------------------------------------------------

    def _start_idle_timer(self) -> None:
        """Start a background thread that unloads models after idle timeout."""
        if MODEL_IDLE_TIMEOUT <= 0:
            logger.info("Model idle unload disabled (MODEL_IDLE_TIMEOUT=0)")
            return

        def _check_idle():
            while True:
                time.sleep(60)  # check every minute
                if self.current_model is None:
                    continue
                model_id = self.current_model_id
                # Standby models are never idle-unloaded
                if self.is_standby(model_id):
                    continue
                # Models with active keep_alive are not idle-unloaded
                if self._is_keep_alive_active(model_id):
                    remaining = self.get_keep_alive_remaining(model_id)
                    logger.debug(
                        "Model %s has active keep_alive (%.0fs remaining), skipping idle unload",
                        model_id,
                        remaining if remaining != math.inf else -1,
                    )
                    continue
                if self._in_use > 0:
                    # A task is actively using the model — skip this cycle entirely
                    logger.debug(
                        "Model %s in use (%d), skipping idle check",
                        model_id,
                        self._in_use,
                    )
                    continue
                idle_seconds = time.monotonic() - self._last_used
                if idle_seconds >= MODEL_IDLE_TIMEOUT:
                    logger.info(
                        "Model %s idle for %.0fs (timeout=%ds), unloading to free GPU",
                        model_id,
                        idle_seconds,
                        MODEL_IDLE_TIMEOUT,
                    )
                    with self._load_lock:
                        # Double-check after acquiring lock
                        if self.current_model is not None and self._in_use == 0:
                            mid = self.current_model_id
                            if self.is_standby(mid) or self._is_keep_alive_active(mid):
                                continue
                            idle_now = time.monotonic() - self._last_used
                            if idle_now >= MODEL_IDLE_TIMEOUT:
                                self._unload_current()

        t = threading.Thread(target=_check_idle, daemon=True, name="model-idle-timer")
        t.start()
        logger.info("Model idle unload timer started (timeout=%ds)", MODEL_IDLE_TIMEOUT)

    # -- Status -------------------------------------------------------------

    def get_status(self, model_id: str) -> dict:
        """Return status dict for a specific model."""
        if model_id not in self._registry:
            return {"id": model_id, "status": "unknown"}

        if model_id == self._loading_model_id:
            status = "loading"
        elif model_id == self.current_model_id:
            status = "loaded"
        else:
            status = "available"

        model_class = self._registry[model_id]
        instance = model_class()
        info = instance.get_info()
        info["status"] = status
        info["standby"] = self.is_standby(model_id)
        remaining = self.get_keep_alive_remaining(model_id)
        info["keep_alive_seconds_remaining"] = remaining if remaining is not None else None
        return info

    def list_models(self) -> list[dict]:
        """Return status dicts for all registered models."""
        return [self.get_status(mid) for mid in self._registry]

    @property
    def registered_ids(self) -> list[str]:
        return list(self._registry.keys())

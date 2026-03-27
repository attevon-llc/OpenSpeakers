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
        logger.info("Unloading model %s", self.current_model_id)
        try:
            self.current_model.unload()
        except Exception:
            logger.exception("Error unloading model %s", self.current_model_id)
        finally:
            self.current_model = None
            self.current_model_id = None
            self._clear_gpu_cache()

    def _clear_gpu_cache(self) -> None:
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.debug("GPU cache cleared")
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

        If *respect_standby* is True (the default), standby models are kept loaded.
        Pass ``respect_standby=False`` to force-unload everything (e.g. on shutdown).
        """
        with self._load_lock:
            if (
                self.current_model is not None
                and respect_standby
                and self.is_standby(self.current_model_id)
            ):
                logger.info(
                    "Keeping standby model %s loaded after task completion",
                    self.current_model_id,
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
                # Standby models are never idle-unloaded
                if self.is_standby(self.current_model_id):
                    continue
                if self._in_use > 0:
                    # A task is actively using the model — skip this cycle entirely
                    logger.debug(
                        "Model %s in use (%d), skipping idle check",
                        self.current_model_id,
                        self._in_use,
                    )
                    continue
                idle_seconds = time.monotonic() - self._last_used
                if idle_seconds >= MODEL_IDLE_TIMEOUT:
                    logger.info(
                        "Model %s idle for %.0fs (timeout=%ds), unloading to free GPU",
                        self.current_model_id,
                        idle_seconds,
                        MODEL_IDLE_TIMEOUT,
                    )
                    with self._load_lock:
                        # Double-check after acquiring lock
                        if self.current_model is not None and self._in_use == 0:
                            if self.is_standby(self.current_model_id):
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
        return info

    def list_models(self) -> list[dict]:
        """Return status dicts for all registered models."""
        return [self.get_status(mid) for mid in self._registry]

    @property
    def registered_ids(self) -> list[str]:
        return list(self._registry.keys())

# CLAUDE.md — OpenSpeakers

## Project Overview

OpenSpeakers is a unified TTS and voice cloning application supporting 11 open-source
models with GPU hot-swap, async job queuing, real-time streaming, and a SvelteKit UI.

See `docs/PLAN.md` for the full implementation plan and `docs/MARKET_RESEARCH.md` for
competitor analysis.

## Architecture

- **Frontend**: SvelteKit 2 + Svelte 5 runes + TypeScript + Tailwind CSS (port 5200)
- **Backend**: FastAPI + SQLAlchemy 2.0 + Alembic (port 8080)
- **Queue**: Celery + Redis (concurrency=1 per worker for GPU serialization)
- **Database**: PostgreSQL (job history, voice profiles, batch tracking)
- **Models**: Hot-swapped on GPU via `ModelManager` singleton; Kokoro stays in standby

## Key Design: Model Hot-Swap

`backend/app/models/manager.py` — `ModelManager` is a singleton that:
1. Tracks `current_model_id` (which model is in GPU VRAM)
2. On `load_model(id)`: unloads current + `torch.cuda.empty_cache()`, then loads new
3. GPU access serialized via `threading.Lock` (Celery worker concurrency=1)
4. Idle timer (60 s): auto-unloads non-standby models between tasks
5. `standby: true` models (Kokoro) stay loaded permanently
6. Only Celery workers load ML models; the FastAPI backend never touches the GPU

## Worker Architecture

Each model group runs in its own container on a dedicated Celery queue:

| Container | Queue | Models | Dockerfile |
|-----------|-------|--------|------------|
| `worker` | `tts` | Kokoro, VibeVoice 0.5B, VibeVoice 1.5B | `Dockerfile.worker` |
| `worker-fish` | `tts.fish-speech` | Fish Audio S2-Pro | `Dockerfile.worker-fish` |
| `worker-qwen3` | `tts.qwen3` | Qwen3 TTS | `Dockerfile.worker-qwen3` |
| `worker-orpheus` | `tts.orpheus` | Orpheus 3B | `Dockerfile.worker-orpheus` |
| `worker-dia` | `tts.dia` | Dia 1.6B | `Dockerfile.worker-dia` |
| `worker-f5` | `tts.f5-tts` | F5-TTS, Chatterbox, CosyVoice 2.0 | `Dockerfile.worker-f5` |

Queue routing is the single source of truth in `QUEUE_MAP` in
`backend/app/api/endpoints/tts.py`.

All secondary workers inherit from `backend/Dockerfile.base-gpu` which provides:
- PyTorch 2.10.0+cu128 and torchaudio
- NVIDIA env vars baked in (`NVIDIA_VISIBLE_DEVICES=all`)
- Common audio/ML packages (soundfile, numpy, scipy, librosa, accelerate)

Note: flash-attn is NOT in the base image — it requires nvcc at build time which is absent
from python:3.12-slim. The main worker uses a separate base with flash-attn pre-built.

## Model Abstraction

All TTS models implement `TTSModelBase` (`backend/app/models/base.py`):

```python
class TTSModelBase:
    model_id: str
    model_name: str
    description: str
    supports_voice_cloning: bool = False
    supports_streaming: bool = False
    supports_speed: bool = False    # show speed slider in UI
    supports_pitch: bool = False    # show pitch slider in UI
    vram_gb_estimate: float = 0.0

    def load(self, device: str = "cuda") -> None: ...
    def unload(self) -> None: ...
    def generate(self, request: GenerateRequest) -> GenerateResult: ...
    def stream_generate(self, request: GenerateRequest) -> Iterator[bytes]: ...
    def clone_voice(self, audio_path: str, name: str) -> dict: ...
```

## Adding a New Model

1. Create `backend/app/models/<name>.py` implementing `TTSModelBase`
2. Register in `ModelManager._register_defaults()` in `manager.py`
3. Add config entry to `configs/models.yaml`
4. If it needs a dedicated worker: add `Dockerfile.worker-<name>` and a new service
   in `docker-compose.yml` with the appropriate queue name

```python
# backend/app/models/my_model.py
from app.models.base import TTSModelBase, GenerateRequest, GenerateResult

class MyModel(TTSModelBase):
    model_id = "my-model"
    model_name = "My TTS Model"
    description = "..."
    supports_voice_cloning = False
    supports_streaming = False
    supports_speed = False

    def load(self, device: str = "cuda") -> None:
        self._model = ...       # load weights
        self._loaded = True

    def unload(self) -> None:
        self._model = None
        self._loaded = False
        import torch; torch.cuda.empty_cache()

    def generate(self, request: GenerateRequest) -> GenerateResult:
        audio_bytes = ...
        return GenerateResult(audio_bytes=audio_bytes, sample_rate=24000,
                              duration_seconds=..., format="wav")
```

## API Endpoints

### TTS (`/api/tts/`)
- `POST /generate` — submit job
- `GET /jobs/{id}` — poll status
- `GET /jobs/{id}/audio` — stream audio
- `GET /jobs` — list with pagination + filter (`page`, `page_size`, `status`, `model_id`, `search`)
- `DELETE /jobs/{id}` — cancel (revokes Celery task via `celery_app.control.revoke`)
- `POST /batch` — submit up to 100 lines; returns `batch_id` + `job_ids[]`
- `GET /batches/{id}` — aggregate batch status
- `GET /batches/{id}/zip` — stream ZIP of all complete audio files

### Voices (`/api/voices/`)
- `GET /` — list all voice profiles
- `POST /` — create (multipart upload of reference audio)
- `GET /{id}` — get single profile
- `PATCH /{id}` — update name, description, tags
- `GET /{id}/audio` — stream reference audio file
- `DELETE /{id}` — delete profile + audio file
- `GET /builtin/{model_id}` — list preset voices (e.g. Kokoro's 50+ voices)

### Models (`/api/models/`)
- `GET /` — all models with capabilities (`supports_speed`, `supports_pitch`, etc.)
- `GET /{id}` — single model info

### System (`/api/system/`)
- `GET /health` — health check
- `GET /gpu` — GPU stats snapshot

### OpenAI Compat (`/v1/`)
- `POST /audio/speech` — OpenAI-compatible; maps `tts-1` → Kokoro, `tts-1-hd` → Orpheus 3B
- `GET /models` — OpenAI-format model list

### WebSocket (`/ws/`)
- `/ws/jobs/{id}` — events: `queued`, `loading`, `generating`, `audio_chunk`, `complete`, `failed`
- `/ws/gpu` — GPU stats stream (1 s interval)

## Development Commands

```bash
# Start all services (full GPU stack)
docker compose -f docker-compose.yml -f docker-compose.override.yml \
               -f docker-compose.gpu.yml up -d

# Start lightweight (no GPU workers)
docker compose up postgres redis backend frontend

# Run backend tests
docker compose exec backend pytest tests/ -v

# Apply DB migrations
docker compose exec backend alembic upgrade head

# Generate new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Frontend type check (rollup native binding requires container)
docker compose exec frontend npm run check

# Rebuild one worker
docker compose -f docker-compose.yml -f docker-compose.override.yml \
               -f docker-compose.gpu.yml up -d --build worker-orpheus

# Tail worker logs
docker compose logs -f worker-orpheus

# Access backend shell
docker compose exec backend bash

# Smoke test all models
docker compose exec worker python scripts/test_all_models.py
```

## Important File Locations

| Path | Purpose |
|------|---------|
| `backend/app/models/manager.py` | ModelManager singleton (hot-swap + idle timer) |
| `backend/app/models/base.py` | TTSModelBase abstract class |
| `backend/app/models/kokoro.py` | Kokoro 82M (standby model) |
| `backend/app/models/vibevoice.py` | VibeVoice 0.5B with streaming |
| `backend/app/models/vibevoice_1p5b.py` | VibeVoice 1.5B (zero-shot cloning) |
| `backend/app/models/fish_speech.py` | Fish Audio S2-Pro |
| `backend/app/models/qwen3_tts.py` | Qwen3 TTS 1.7B |
| `backend/app/models/orpheus.py` | Orpheus 3B (vLLM backend) |
| `backend/app/models/dia_tts.py` | Dia 1.6B dialogue model |
| `backend/app/tasks/tts_tasks.py` | Celery tasks (generation + streaming) |
| `backend/app/api/endpoints/tts.py` | TTS routes + QUEUE_MAP |
| `backend/app/api/endpoints/openai_compat.py` | OpenAI /v1/audio/speech |
| `backend/app/db/models.py` | SQLAlchemy ORM (TTSJob, VoiceProfile) |
| `backend/alembic/versions/` | DB migration files |
| `configs/models.yaml` | Model registry (enable/disable/configure) |
| `frontend/src/routes/tts/+page.svelte` | Main TTS page |
| `frontend/src/routes/batch/+page.svelte` | Batch generation page |
| `frontend/src/routes/history/+page.svelte` | Job history page |
| `frontend/src/components/ModelParams.svelte` | Per-model parameter controls |
| `frontend/src/components/ToastContainer.svelte` | Toast notification system |
| `frontend/src/lib/stores/toasts.ts` | Toast store (addToast, removeToast) |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GPU_DEVICE_ID` | `0` | CUDA device index for all workers |
| `MODEL_CACHE_DIR` | `./models` | HuggingFace cache root (mounted as volume) |
| `AUDIO_OUTPUT_DIR` | `./audio_output` | Generated audio storage |
| `DATABASE_URL` | auto | PostgreSQL connection string |
| `CELERY_BROKER_URL` | auto | Redis URL |
| `HF_TOKEN` | — | Required for gated models (Orpheus 3B) |
| `BACKEND_PORT` | `8080` | Exposed API port |
| `FRONTEND_PORT` | `5200` | Exposed UI port |

## Service URLs (dev)

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5200 |
| Backend API | http://localhost:8080/api |
| API Docs (Swagger) | http://localhost:8080/docs |
| ReDoc | http://localhost:8080/redoc |
| PostgreSQL | localhost:5432 (127.0.0.1 only) |
| Redis | localhost:6379 (127.0.0.1 only) |

## DB Schema Notes

`TTSJob` columns of note:
- `celery_task_id` — set at task start; used by cancel endpoint to revoke
- `batch_id` — UUID grouping jobs created by a single batch request
- `status` — enum: `pending`, `running`, `complete`, `failed`, `cancelled`

`VoiceProfile` columns of note:
- `description` — optional free-text description
- `tags` — JSON array of string tags
- `reference_audio_path` — path to uploaded reference audio file

## Known Limitations / Deferred

- **Qwen3 streaming**: `non_streaming_mode=False` exists but docs say it only "simulates"
  streaming text input — not true PCM streaming. Currently forced to `non_streaming_mode=True`.
- **flash-attn in base image**: requires nvcc at build time (not in python:3.12-slim). Main
  worker uses a separate base image with flash-attn pre-built. Secondary workers use sdpa fallback.
- **F5-TTS, Chatterbox, CosyVoice 2.0, Parler TTS**: model stubs registered in the registry
  but `worker-f5` container is not yet built/deployed. Implementation is complete; just needs
  the container to be built and started.

# OpenSpeakers

A unified, self-hosted TTS and voice cloning application supporting 11 open-source models
with GPU hot-swap, async job queuing, real-time streaming, and a modern SvelteKit UI.

## Features

- **11 TTS models** — Kokoro, VibeVoice 0.5B/1.5B, Fish Audio S2-Pro, Qwen3 TTS,
  Orpheus 3B, Dia 1.6B, F5-TTS, Chatterbox, CosyVoice 2.0, Parler TTS
- **GPU hot-swap** — only one model in VRAM at a time; auto-evict with 60 s idle timer
- **Voice cloning** — zero-shot cloning with reference audio (Fish S2-Pro, VibeVoice 1.5B, Qwen3)
- **Streaming audio** — real-time PCM chunks via WebSocket (VibeVoice 0.5B)
- **Async job queue** — Celery + Redis; one generation at a time per worker
- **Job cancel** — revoke pending or running jobs mid-flight
- **Batch generation** — submit up to 100 lines at once, download all as ZIP
- **OpenAI-compatible API** — drop-in `/v1/audio/speech` endpoint
- **Full job history** — search, filter by model/status, pagination
- **Model comparison** — generate the same text with multiple models side-by-side
- **Voice management** — rename, add description and tags, preview reference audio
- **Emotion/style tags** — Fish S2-Pro `[whisper]`, `[excited]`; Orpheus `<laugh>`, `<sigh>`
- **Dialogue mode** — Dia 1.6B `[S1]`/`[S2]` multi-speaker scripting
- **Dark mode** — default dark theme with toggle
- **Mobile responsive** — sidebar collapses on small screens
- **Keyboard shortcuts** — press `?` for the help modal

## Supported Models

| Model | VRAM | Cloning | Streaming | Languages | Notes |
|-------|------|---------|-----------|-----------|-------|
| **Kokoro 82M** | ~0.5 GB | — | ✓ | 8 | Lightweight, always in standby |
| **VibeVoice 0.5B** | ~5 GB | — | ✓ | 12+ | Real-time streaming |
| **VibeVoice 1.5B** | ~12 GB | ✓ zero-shot | — | 10+ | Multi-speaker, long-form |
| **Fish Audio S2-Pro** | ~22 GB | ✓ zero-shot | ✓ | 80+ | 15K emotion tags |
| **Qwen3 TTS 1.7B** | ~10 GB | ✓ zero-shot | — | 10+ | Voice design via instruct text |
| **Orpheus 3B** | ~7 GB | — | ✓ | EN | Llama-based, emotion/intonation tags |
| **Dia 1.6B** | ~10 GB | ✓ | ✓ | EN | [S1]/[S2] dialogue, nonverbal sounds |
| **F5-TTS** | ~3 GB | ✓ zero-shot | ✓ | EN/ZH+ | Flow matching, 15x realtime |
| **Chatterbox** | ~5 GB | ✓ zero-shot | ✓ | 23 | Emotion exaggeration control |
| **CosyVoice 2.0** | ~5 GB | ✓ zero-shot | ✓ | Multi | 150 ms latency, voice design |
| **Parler TTS Mini** | ~3 GB | — | ✓ | EN | Describe any voice in natural language |

## Quick Start

### Prerequisites

- Docker + Docker Compose v2
- NVIDIA GPU with >= 8 GB VRAM (48 GB A6000 recommended for larger models)
- NVIDIA Container Toolkit (`nvidia-docker2`)

### Setup

```bash
# Clone the repo
git clone https://github.com/davidamacey/OpenSpeakers.git
cd OpenSpeakers

# Copy and edit environment file
cp .env.example .env

# Build the shared GPU base image first
docker build --network=host -t open_speakers-gpu-base:latest \
  -f backend/Dockerfile.base-gpu backend/

# Build and start all services
docker compose -f docker-compose.yml \
               -f docker-compose.override.yml \
               -f docker-compose.gpu.yml up -d --build

# Run database migrations
docker compose exec backend alembic upgrade head
```

The frontend will be available at **http://localhost:5200** and the API at **http://localhost:8080**.

### First Use

1. Open the **Models** page to browse available models and their capabilities
2. Go to **TTS**, select a model, enter text and click **Generate**
3. Use the **Clone** page to upload reference audio and create voice profiles
4. Use the **Batch** page to generate multiple lines at once
5. Use the **Compare** page to run the same text through multiple models

## Docker Architecture

OpenSpeakers uses **dedicated Celery workers per model group** to isolate GPU memory and
Python environments. Each worker listens on its own queue.

| Service | Queue | Models | Notes |
|---------|-------|--------|-------|
| `worker` | `tts` | Kokoro, VibeVoice 0.5B, VibeVoice 1.5B | Main worker |
| `worker-fish` | `tts.fish-speech` | Fish Audio S2-Pro | Custom CUDA build |
| `worker-qwen3` | `tts.qwen3` | Qwen3 TTS | transformers 5.x |
| `worker-orpheus` | `tts.orpheus` | Orpheus 3B | vLLM backend, 2 GB shm |
| `worker-dia` | `tts.dia` | Dia 1.6B | Reinstalls torch cu128 after Dia |
| `worker-f5` | `tts.f5-tts` | F5-TTS, Chatterbox, CosyVoice 2.0 | Light models |

All secondary workers inherit from `Dockerfile.base-gpu` which provides PyTorch 2.10+cu128
and common audio/ML packages.

## API Reference

### TTS Jobs

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/tts/generate` | Submit a generation job |
| `GET` | `/api/tts/jobs/{id}` | Get job status |
| `GET` | `/api/tts/jobs/{id}/audio` | Stream audio file |
| `GET` | `/api/tts/jobs` | List jobs (page, status, model, search) |
| `DELETE` | `/api/tts/jobs/{id}` | Cancel a pending/running job |
| `POST` | `/api/tts/batch` | Batch submit up to 100 lines |
| `GET` | `/api/tts/batches/{id}` | Batch status |
| `GET` | `/api/tts/batches/{id}/zip` | Download all audio as ZIP |

### Voice Profiles

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/voices` | List voice profiles |
| `POST` | `/api/voices` | Create (upload reference audio) |
| `GET` | `/api/voices/{id}` | Get single voice profile |
| `PATCH` | `/api/voices/{id}` | Update name, description, tags |
| `GET` | `/api/voices/{id}/audio` | Stream reference audio |
| `DELETE` | `/api/voices/{id}` | Delete voice profile |
| `GET` | `/api/voices/builtin/{model_id}` | List built-in voices for a model |

### Models

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/models` | List all registered models with capabilities |
| `GET` | `/api/models/{id}` | Get model info |

### OpenAI Compatibility

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/audio/speech` | OpenAI-compatible TTS endpoint |
| `GET` | `/v1/models` | OpenAI-format model list |

Use with any OpenAI-compatible client (Continue.dev, OpenWebUI, SillyTavern, etc.):

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8080/v1", api_key="not-needed")
audio = client.audio.speech.create(model="tts-1", voice="alloy", input="Hello world")
audio.stream_to_file("output.wav")
```

### WebSocket

| Path | Description |
|------|-------------|
| `/ws/jobs/{id}` | Real-time job progress and audio chunk events |
| `/ws/gpu` | Live GPU stats (utilization, temperature, power) |

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| TTS | `/tts` | Main text-to-speech generation with streaming |
| Clone | `/clone` | Upload reference audio, manage voice profiles |
| Compare | `/compare` | Side-by-side model comparison |
| Batch | `/batch` | Bulk generation from pasted text or .txt file |
| History | `/history` | Full job history with search and filter |
| Models | `/models` | Model browser and capability reference |
| Settings | `/settings` | Output format, GPU stats, storage paths |
| About | `/about` | Model descriptions and project links |

## Project Structure

```
open_speakers/
├── backend/
│   ├── Dockerfile.base-gpu          # Shared GPU base (PyTorch 2.10+cu128)
│   ├── Dockerfile.worker            # Main worker (Kokoro + VibeVoice)
│   ├── Dockerfile.worker-fish       # Fish Speech worker
│   ├── Dockerfile.worker-qwen3      # Qwen3 TTS worker
│   ├── Dockerfile.worker-orpheus    # Orpheus 3B worker (vLLM)
│   ├── Dockerfile.worker-dia        # Dia 1.6B worker
│   ├── Dockerfile.worker-f5         # F5-TTS / Chatterbox / CosyVoice worker
│   └── app/
│       ├── api/endpoints/           # REST API routes + OpenAI compat
│       ├── models/                  # TTS model implementations
│       ├── tasks/                   # Celery tasks (generation, streaming)
│       ├── db/                      # SQLAlchemy ORM models + migrations
│       └── schemas/                 # Pydantic schemas
├── frontend/src/
│   ├── routes/                      # tts, clone, compare, batch, history, models, settings
│   ├── components/                  # AudioPlayer, ModelParams, ToastContainer, etc.
│   └── lib/                         # API clients, Svelte stores
├── configs/models.yaml              # Model registry (enable/disable models here)
├── docs/                            # PLAN.md, MARKET_RESEARCH.md
├── scripts/
│   ├── test_all_models.py           # Smoke-test all deployed models
│   └── package-offline.sh           # Air-gapped install packaging
├── docker-compose.yml               # Base service definitions
├── docker-compose.override.yml      # Dev build targets (auto-loaded)
├── docker-compose.gpu.yml           # NVIDIA GPU passthrough overlay
└── docker-compose.offline.yml       # Air-gapped / offline deployment
```

## Environment Variables

Copy `.env.example` to `.env` and set:

| Variable | Default | Description |
|----------|---------|-------------|
| `GPU_DEVICE_ID` | `0` | CUDA device index |
| `MODEL_CACHE_DIR` | `./models` | HuggingFace model cache root |
| `AUDIO_OUTPUT_DIR` | `./audio_output` | Generated audio storage |
| `POSTGRES_PASSWORD` | `openspeakers` | PostgreSQL password |
| `HF_TOKEN` | — | HuggingFace token (required for gated models like Orpheus) |
| `BACKEND_PORT` | `8080` | Backend API port |
| `FRONTEND_PORT` | `5200` | Frontend port |

## Development

```bash
# Start all services
docker compose -f docker-compose.yml -f docker-compose.override.yml \
               -f docker-compose.gpu.yml up -d

# Backend API docs (Swagger UI)
open http://localhost:8080/docs

# Run backend tests
docker compose exec backend pytest tests/ -v

# Frontend type check (must run inside container)
docker compose exec frontend npm run check

# Rebuild a specific worker after Dockerfile changes
docker compose -f docker-compose.yml -f docker-compose.override.yml \
               -f docker-compose.gpu.yml up -d --build worker-orpheus

# Apply DB migrations
docker compose exec backend alembic upgrade head

# Smoke test all models
docker compose exec worker python scripts/test_all_models.py
```

See `CLAUDE.md` for developer architecture notes and `docs/PLAN.md` for the full
feature roadmap and implementation details.

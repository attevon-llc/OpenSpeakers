# OpenSpeakers — Implementation Plan

## Completion Status

> Last updated: 2026-03-27

### Summary

All planned phases (1–6) are complete. 7 of 11 registered models are fully deployed and
working. The remaining 4 (F5-TTS, Chatterbox, CosyVoice 2.0, Parler TTS) have complete
implementations and are registered in the model registry, but the `worker-f5` container has
not yet been built or deployed.

### Phase 1 — Foundation: COMPLETE

- [x] Project scaffold: backend + frontend + Docker Compose
- [x] `TTSModelBase` abstraction layer
- [x] `ModelManager` singleton with hot-swap and `threading.Lock`
- [x] VibeVoice 0.5B implementation with PCM16 streaming
- [x] Fish Audio S2-Pro implementation (full, not stub)
- [x] Celery worker with single-GPU concurrency per container
- [x] FastAPI endpoints: generate, job status, audio download, model list
- [x] PostgreSQL schema + Alembic migrations
- [x] SvelteKit frontend: TTS page + streaming audio player
- [x] Docker build and smoke test (all 7 deployed models passing)

### Phase 2 — More Models: COMPLETE

- [x] Qwen3 TTS 1.7B implementation (`worker-qwen3` container)
- [x] Kokoro 82M implementation — standby model, always loaded
- [x] Orpheus 3B implementation (vLLM backend, `worker-orpheus` container)
- [x] Dia 1.6B implementation (`worker-dia` container)
- [x] `configs/models.yaml` model registry for easy enable/disable
- [x] VRAM estimates tracked per model in registry and UI

### Phase 3 — Voice Cloning: COMPLETE

- [x] Fish Audio S2-Pro zero-shot cloning
- [x] VibeVoice 1.5B zero-shot cloning (`voice_samples` parameter)
- [x] Qwen3 TTS zero-shot cloning (reference audio path)
- [x] Voice cloning page (`/clone`)
- [x] Voice profile persistence (PostgreSQL + file storage)
- [x] Voice profile management: rename, tag, describe, preview reference audio
- [x] Model comparison page (`/compare`) with sequential multi-model generation

### Phase 4 — Polish: COMPLETE

- [x] Streaming TTS output (VibeVoice 0.5B via Redis pub/sub + Web Audio API)
- [x] WebSocket progress for long generations (`/ws/jobs/{id}`)
- [x] Batch generation (`POST /api/tts/batch`) with ZIP download
- [x] Job cancellation (`DELETE /api/tts/jobs/{id}`)
- [x] Full job history page (`/history`) with search, filter, pagination
- [x] Toast notification system
- [x] Keyboard shortcuts modal
- [x] Mobile-responsive sidebar
- [x] Dark mode with FOUC prevention
- [x] Per-page `<title>` tags
- [x] WaveSurfer.js waveform visualisation

### Phase 5 — Model Expansion: COMPLETE (partial deployment)

- [x] VibeVoice 1.5B added to main `worker` container
- [x] F5-TTS implementation (registered; `worker-f5` not yet deployed)
- [x] Chatterbox implementation (registered; `worker-f5` not yet deployed)
- [x] CosyVoice 2.0 implementation (registered; `worker-f5` not yet deployed)
- [x] Parler TTS Mini implementation (registered; `worker-f5` not yet deployed)
- [ ] `worker-f5` container build and deployment — **PENDING**

### Phase 6 — OpenAI Compatibility: COMPLETE

- [x] `POST /v1/audio/speech` — OpenAI-compatible TTS endpoint
- [x] `GET /v1/models` — OpenAI-format model list
- [x] `tts-1` → Kokoro 82M mapping (fast, always available via standby)
- [x] `tts-1-hd` → Orpheus 3B mapping (highest quality)
- [x] `worker-kokoro` dedicated queue for low-latency OpenAI-compat responses
- [x] Ollama-style `keep_alive` parameter on generate and model-load endpoints
- [x] `POST /api/models/{id}/load` — pre-warm endpoint with `keep_alive`
- [x] `DELETE /api/models/{id}/load` — force-unload endpoint
- [x] `openspeakers.sh` management CLI

### Deferred / Not Planned

- **Qwen3 true streaming**: `non_streaming_mode=False` exists in the API but the library
  only simulates streaming text input, not true PCM chunk output. Deferred until confirmed
  otherwise.
- **flash-attn in base GPU image**: requires `nvcc` at build time (absent from
  `python:3.12-slim`). Secondary workers fall back to `sdpa`. Deferred.
- **MinIO object storage**: audio files stored on local disk. MinIO integration deferred.
- **API key authentication**: no auth layer; intended for single-user / LAN deployment.
- **Flower monitoring dashboard**: not deployed; use `docker compose logs` for monitoring.
- **Docker Hub publish** (`davidamacey/openspeakers`): not yet published.

---

## Overview

OpenSpeakers is a unified TTS (text-to-speech) and voice cloning application that runs
multiple open-source models on a single GPU with hot-swap capability. It follows the same
architecture as OpenTranscribe (Svelte frontend + FastAPI backend + Celery + Redis + PostgreSQL).

---

## Architecture

### Core Design Principles

1. **Single GPU, multiple models** — only one TTS model is loaded in GPU VRAM at a time.
   Hot-swapping means the current model is unloaded (and CUDA cache cleared) before loading
   the next. On an A6000 (48 GB) multiple lighter models could coexist, but we default to
   one-at-a-time for broadest hardware support (8–12 GB typical GPU).

2. **Model abstraction layer** — all TTS models implement `TTSModelBase`. Adding a new model
   is a matter of writing one class and registering it.

3. **Async job queue** — generation is dispatched to a Celery worker so the API returns
   immediately with a `job_id`. The frontend polls or connects via WebSocket for progress.

4. **Voice profiles** — cloned voices are stored as embeddings/reference audio and can be
   reused across generation requests.

### Services

```
┌─────────────────┐       ┌──────────────────┐
│   SvelteKit UI  │──────▶│  FastAPI Backend  │
│   (port 5173)   │◀──────│   (port 8080)     │
└─────────────────┘       └────────┬─────────┘
                                   │
                          ┌────────▼─────────┐
                          │  Redis (broker)   │
                          └────────┬─────────┘
                                   │
                          ┌────────▼─────────┐
                          │  Celery Worker    │
                          │  (concurrency=1)  │
                          │  Model Manager    │
                          └────────┬─────────┘
                                   │
                     ┌─────────────┼──────────────┐
                     │             │              │
              ┌──────▼───┐  ┌──────▼───┐  ┌──────▼───┐
              │VibeVoice │  │Fish Speech│  │ Qwen3 TTS│
              │  (loaded)│  │ (unloaded)│  │ (unloaded)│
              └──────────┘  └──────────┘  └──────────┘
```

### Model Hot-Swap Flow

```
Request: generate with fish-speech-s2
  │
  ├─ ModelManager.load_model("fish-speech-s2")
  │     ├─ current_model_id == "vibevoice"?  → unload + torch.cuda.empty_cache()
  │     └─ load FishSpeechModel to GPU
  │
  └─ model.generate(text, voice_config)
        └─ returns audio bytes
```

---

## Database Schema

### `tts_jobs`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| model_id | VARCHAR | Which model was used |
| text | TEXT | Input text |
| voice_profile_id | UUID FK | Voice profile used (nullable) |
| parameters | JSONB | Speed, pitch, language, etc. |
| status | ENUM | pending/running/complete/failed |
| error_message | TEXT | Error if failed |
| output_path | VARCHAR | Path to generated audio file |
| duration_seconds | FLOAT | Duration of generated audio |
| processing_time_ms | INT | Time taken to generate |
| created_at | TIMESTAMP | When job was created |
| completed_at | TIMESTAMP | When job finished |

### `voice_profiles`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR | Display name |
| model_id | VARCHAR | Which model this voice is for |
| reference_audio_path | VARCHAR | Path to reference audio |
| embedding_path | VARCHAR | Path to voice embedding (model-specific) |
| metadata | JSONB | Model-specific metadata |
| created_at | TIMESTAMP | Creation time |

### `model_configs`
| Column | Type | Description |
|--------|------|-------------|
| model_id | VARCHAR PK | Model identifier |
| enabled | BOOLEAN | Whether model is available |
| hf_repo | VARCHAR | HuggingFace repo ID |
| custom_config | JSONB | Override config |

---

## API Endpoints

### TTS
- `POST /api/tts/generate` — Submit TTS job → returns `{job_id}`
- `GET /api/tts/jobs/{job_id}` — Poll job status
- `GET /api/tts/jobs/{job_id}/audio` — Download generated audio
- `GET /api/tts/jobs` — List recent jobs (paginated)

### Models
- `GET /api/models` — List all registered models with status
- `GET /api/models/{model_id}` — Get model details
- `GET /api/models/{model_id}/status` — Loaded/unloaded/loading status

### Voices
- `GET /api/voices` — List saved voice profiles
- `POST /api/voices` — Create voice profile (upload reference audio)
- `DELETE /api/voices/{voice_id}` — Delete voice profile

### System
- `GET /health` — Health check
- `GET /api/system/info` — GPU info, model cache stats

---

## Frontend Pages

### 1. TTS Page (`/tts`)
- Model dropdown with status indicators (loaded/available)
- Text area (multi-line input)
- Voice selector (built-in voices + saved cloned voices)
- Parameter controls: speed (0.5–2.0), pitch (-12 to +12), language
- "Generate" button with loading state
- Audio player with waveform visualization
- Download button
- Job history panel (last 10 jobs)

### 2. Voice Cloning Page (`/clone`)
- Reference audio upload (WAV/MP3/FLAC, max 30 sec)
- Model selector (only models that support cloning)
- Voice name input
- Preview generation with cloned voice
- Saved voices gallery

### 3. Comparison Page (`/compare`)
- Text input (shared)
- Multi-model selector (pick 2–4 models)
- "Generate All" button
- Side-by-side audio players per model
- Quality rating (thumbs up/down for each)
- Export comparison as ZIP

### 4. Settings Page (`/settings`)
- GPU Configuration: device ID, VRAM limit
- Model Management: download/delete models, show VRAM usage
- Output: default format (WAV/MP3/OGG), sample rate
- Default parameters: speed, pitch, language

---

## Implementation Phases

### Phase 1 — Foundation (COMPLETE)
**Goal**: Two models working end-to-end with hot-swap.

- [x] Project scaffold: backend + frontend + Docker Compose
- [x] Model abstraction layer (`TTSModelBase`)
- [x] Model manager (hot-swap, singleton)
- [x] VibeVoice implementation (microsoft/VibeVoice-Realtime-0.5B)
- [x] Fish Speech S2-Pro full implementation (fishaudio/s2-pro)
- [x] Celery worker with single-GPU concurrency
- [x] FastAPI endpoints: generate, job status, model list
- [x] PostgreSQL schema + Alembic migrations
- [x] SvelteKit frontend: TTS page + audio player
- [x] Docker build and smoke test (all 7 models passing)

### Phase 2 — More Models (COMPLETE)
**Goal**: Qwen3 TTS and additional models.

- [x] Qwen3 TTS 1.7B implementation (`Qwen/Qwen3-TTS`)
- [x] Kokoro 82M implementation (`hexgrad/Kokoro-82M`) — standby model
- [x] Orpheus 3B implementation (`canopylabs/orpheus-3b-0.1-ft`) via vLLM
- [x] Dia 1.6B implementation (`nari-labs/Dia-1.6B`)
- [x] `configs/models.yaml` model registry for easy enable/disable
- [x] VRAM usage tracking per model

### Phase 3 — Voice Cloning (COMPLETE)
**Goal**: Full voice cloning UI and storage.

- [x] Fish Audio S2-Pro zero-shot voice cloning
- [x] VibeVoice 1.5B zero-shot cloning (`voice_samples`)
- [x] Qwen3 TTS zero-shot cloning (reference audio path)
- [x] Voice Cloning page (`/clone`)
- [x] Voice profile persistence (PostgreSQL + file storage)
- [x] Comparison page with multi-model side-by-side

### Phase 4 — Polish (COMPLETE)
**Goal**: Production-ready with presets and streaming.

- [x] Streaming TTS output — VibeVoice 0.5B PCM16 chunks via Redis pub/sub
- [x] WebSocket progress for long generations (`/ws/jobs/{id}`)
- [x] Batch generation (up to 100 lines) with ZIP download
- [x] Job cancellation (`DELETE /api/tts/jobs/{id}`)
- [x] Full job history page with search, filter, pagination
- [x] Toast notifications, keyboard shortcuts, mobile responsive layout
- [ ] Preset system (save parameter combinations) — deferred
- [ ] API key authentication — deferred (single-user / LAN use case)
- [ ] MinIO for audio file storage — deferred
- [ ] Flower monitoring dashboard — deferred
- [ ] Docker Hub publish (`davidamacey/openspeakers`) — deferred

---

## Model Details

### VibeVoice (Phase 1)
- **Repo**: `microsoft/VibeVoice-Realtime-0.5B`
- **Type**: End-to-end speech LM with diffusion TTS head
- **VRAM**: ~4–6 GB
- **Languages**: EN, DE, FR, ES, IT, PT, NL, PL, JP, KR, ZH
- **Voice cloning**: Yes (reference speaker embedding via .pt voice files)
- **Streaming**: Yes
- **Notes**: David has a forked repo at `/mnt/nvm/repos/VibeVoice`

### Fish Speech S2 (Phase 1 stub → Phase 3 full)
- **Repo**: `fishaudio/fish-speech-1.5`
- **Type**: VQGAN + LLM + HiFiGAN vocoder
- **VRAM**: ~4–6 GB
- **Languages**: EN, ZH, JP, KR, FR, DE, AR, ES
- **Voice cloning**: Yes (3–10 second reference clips)
- **Streaming**: Yes (chunked)

### Qwen3 TTS (Phase 2)
- **Repo**: `Qwen/Qwen3-TTS` (or similar)
- **Type**: LLM-based TTS
- **VRAM**: ~8–16 GB (depends on model size)
- **Languages**: 50+
- **Voice cloning**: Limited (via prompting)

### Kokoro (Phase 2)
- **Repo**: `hexgrad/Kokoro-82M`
- **Type**: StyleTTS2-derived, very small
- **VRAM**: < 1 GB
- **Languages**: EN, FR, ES, JA, ZH, KO, HI, PT, IT, ...
- **Voice cloning**: No (uses preset voices)
- **Notes**: Fast inference, good for testing hot-swap

---

## Development Workflow

```bash
# Start all services (dev mode with hot reload)
docker compose up

# Backend only
docker compose up backend redis postgres

# Worker only
docker compose up worker

# Frontend dev server
cd frontend && npm run dev

# Run migrations
docker compose exec backend alembic upgrade head

# Shell into worker
docker compose exec worker bash
```

## Port Map (development)
| Service | Port |
|---------|------|
| Frontend (Vite) | 5173 |
| Backend (FastAPI) | 8080 |
| PostgreSQL | 5432 |
| Redis | 6379 |

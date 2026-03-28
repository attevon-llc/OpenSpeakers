# Changelog

All notable changes to OpenSpeakers are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

#### Models
- Kokoro 82M TTS model — always-on standby model (~0.5 GB VRAM), 50+ built-in voices
- VibeVoice 0.5B — real-time PCM16 streaming via Redis pub/sub and Web Audio API
- VibeVoice 1.5B — zero-shot voice cloning from reference audio
- Fish Audio S2-Pro — zero-shot cloning, 80+ languages, 15 K emotion/style tags (`[whisper]`, `[excited]`, etc.)
- Qwen3 TTS 1.7B — zero-shot cloning, voice design via natural-language instruct text
- Orpheus 3B — Llama-based TTS with emotion/intonation tags (`<laugh>`, `<sigh>`, `<gasp>`, etc.); runs via vLLM backend
- Dia 1.6B — dialogue model with `[S1]`/`[S2]` multi-speaker scripting and nonverbal sound generation
- F5-TTS — flow matching TTS, zero-shot cloning, MIT license (`worker-f5` container)
- Chatterbox — emotion exaggeration control, zero-shot cloning, MIT license (`worker-f5` container)
- CosyVoice 2.0 — 150 ms latency, zero-shot cloning, voice design via text (`worker-f5` container)
- Parler TTS Mini — describe any voice in natural language, no reference audio needed (`worker-f5` container)

#### Backend — Core
- FastAPI backend (port 8080) with Pydantic v2 schemas and full OpenAPI docs
- SQLAlchemy 2.0 ORM with Alembic migrations for `tts_jobs` and `voice_profiles` tables
- PostgreSQL database (bound to 127.0.0.1 for security)
- Celery 5 + Redis async job queue with concurrency=1 per worker for GPU serialisation
- `ModelManager` singleton — hot-swap with `threading.Lock`, 60-second idle auto-unload timer
- `TTSModelBase` abstract class — uniform `load`, `unload`, `generate`, `stream_generate`, `clone_voice` interface
- `configs/models.yaml` model registry — enable/disable models without code changes

#### Backend — API Endpoints
- `POST /api/tts/generate` — submit TTS job with `keep_alive` parameter (Ollama-style VRAM retention: -1/0/N)
- `GET /api/tts/jobs/{id}` — poll job status and metadata
- `GET /api/tts/jobs/{id}/audio` — stream generated audio file
- `GET /api/tts/jobs` — paginated job list with `status`, `model_id`, and full-text `search` filters
- `DELETE /api/tts/jobs/{id}` — cancel pending or running job (revokes Celery task via `control.revoke`)
- `POST /api/tts/batch` — submit up to 100 lines in one request; returns `batch_id` + `job_ids[]`
- `GET /api/tts/batches/{id}` — aggregate batch status
- `GET /api/tts/batches/{id}/zip` — stream ZIP archive of all completed audio files
- `GET /api/voices/` — list voice profiles
- `POST /api/voices/` — create voice profile (multipart upload of reference audio)
- `GET /api/voices/{id}` — get single voice profile
- `PATCH /api/voices/{id}` — update name, description, and tags
- `GET /api/voices/{id}/audio` — stream reference audio file
- `DELETE /api/voices/{id}` — delete profile and associated audio file
- `GET /api/voices/builtin/{model_id}` — list preset built-in voices for a model
- `GET /api/models/` — list all models with full capabilities (`supports_speed`, `supports_pitch`, etc.)
- `GET /api/models/{id}` — get single model info
- `POST /api/models/{id}/load` — pre-warm a model with optional `keep_alive`
- `DELETE /api/models/{id}/load` — force-unload a model from VRAM
- `GET /api/system/health` — service health check
- `GET /api/system/gpu` — GPU stats snapshot (utilisation, temperature, power, VRAM)
- `POST /v1/audio/speech` — OpenAI-compatible TTS endpoint; maps `tts-1` → Kokoro, `tts-1-hd` → Orpheus 3B
- `GET /v1/models` — OpenAI-format model list
- `WS /ws/jobs/{id}` — real-time job events: `queued`, `loading`, `generating`, `audio_chunk`, `complete`, `failed`
- `WS /ws/gpu` — GPU stats WebSocket stream at 1-second intervals

#### Worker Architecture
- Dedicated Celery worker containers per model group for dependency and GPU isolation
- `worker-kokoro` container (`tts.kokoro` queue) — Kokoro 82M (standby — always loaded)
- `worker` container (`tts` queue) — VibeVoice 0.5B, VibeVoice 1.5B
- `worker-fish` container (`tts.fish-speech` queue) — Fish Audio S2-Pro
- `worker-qwen3` container (`tts.qwen3` queue) — Qwen3 TTS 1.7B
- `worker-orpheus` container (`tts.orpheus` queue) — Orpheus 3B (vLLM, 2 GB shared memory)
- `worker-dia` container (`tts.dia` queue) — Dia 1.6B
- `worker-f5` container (`tts.f5-tts` queue) — F5-TTS, Chatterbox, CosyVoice 2.0, Parler TTS Mini
- `Dockerfile.base-gpu` — shared GPU base image with PyTorch 2.10+cu128, torchaudio, and NVIDIA env vars
- `QUEUE_MAP` in `backend/app/api/endpoints/tts.py` as single source of truth for routing

#### Frontend
- SvelteKit 2 + Svelte 5 runes frontend (port 5200) with TypeScript and Tailwind CSS
- TTS page (`/tts`) — model selector, text area, voice selector, parameter controls, streaming audio player, recent jobs
- Clone page (`/clone`) — reference audio upload, cloning-capable model selector, voice profile gallery
- Compare page (`/compare`) — sequential multi-model comparison with side-by-side audio players
- Batch page (`/batch`) — multi-line text input, per-line progress indicators, ZIP download
- History page (`/history`) — searchable/filterable full job history with pagination
- Models page (`/models`) — model browser with capability table, VRAM estimates, and status indicators
- Settings page (`/settings`) — output format, live GPU stats via WebSocket, storage path display
- About page (`/about`) — model descriptions and links
- `AudioPlayer` component with WaveSurfer.js waveform, keyboard seek (arrows / Home / End)
- `ModelParams` component — per-model parameter controls (speed slider, pitch slider, voice selector)
- `ToastContainer` component + `toasts.ts` store — non-blocking success/error/warning notifications
- `WaveformPreview` component — WaveSurfer.js wrapper for embedded waveform display
- `KeyboardShortcutsModal` component — press `?` to show all shortcuts
- `GpuStatus` component — live GPU widget fed by `/ws/gpu`
- `JobProgress` component — real-time step indicator (Queue → Load → Generate → Done) with `aria-live`
- Dark mode default with `class="dark"` on `<html>`, FOUC-prevention script, and `ThemeToggle` component
- Mobile-responsive sidebar — hamburger toggle below 768 px, slide-in overlay, auto-close on navigation
- Per-page `<title>` tags for browser tab / accessibility
- Vite proxy for `/api`, `/ws`, `/docs`, `/redoc`, `/openapi.json`

#### Streaming Audio
- VibeVoice 0.5B `stream_generate()` yields PCM16 bytes via `AudioStreamer` background thread
- Celery task detects `supports_streaming` and publishes `audio_chunk` Redis pub/sub events while assembling final WAV
- Frontend `JobProgress.svelte` schedules Web Audio API buffers using `nextStartTime` pattern for gapless playback
- Streaming indicator disappears and full `AudioPlayer` appears when `complete` event arrives

#### Output Formats
- WAV (native), MP3, OGG — format converted via ffmpeg transcoding in the worker

#### Voice Cloning
- Fish Audio S2-Pro `clone_voice()` — reference audio embedded in S2-Pro's VQGAN codec
- VibeVoice 1.5B `clone_voice()` — zero-shot via `voice_samples` parameter
- Qwen3 TTS `clone_voice()` — zero-shot via reference audio path

#### OpenAI Compat
- `POST /v1/audio/speech` routes to dedicated `worker-kokoro` queue for Kokoro, ensuring low-latency response
- Compatible with `openai` Python SDK, Continue.dev, OpenWebUI, SillyTavern, and any app using the OpenAI TTS API

#### Infrastructure
- `openspeakers.sh` management CLI — `start`, `stop`, `restart`, `status`, `logs`, `health`, `workers`, `db`, `build`, `shell`, `test`, `gpu`, `clean`, `purge`
- `docker-compose.yml` — base service definitions
- `docker-compose.override.yml` — dev build targets (auto-loaded)
- `docker-compose.gpu.yml` — NVIDIA GPU passthrough overlay
- `docker-compose.offline.yml` — air-gapped / offline deployment
- PostgreSQL and Redis bound to `127.0.0.1` only (not LAN-accessible)
- `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` on Fish worker for S2-Pro memory management

### Fixed
- `VoiceProfile.metadata` renamed to `extra_info` to avoid SQLAlchemy reserved name collision
- `Enum(JobStatus)` uses `values_callable` so stored values are lowercase (`pending`, not `PENDING`)
- `vite.config.ts` corrected import of `sveltekit` to use `@sveltejs/kit/vite`
- `@sveltejs/vite-plugin-svelte` bumped to v5 for Vite 6 compatibility
- `backend/Dockerfile.worker` created (was missing; ML dependencies were not installed in worker container)
- spaCy `en_core_web_sm` model added to `Dockerfile.worker` (required by Kokoro text normalisation)
- Fish Speech: sentinel `None` sent to `launch_thread_safe_queue` before deleting queue reference on unload (without this, daemon thread held 14.7 GB of VRAM after "unload")
- Orpheus 3B `gpu_memory_utilization` set to `0.5` (vLLM default of 0.9 consumed 42 GB)
- Orpheus 3B `unload()` calls `self._model.engine.shutdown()` to terminate vLLM subprocesses
- Step indicator clipping — fixed with `flex-wrap` and compact labels
- Recent jobs "play" button calls `loadRecentJob()` which loads audio into main player and autoplays
- Dark mode contrast fixes in TTS empty state, job progress bar background, and model selector info box
- `settings/+page.svelte` pre-existing TypeScript narrowing issue with `$derived` and optional chaining

---

[Unreleased]: https://github.com/davidamacey/OpenSpeakers/compare/HEAD...HEAD

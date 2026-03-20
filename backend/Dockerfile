# open_speakers backend
# Multi-stage build: API-only image by default.
# The worker uses the same image but installs ML deps at runtime via MODEL_INSTALL.

FROM python:3.12-slim AS base

# Non-root user (UID 1000 matches host volume ownership convention)
RUN groupadd -g 1000 appuser && useradd -u 1000 -g 1000 -m appuser

WORKDIR /app

# System deps for psycopg2, soundfile, and ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure audio output dir exists and is writable
RUN mkdir -p /app/audio_output && chown -R appuser:appuser /app/audio_output

USER appuser

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

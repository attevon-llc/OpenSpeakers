"""Integration tests: submit a job to each registered model, poll to completion, check audio.

- ``test_kokoro_end_to_end`` is the fast default test (Kokoro standby, ~1-2s).
- ``test_all_models_end_to_end`` is env-guarded and runs one generation per
  non-kokoro registered model. Each cold-load costs 10–60 s of model download
  + VRAM transfer, so it's opt-in via ``TEST_ALL_MODELS=1``.
"""

from __future__ import annotations

import os
import time

import pytest
from fastapi.testclient import TestClient


def _run_generation_and_assert_audio(
    client: TestClient,
    model_id: str,
    text: str = "Hello from the test suite.",
    timeout_s: int = 300,
) -> None:
    """Submit → poll → verify for a single model. Shared between the Kokoro fast
    test and the full-suite loop."""
    resp = client.post(
        "/api/tts/generate",
        json={"model_id": model_id, "text": text, "speed": 1.0},
    )
    assert resp.status_code in (200, 202), f"{model_id}: submit failed: {resp.text}"
    job_id = resp.json()["job_id"]

    deadline = time.monotonic() + timeout_s
    status = "pending"
    error_message: str | None = None
    while time.monotonic() < deadline:
        time.sleep(1.0)
        jresp = client.get(f"/api/tts/jobs/{job_id}")
        assert jresp.status_code == 200, f"{model_id}: poll failed {jresp.status_code}"
        body = jresp.json()
        status = body["status"]
        error_message = body.get("error_message")
        if status in ("complete", "failed", "cancelled"):
            break

    assert status == "complete", (
        f"{model_id} job {job_id} ended in {status}: {error_message or '(no error msg)'}"
    )

    aresp = client.get(f"/api/tts/jobs/{job_id}/audio")
    assert aresp.status_code == 200, f"{model_id}: audio fetch failed"
    assert aresp.headers["content-type"].startswith("audio/"), (
        f"{model_id}: unexpected content-type {aresp.headers.get('content-type')}"
    )
    assert len(aresp.content) > 1000, f"{model_id}: audio too small to be real"


@pytest.mark.skipif(
    os.environ.get("SKIP_KOKORO_TESTS", "").lower() in ("1", "true", "yes"),
    reason="SKIP_KOKORO_TESTS set",
)
class TestKokoroGeneration:
    def test_end_to_end_generate_and_fetch_audio(self, client: TestClient) -> None:
        _run_generation_and_assert_audio(client, "kokoro", timeout_s=60)


# Full-matrix test — only runs when explicitly opted in. Each model has its own
# VRAM footprint and cold-load cost; the special-case text for dia-1b uses the
# dialogue tag format it requires.
_FULL_MATRIX_ENABLED = os.environ.get("TEST_ALL_MODELS", "").lower() in ("1", "true", "yes")

_MODEL_TEXT: dict[str, str] = {
    "dia-1b": "[S1] Hello from the test suite. [S2] Glad to hear from you.",
}
_MODEL_TIMEOUT: dict[str, int] = {
    "dia-1b": 600,  # dialogue model is slow
    "orpheus-3b": 600,  # vLLM cold-start
    "fish-speech-s2": 600,  # 22 GB model
    "vibevoice-1.5b": 600,
}


def _get_model_ids() -> list[str]:
    """Discover registered models at collection time.

    The ModelManager is a singleton so we only hit it once per session, and we
    skip Kokoro because it's already covered by the fast-path test.
    """
    from app.models.manager import ModelManager

    return [m for m in ModelManager.get_instance().registered_ids if m != "kokoro"]


@pytest.mark.skipif(not _FULL_MATRIX_ENABLED, reason="Set TEST_ALL_MODELS=1 to run")
@pytest.mark.parametrize("model_id", _get_model_ids() if _FULL_MATRIX_ENABLED else [])
def test_model_end_to_end(client: TestClient, model_id: str) -> None:
    text = _MODEL_TEXT.get(model_id, "Hello from the test suite.")
    timeout = _MODEL_TIMEOUT.get(model_id, 300)
    _run_generation_and_assert_audio(client, model_id, text=text, timeout_s=timeout)

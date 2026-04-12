"""Smoke tests for the public API surface.

These don't assert exact model-by-model behaviour — they verify that the app boots,
the registered endpoints return the shapes clients depend on, and that validation
rejects obviously-wrong input. Heavier integration tests (actually generating audio)
live in test_generation.py and are opt-in via an env flag.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealth:
    def test_health_endpoint_returns_200(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("status") in {"ok", "healthy"} or body.get("ok") is True

    def test_openapi_served(self, client: TestClient) -> None:
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        paths = resp.json()["paths"]
        # A few endpoints that must exist for the frontend to work
        assert "/api/models" in paths
        assert "/api/tts/generate" in paths
        assert "/api/tts/jobs" in paths
        assert "/api/voices" in paths


class TestModelsEndpoint:
    def test_list_models_returns_array(self, client: TestClient) -> None:
        resp = client.get("/api/models")
        assert resp.status_code == 200
        models = resp.json()
        assert isinstance(models, list)
        assert len(models) > 0, "expected at least one model registered"

    def test_each_model_has_required_fields(self, client: TestClient) -> None:
        resp = client.get("/api/models")
        required = {
            "id",
            "name",
            "description",
            "supports_voice_cloning",
            "supports_streaming",
            "supports_speed",
            "supports_pitch",
            "supported_languages",
            "vram_gb_estimate",
            "status",
        }
        for m in resp.json():
            missing = required - set(m.keys())
            assert not missing, f"model {m.get('id')} missing fields: {missing}"

    def test_kokoro_is_registered(self, client: TestClient) -> None:
        """Kokoro is the standby/default model — the app is broken if it's gone."""
        resp = client.get("/api/models")
        ids = [m["id"] for m in resp.json()]
        assert "kokoro" in ids

    def test_get_single_model(self, client: TestClient) -> None:
        resp = client.get("/api/models/kokoro")
        assert resp.status_code == 200
        m = resp.json()
        assert m["id"] == "kokoro"

    def test_get_unknown_model_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/models/does-not-exist")
        assert resp.status_code == 404


class TestVoicesEndpoint:
    def test_list_voices_returns_voices_shape(self, client: TestClient) -> None:
        resp = client.get("/api/voices")
        assert resp.status_code == 200
        body = resp.json()
        assert "voices" in body
        assert isinstance(body["voices"], list)

    def test_list_builtin_kokoro_voices(self, client: TestClient) -> None:
        resp = client.get("/api/voices/builtin/kokoro")
        assert resp.status_code == 200
        voices = resp.json()
        assert isinstance(voices, list)
        # Kokoro ships with dozens of built-in voices; be defensive but non-zero.
        assert len(voices) > 0


class TestJobsEndpoint:
    def test_list_jobs_returns_pagination_shape(self, client: TestClient) -> None:
        resp = client.get("/api/tts/jobs")
        assert resp.status_code == 200
        body = resp.json()
        for key in ("jobs", "total", "page", "page_size"):
            assert key in body

    def test_list_jobs_honours_page_size(self, client: TestClient) -> None:
        resp = client.get("/api/tts/jobs", params={"page": 1, "page_size": 5})
        assert resp.status_code == 200
        assert resp.json()["page_size"] == 5

    def test_get_unknown_job_returns_404(self, client: TestClient) -> None:
        # A valid-looking UUID that has no matching row
        resp = client.get("/api/tts/jobs/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestGenerateValidation:
    def test_generate_rejects_unknown_model(self, client: TestClient) -> None:
        resp = client.post(
            "/api/tts/generate",
            json={"model_id": "no-such-model", "text": "hello"},
        )
        assert resp.status_code in (400, 404, 422)

    def test_generate_rejects_empty_text(self, client: TestClient) -> None:
        resp = client.post(
            "/api/tts/generate",
            json={"model_id": "kokoro", "text": ""},
        )
        assert resp.status_code == 422

    def test_generate_rejects_oversize_text(self, client: TestClient) -> None:
        resp = client.post(
            "/api/tts/generate",
            json={"model_id": "kokoro", "text": "x" * 5000},
        )
        assert resp.status_code == 422

    def test_generate_rejects_out_of_range_speed(self, client: TestClient) -> None:
        resp = client.post(
            "/api/tts/generate",
            json={"model_id": "kokoro", "text": "hi", "speed": 9.9},
        )
        assert resp.status_code == 422


class TestBatchValidation:
    def test_batch_rejects_empty_lines(self, client: TestClient) -> None:
        resp = client.post("/api/tts/batch", json={"model_id": "kokoro", "lines": []})
        assert resp.status_code == 422

    def test_batch_rejects_too_many_lines(self, client: TestClient) -> None:
        resp = client.post(
            "/api/tts/batch",
            json={"model_id": "kokoro", "lines": ["x"] * 101},
        )
        assert resp.status_code == 422

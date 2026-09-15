"""End-to-end test of the /history endpoint with an Authorization header.

Proves the full recently-played path: FastAPI route -> HistoryAgent ->
Spotify API (mocked) -> normalized list returned to the client.
"""
import json

import pytest
from fastapi.testclient import TestClient


def _payload():
    items = [{
        "track": {
            "id": "abc123",
            "name": "Fix You",
            "artists": [{"name": "Coldplay"}],
            "album": {"name": "X&Y", "images": [{"url": "https://img.example/1.jpg"}]},
            "external_urls": {"spotify": "https://open.spotify.com/track/abcabcabcabcabcabcabc1"},
        },
        "played_at": "2026-09-04T12:00:00Z",
    }, {
        "track": {
            "id": "def456",
            "name": "Yellow",
            "artists": [{"name": "Coldplay"}],
            "album": {"name": "Parachutes", "images": []},
            "external_urls": {"spotify": "https://open.spotify.com/track/defdefdefdefdefdefdef2"},
        },
        "played_at": "2026-09-04T11:00:00Z",
    }]
    return json.dumps({"items": items}).encode()


class MockResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return _payload()


def test_history_with_bearer_returns_normalized_listening_history(monkeypatch):
    def fake_urlopen(req, *args, **kwargs):
        assert "me/player/recently-played" in req.full_url
        return MockResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    from backend.main import app

    client = TestClient(app)
    resp = client.get("/history", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    first = data[0]
    assert first["name"] == "Fix You"
    assert first["artist"] == "Coldplay"
    assert first["album"] == "X&Y"
    assert first["timestamp"] == "2026-09-04T12:00:00Z"
    assert first["image"] == "https://img.example/1.jpg"
    assert "spotify.com/track" in first["spotifyUrl"]
    # Empty image falls back gracefully.
    assert data[1]["image"] == ""
"""Tests for mood-based recommendations and the public music endpoints."""
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.agents.spotify_agent import SpotifyDataAgent
from backend.main import app
from backend.sample_data import SONG_LIBRARY

MOOD_FEATURES = {
    "calm": {"energy": 0.3, "valence": 0.55, "danceability": 0.4, "acousticness": 0.7},
    "energetic": {"energy": 0.9, "valence": 0.7, "danceability": 0.8, "acousticness": 0.05},
    "happy": {"energy": 0.72, "valence": 0.85, "danceability": 0.75, "acousticness": 0.15},
    "sad": {"energy": 0.3, "valence": 0.3, "danceability": 0.35, "acousticness": 0.55},
    "aggressive": {"energy": 0.9, "valence": 0.4, "danceability": 0.55, "acousticness": 0.05},
    "romantic": {"energy": 0.45, "valence": 0.65, "danceability": 0.5, "acousticness": 0.4},
    "neutral": {"energy": 0.5, "valence": 0.5, "danceability": 0.5, "acousticness": 0.35},
}


@pytest.fixture
def agent():
    return SpotifyDataAgent()


@pytest.fixture
def client():
    return TestClient(app)


def test_song_library_is_big_and_mood_varied():
    """The library must be large enough (and cover enough moods) that
    different moods can produce genuinely different recommendation sets."""
    assert len(SONG_LIBRARY) >= 20
    moods = {t["mood"] for t in SONG_LIBRARY}
    assert len(moods) >= 7


def test_recommendations_return_limit_distinct_tracks(agent):
    recs = agent.get_recommendations("calm", MOOD_FEATURES["calm"], limit=5)
    assert len(recs) == 5
    assert len({r["id"] for r in recs}) == 5


def test_recommendations_prioritize_matching_mood(agent):
    for mood in ("calm", "energetic", "happy", "sad", "aggressive"):
        recs = agent.get_recommendations(mood, MOOD_FEATURES[mood], limit=5)
        matches = sum(1 for r in recs if r["mood"] == mood)
        assert matches >= 3, f"expected >=3 '{mood}' tracks in top 5, got {matches}"


def test_recommendations_vary_by_mood(agent):
    """Regression: different moods must produce different recommendation sets."""
    sets = {}
    for mood, features in MOOD_FEATURES.items():
        recs = agent.get_recommendations(mood, features, limit=5)
        sets[mood] = tuple(sorted(r["id"] for r in recs))

    moods = sorted(sets)
    for i, mood_a in enumerate(moods):
        for mood_b in moods[i + 1:]:
            assert sets[mood_a] != sets[mood_b], (
                f"'{mood_a}' and '{mood_b}' produced identical recommendations"
            )


def test_listening_history_boosts_artist(agent):
    features = MOOD_FEATURES["neutral"]
    listening = [
        {"name": "Fix You", "artist": "Coldplay"},
        {"name": "Yellow", "artist": "Coldplay"},
    ]
    base = agent.get_recommendations("neutral", features, limit=10)
    boosted = agent.get_recommendations("neutral", features, limit=10, listening_history=listening)

    def first_coldplay_position(recs):
        for i, r in enumerate(recs):
            if "coldplay" in r["artist"].lower():
                return i
        return len(recs)

    assert first_coldplay_position(boosted) <= first_coldplay_position(base)


def test_every_library_track_has_a_spotify_url():
    """The player only renders a Spotify embed for real open.spotify.com URLs,
    so every library track needs one."""
    for track in SONG_LIBRARY:
        url = track.get("spotifyUrl", "")
        assert url.startswith("https://open.spotify.com/track/"), f"{track['name']} missing spotifyUrl"
        assert len(url.rsplit("/", 1)[-1]) == 22


def test_recommendations_endpoint_public(client):
    response = client.post(
        "/recommendations",
        json={"mood": "calm", "audioFeatures": MOOD_FEATURES["calm"]},
    )
    assert response.status_code == 200
    assert len(response.json()["recommendations"]) == 5


def test_history_endpoint_public(client, monkeypatch):
    monkeypatch.setattr(
        "backend.main.history_agent.get_listening_history",
        lambda **kwargs: [],
    )
    response = client.get("/history")
    assert response.status_code == 200
def test_search_recommendations_uses_seeds_and_targets(monkeypatch):
    """Live recommendations call the Spotify API seeded with recently-played tracks
    and targeted to the mood's audio profile."""

    class MockResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            if 'recommendations' in self.url:
                return json.dumps({
                    'tracks': [{
                        'id': 'rec1', 'name': 'Rec One', 'artists': [{'name': 'Artist A'}],
                        'album': {'name': 'Album A', 'images': [{'url': 'https://img.example/1.jpg'}]},
                        'duration_ms': 200000,
                        'external_urls': {'spotify': 'https://open.spotify.com/track/rec1'},
                    }]
                }).encode()
            return json.dumps({
                'audio_features': [{'id': 'rec1', 'energy': 0.7, 'valence': 0.8, 'danceability': 0.6, 'acousticness': 0.1}]
            }).encode()

    requests_seen = []

    def fake_urlopen(req, *args, **kwargs):
        requests_seen.append(req.full_url)

        mock = MockResponse()
        mock.url = req.full_url
        return mock

    monkeypatch.setattr('urllib.request.urlopen', fake_urlopen)

    listening = [
        {'id': 'seed1', 'name': 'Seed One', 'artist': 'Artist A'},
        {'id': 'seed2', 'name': 'Seed Two', 'artist': 'Artist B'},
    ]
    recs = SpotifyDataAgent().search_recommendations(
        'test-token', 'happy', MOOD_FEATURES['happy'], listening_history=listening
    )

    assert len(recs) == 1
    assert recs[0]['id'] == 'rec1'
    assert recs[0]['artist'] == 'Artist A'
    assert recs[0]['mood'] == 'happy'
    assert 'seed_tracks=seed1%2Cseed2' in requests_seen[0]
    assert 'target_valence=0.85' in requests_seen[0]
from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_spotify_player_auth_url():
    response = client.get('/spotify/auth-url')
    assert response.status_code == 200
    assert response.json()['url'].startswith('https://accounts.spotify.com/authorize?')

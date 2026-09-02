import os
from urllib.parse import parse_qs, urlparse

from backend.main import build_spotify_auth_url


def test_build_spotify_auth_url_uses_env_values():
    url = build_spotify_auth_url()
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert 'accounts.spotify.com' in parsed.netloc
    assert query['client_id'][0] == os.getenv('SPOTIFY_CLIENT_ID')
    assert query['redirect_uri'][0] == os.getenv('SPOTIFY_REDIRECT_URI')
    assert query['response_type'][0] == 'code'

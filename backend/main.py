import os
import json
import secrets
import base64
import logging
from datetime import datetime
from pathlib import Path
from urllib import parse, request
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from backend.agents.orchestrator_agent import OrchestratorAgent
from backend.agents.spotify_agent import SpotifyDataAgent
from backend.agents.history_agent import HistoryAgent
from backend.agents.notification_agent import NotificationAgent
from backend.sample_data import SAMPLE_TRACK, MOOD_HISTORY

# Load environment variables from the backend folder and project root
for env_path in (
    Path(__file__).resolve().parent / '.env',
    Path(__file__).resolve().parents[1] / '.env',
):
    if env_path.exists():
        load_dotenv(env_path)

FRONTEND_REDIRECT_URI = os.getenv('FRONTEND_REDIRECT_URI', 'http://localhost:3000')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:8000/callback')
SOUNDCLOUD_CLIENT_ID = os.getenv('SOUNDCLOUD_CLIENT_ID')
SOUNDCLOUD_CLIENT_SECRET = os.getenv('SOUNDCLOUD_CLIENT_SECRET')
SOUNDCLOUD_REDIRECT_URI = os.getenv('SOUNDCLOUD_REDIRECT_URI', 'http://localhost:3000')
AUTH_TOKEN = secrets.token_urlsafe(32)
APP_USER = {
    'id': 'harmony-user',
    'name': 'Harmony User',
    'email': '',
    'demo': False,
}
logger = logging.getLogger(__name__)


def _validate_redirect_uri(uri: Optional[str], name: str) -> None:
    """Warn loudly if a redirect URI won't match Spotify's exact-match rules."""
    if not uri:
        print(f"[harmony] WARNING: {name} is not set. OAuth login will fail until it is configured.")
        return
    if uri.endswith('/'):
        print(
            f"[harmony] WARNING: {name}={uri} ends with '/'. "
            f"Spotify matches redirect URIs exactly - remove the trailing slash in your .env."
        )
    if name == 'SPOTIFY_REDIRECT_URI':
        from urllib.parse import urlparse

        parsed = urlparse(uri)
        if parsed.port != 8000 or parsed.path != '/callback':
            print(
                f"[harmony] WARNING: {name}={uri} does not look like the backend OAuth callback "
                f"(expected e.g. http://localhost:8000/callback). Make sure this exact value is "
                f"registered under your app in the Spotify Developer Dashboard "
                f"(https://developer.spotify.com/dashboard)."
            )
    print(f"[harmony] {name} = {uri}")


_validate_redirect_uri(SPOTIFY_REDIRECT_URI, 'SPOTIFY_REDIRECT_URI')
_validate_redirect_uri(FRONTEND_REDIRECT_URI, 'FRONTEND_REDIRECT_URI')


def build_spotify_auth_url() -> str:
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': 'user-read-currently-playing user-read-playback-state user-read-recently-played user-read-private user-top-read',
        'show_dialog': 'true',
    }
    return 'https://accounts.spotify.com/authorize?' + parse.urlencode(params)


def exchange_code_for_token(code: str) -> Dict:
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise ValueError('Spotify OAuth credentials are not configured.')

    auth_header = base64.b64encode(f'{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}'.encode()).decode()
    payload = parse.urlencode({
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': SPOTIFY_REDIRECT_URI,
    }).encode()
    req = request.Request(
        'https://accounts.spotify.com/api/token',
        data=payload,
        headers={'Authorization': f'Basic {auth_header}', 'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    with request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def spotify_refresh_access_token(refresh_token: str) -> Dict:
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise ValueError('Spotify OAuth credentials are not configured.')

    auth_header = base64.b64encode(f'{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}'.encode()).decode()
    payload = parse.urlencode({
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }).encode()
    req = request.Request(
        'https://accounts.spotify.com/api/token',
        data=payload,
        headers={'Authorization': f'Basic {auth_header}', 'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    with request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def spotify_get_current_track(access_token: str) -> Dict:
    req = request.Request(
        'https://api.spotify.com/v1/me/player/currently-playing',
        headers={'Authorization': f'Bearer {access_token}'},
    )
    with request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    item = data.get('item') if data else None
    if not item:
        return {'id': None, 'name': 'Nothing playing', 'artist': '', 'album': '', 'duration': 0, 'progress': 0, 'isPlaying': False}
    images = item.get('album', {}).get('images', [])
    return {
        'id': item.get('id'),
        'name': item.get('name', 'Unknown track'),
        'artist': ', '.join(artist['name'] for artist in item.get('artists', [])),
        'album': item.get('album', {}).get('name', 'Unknown album'),
        'image': images[0]['url'] if images else '',
        'duration': int(item.get('duration_ms', 0) / 1000),
        'progress': int(data.get('progress_ms', 0) / 1000),
        'isPlaying': bool(data.get('is_playing')),
        'spotifyUrl': item.get('external_urls', {}).get('spotify', ''),
    }


def spotify_get_user_profile(access_token: str) -> Dict:
    """The authenticated user's Spotify profile."""
    req = request.Request(
        'https://api.spotify.com/v1/me',
        headers={'Authorization': f'Bearer {access_token}'},
    )
    with request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    return {
        'id': data.get('id', 'harmony-user'),
        'name': data.get('display_name') or data.get('id') or 'Harmony User',
        'email': data.get('email', ''),
        'demo': False,
    }


def soundcloud_get_current_track() -> Dict:
    return {
        'id': 'soundcloud-demo-track',
        'name': 'Midnight City',
        'artist': 'M83',
        'album': 'Hurry Up, We’re Dreaming',
        'image': 'https://i1.sndcdn.com/artworks-000075910274-k2u0ft-t500x500.jpg',
        'duration': 242,
        'progress': 42,
        'isPlaying': True,
        'audio_features': {},
        'soundcloudUrl': 'https://soundcloud.com/m83/midnight-city',
    }


# Initialize AWS services if enabled
if os.getenv('USE_AWS_REKOGNITION', 'false').lower() == 'true':
    import boto3
    # AWS clients will be initialized by the agents

app = FastAPI(title="Harmony API")
agent = OrchestratorAgent()
spotify_agent = SpotifyDataAgent()
history_agent = HistoryAgent()
notification_agent = NotificationAgent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuthResponse(BaseModel):
    token: str
    user: Dict


class MoodDetectionRequest(BaseModel):
    imageData: str


class RecommendationRequest(BaseModel):
    mood: str
    audioFeatures: Dict[str, float]


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class PreferencesRequest(BaseModel):
    preferences: Dict[str, object] = Field(default_factory=dict)


@app.get("/health")
def health_check():
    status = get_aws_status()
    ready = all(not service['enabled'] or service['client_initialized'] for service in status.values())
    return {"status": "ok" if ready else "degraded", "ready": ready, "aws": status}


def _raise_service_unavailable(service: str, exc: Exception) -> None:
    # Mistral is an external API (api.mistral.ai), not an AWS service, so an
    # "AWS region" message is misleading for it (same for Spotify).
    if service in ('Mistral', 'Spotify'):
        endpoint = 'api.mistral.ai' if service == 'Mistral' else 'Spotify Web API'
        detail = (
            f"{service} ({endpoint}) is unavailable. "
            "Check service access and network connectivity."
        )
    else:
        region = os.getenv('AWS_REGION', 'us-east-1')
        detail = f"{service} is unavailable in AWS region {region}. Check service access and network connectivity."
    raise HTTPException(
        status_code=503,
        detail=detail,
    ) from exc


def _mood_service_name(exc: Exception) -> str:
    message = str(exc).lower()
    if 'dynamodb' in message:
        return 'DynamoDB'
    if 'rekognition' in message:
        return 'Rekognition'
    if 'mistral' in message:
        return 'Mistral'
    if 'spotify' in message:
        return 'Spotify'
    return 'AWS mood analysis services'


@app.post("/auth", response_model=AuthResponse)
def authenticate():
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail='Spotify credentials are not configured')
    return {"token": AUTH_TOKEN, "user": APP_USER}


@app.get("/spotify/auth-url")
def spotify_auth_url():
    return {"url": build_spotify_auth_url()}


@app.get("/callback")
def spotify_callback(code: Optional[str] = None, error: Optional[str] = None):
    if error:
        raise HTTPException(status_code=400, detail=error)
    if not code:
        raise HTTPException(status_code=400, detail='Missing Spotify authorization code.')
    try:
        token_data = exchange_code_for_token(code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    access_token = token_data.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail='Spotify token exchange failed.')
    refresh_token = token_data.get('refresh_token') or ''
    expires_in = token_data.get('expires_in') or 3600
    params = parse.urlencode({
        'spotify_token': access_token,
        'spotify_refresh_token': refresh_token,
        'spotify_expires_in': expires_in,
    })
    return RedirectResponse(f"{FRONTEND_REDIRECT_URI}/?{params}")


@app.post("/spotify/refresh")
def spotify_refresh(request: TokenRefreshRequest):
    if not request.refresh_token:
        raise HTTPException(status_code=400, detail='Missing refresh token')
    try:
        token_data = spotify_refresh_access_token(request.refresh_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f'Spotify token refresh failed: {exc}')
    access_token = token_data.get('access_token')
    if not access_token:
        raise HTTPException(status_code=401, detail='Spotify token refresh failed.')
    return {
        'access_token': access_token,
        'expires_in': token_data.get('expires_in', 3600),
    }


@app.get("/me")
def me(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.replace('Bearer ', '').strip()
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        return spotify_get_user_profile(token)
    except Exception:
        return APP_USER


@app.get("/current-track")
def current_track(authorization: Optional[str] = Header(None)):
    if not authorization:
        return {"authenticated": False, "message": "Spotify is not connected."}

    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return {"authenticated": False, "message": "Spotify credentials are not configured."}

    token = authorization.replace('Bearer ', '').strip()
    if not token:
        return {"authenticated": False, "message": "Spotify is not connected."}

    try:
        return {"authenticated": True, **spotify_get_current_track(token)}
    except Exception:
        return {"authenticated": False, "message": "Spotify authorization has expired."}

@app.post("/detect-mood")
def detect_mood(request: MoodDetectionRequest, authorization: Optional[str] = Header(None)):
    # Mood detection is self-contained (facial analysis + local song library)
    # and deliberately does NOT require Spotify authorization, so recommendations
    # always work even when the user hasn't connected Spotify yet. When an
    # access token is present, the user's Spotify listening history is used to
    # enrich the ranking.
    spotify_token = authorization.replace('Bearer ', '').strip() if authorization else None
    try:
        result = agent.process_session(APP_USER["id"], request.imageData, access_token=spotify_token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Mood detection request failed: %s", exc)
        _raise_service_unavailable(_mood_service_name(exc), exc)

    return result


@app.post("/recommendations")
def recommendations(request: RecommendationRequest, authorization: Optional[str] = Header(None)):
    # When logged in, recommendations come live from the Spotify API seeded with
    # the user's recently-played tracks and targeted to the detected mood.
    # When logged out, they come from the local song library.
    token = authorization.replace('Bearer ', '').strip() if authorization else None
    if token:
        recommendation_agent = agent.recommender_agent
        recs = recommendation_agent.spotify_agent.search_recommendations(
            token,
            request.mood,
            request.audioFeatures,
            limit=5,
        )
    else:
        recs = spotify_agent.get_recommendations(request.mood, request.audioFeatures, limit=5)
    return {"recommendations": recs}


@app.get("/history")
def get_history(authorization: Optional[str] = Header(None)):
    """Mood history, plus the connected user's Spotify listening history.

    When a Spotify access token is provided, recent listening history populates
    the History page; otherwise it falls back to the stored mood history.
    """
    token = authorization.replace('Bearer ', '').strip() if authorization else None
    try:
        if token:
            return history_agent.get_listening_history(access_token=token, limit=10)
        return history_agent.get_history(APP_USER["id"])
    except Exception as exc:
        _raise_service_unavailable('History service', exc)


@app.post("/notify")
def notify(message: Dict[str, str], authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    notification = notification_agent.notify(APP_USER["id"], message.get("message", ""))
    return notification

@app.get("/history/stats")
def get_history_stats(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        return history_agent.get_statistics(APP_USER["id"])
    except Exception as exc:
        _raise_service_unavailable('DynamoDB', exc)

@app.get("/history/trends")
def get_history_trends(time_range: str = "week", authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        return history_agent.get_mood_trends(APP_USER["id"], time_range)
    except Exception as exc:
        _raise_service_unavailable('DynamoDB', exc)

@app.get("/preferences")
def get_preferences():
    try:
        return history_agent.get_user_preferences(APP_USER["id"])
    except Exception as exc:
        _raise_service_unavailable('DynamoDB', exc)


@app.put("/preferences")
def put_preferences(request: PreferencesRequest):
    try:
        return history_agent.save_user_preferences(APP_USER["id"], request.preferences)
    except Exception as exc:
        _raise_service_unavailable('DynamoDB', exc)


@app.get("/aws/status")
def get_aws_status():
    """Check AWS services status"""
    return {
        "rekognition": {
            "enabled": os.getenv('USE_AWS_REKOGNITION', 'false').lower() == 'true',
            "client_initialized": bool(getattr(agent.facial_agent, 'rekognition', None)),
        },
        "dynamodb": {
            "enabled": os.getenv('USE_AWS_DYNAMODB', 'false').lower() == 'true',
            "client_initialized": bool(getattr(history_agent, 'dynamodb', None)),
        },
        "mistral": {
            "enabled": bool(os.getenv('MISTRAL_API_KEY')),
            "client_initialized": bool(getattr(agent.recommender_agent.mistral_agent, 'client', None)),
        },
    }

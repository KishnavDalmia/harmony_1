import os
import json
import base64
import secrets
from datetime import datetime
from pathlib import Path
from urllib import parse, request
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from typing import Optional, Dict, List
from pydantic import BaseModel
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

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:8000/callback')
FRONTEND_REDIRECT_URI = os.getenv('FRONTEND_REDIRECT_URI', 'http://localhost:3000')
SOUNDCLOUD_CLIENT_ID = os.getenv('SOUNDCLOUD_CLIENT_ID')
SOUNDCLOUD_CLIENT_SECRET = os.getenv('SOUNDCLOUD_CLIENT_SECRET')
SOUNDCLOUD_REDIRECT_URI = os.getenv('SOUNDCLOUD_REDIRECT_URI', 'http://localhost:3000')
LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_USERNAME = os.getenv('LASTFM_USERNAME')
LASTFM_API_URL = os.getenv('LASTFM_API_URL', 'https://ws.audioscrobbler.com/2.0/')
AUTH_TOKEN = secrets.token_urlsafe(32)
APP_USER = {
    'id': LASTFM_USERNAME or 'harmony-user',
    'name': LASTFM_USERNAME or 'Harmony User',
    'email': '',
    'demo': False,
}


def build_spotify_auth_url() -> str:
    scopes = ' '.join([
        'user-read-email',
        'user-read-playback-state',
        'user-modify-playback-state',
        'user-read-currently-playing',
        'playlist-read-private',
        'playlist-read-collaborative',
    ])
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': scopes,
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
        headers={
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
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

    if not data or 'item' not in data:
        return SAMPLE_TRACK

    item = data['item']
    image = item.get('album', {}).get('images', [{}])[0].get('url') if item.get('album', {}).get('images') else SAMPLE_TRACK['image']
    artist = ', '.join([artist['name'] for artist in item.get('artists', [])]) if item.get('artists') else SAMPLE_TRACK['artist']

    return {
        'id': item.get('id', SAMPLE_TRACK['id']),
        'name': item.get('name', SAMPLE_TRACK['name']),
        'artist': artist,
        'album': item.get('album', {}).get('name', SAMPLE_TRACK['album']),
        'image': image,
        'duration': int(item.get('duration_ms', SAMPLE_TRACK['duration'] * 1000) / 1000),
        'progress': int(data.get('progress_ms', SAMPLE_TRACK['progress'] * 1000) / 1000),
        'isPlaying': bool(data.get('is_playing', True)),
        'audio_features': {},
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


def lastfm_get_recent_tracks(limit: int = 10) -> List[Dict]:
    if not LASTFM_API_KEY or not LASTFM_USERNAME:
        return []

    params = {
        'method': 'user.getrecenttracks',
        'user': LASTFM_USERNAME,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': str(limit),
    }
    request_url = LASTFM_API_URL + '?' + parse.urlencode(params)

    try:
        with request.urlopen(request_url) as resp:
            payload = json.loads(resp.read().decode())
    except Exception:
        return []

    tracks = payload.get('recenttracks', {}).get('track', [])
    if isinstance(tracks, dict):
        tracks = [tracks]

    recent = []
    for track in tracks[:limit]:
        artist = track.get('artist', {}).get('@text') or (track.get('artist') or {}).get('text') or 'Unknown artist'
        name = track.get('name') or 'Unknown track'
        image = None
        for image_data in track.get('image', []):
            if image_data.get('#text'):
                image = image_data.get('#text')
        if isinstance(track.get('date'), dict):
            played_at = track['date'].get('#text')
        else:
            played_at = datetime.utcnow().isoformat() + 'Z'

        recent.append({
            'id': f"{artist}-{name}-{played_at}",
            'name': name,
            'artist': artist,
            'album': track.get('album', {}).get('#text') or 'Recent track',
            'image': image or 'https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=400&q=80',
            'timestamp': played_at,
            'matchScore': 1.0,
            'soundcloudUrl': track.get('url'),
        })

    return recent


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


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/auth", response_model=AuthResponse)
def authenticate():
    return {"token": AUTH_TOKEN, "user": APP_USER}


@app.get("/spotify/auth-url")
def spotify_auth_url():
    return {"url": build_spotify_auth_url()}


@app.get("/spotify/login")
def spotify_login():
    return RedirectResponse(build_spotify_auth_url())


@app.get("/callback")
def spotify_callback(code: Optional[str] = None, error: Optional[str] = None):
    if error:
        raise HTTPException(status_code=400, detail=error)
    if not code:
        raise HTTPException(status_code=400, detail='Missing Spotify authorization code.')

    token_data = exchange_code_for_token(code)
    access_token = token_data.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail='Spotify token exchange failed.')

    frontend_url = f"{FRONTEND_REDIRECT_URI}/?spotify_token={parse.quote(access_token)}"
    return RedirectResponse(frontend_url)


@app.get("/me")
def me(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.replace('Bearer ', '').strip()
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return APP_USER


@app.get("/current-track")
def current_track(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.replace('Bearer ', '').strip()
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not SOUNDCLOUD_CLIENT_ID:
        return soundcloud_get_current_track()

    try:
        return soundcloud_get_current_track()
    except Exception as exc:
        return soundcloud_get_current_track()


@app.post("/detect-mood")
def detect_mood(request: MoodDetectionRequest, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        result = agent.process_session(APP_USER["id"], request.imageData)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return result


@app.post("/recommendations")
def recommendations(request: RecommendationRequest, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    recs = spotify_agent.get_recommendations(request.mood, request.audioFeatures, limit=5)
    return {"recommendations": recs}


@app.get("/history")
def get_history(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if LASTFM_API_KEY and LASTFM_USERNAME:
        return lastfm_get_recent_tracks(limit=10)

    return history_agent.get_history(APP_USER["id"])


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
    return history_agent.get_statistics(APP_USER["id"])

@app.get("/history/trends")
def get_history_trends(time_range: str = "week", authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return history_agent.get_mood_trends(APP_USER["id"], time_range)

@app.get("/aws/status")
def get_aws_status():
    """Check AWS services status"""
    return {
        "rekognition_enabled": os.getenv('USE_AWS_REKOGNITION', 'false').lower() == 'true',
        "dynamodb_enabled": os.getenv('USE_AWS_DYNAMODB', 'false').lower() == 'true',
        "bedrock_enabled": os.getenv('USE_AWS_BEDROCK', 'false').lower() == 'true'
    }

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
from pydantic import BaseModel
from backend.agents.orchestrator_agent import OrchestratorAgent
from backend.agents.spotify_agent import SpotifyDataAgent
from backend.agents.history_agent import HistoryAgent
from backend.agents.notification_agent import NotificationAgent
from backend.sample_data import DEMO_TOKEN, DEMO_USER, SAMPLE_TRACK, MOOD_HISTORY

# Load environment variables
load_dotenv()

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
    return {"token": DEMO_TOKEN, "user": DEMO_USER}


@app.get("/me")
def me(authorization: Optional[str] = Header(None)):
    if not authorization or authorization != f"Bearer {DEMO_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return DEMO_USER


@app.get("/current-track")
def current_track(authorization: Optional[str] = Header(None)):
    if not authorization or authorization != f"Bearer {DEMO_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return SAMPLE_TRACK


@app.post("/detect-mood")
def detect_mood(request: MoodDetectionRequest, authorization: Optional[str] = Header(None)):
    if not authorization or authorization != f"Bearer {DEMO_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        result = agent.process_session(DEMO_USER["id"], request.imageData)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return result


@app.post("/recommendations")
def recommendations(request: RecommendationRequest, authorization: Optional[str] = Header(None)):
    if not authorization or authorization != f"Bearer {DEMO_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    recs = spotify_agent.get_recommendations(request.mood, request.audioFeatures, limit=5)
    return {"recommendations": recs}


@app.get("/history")
def get_history(authorization: Optional[str] = Header(None)):
    if not authorization or authorization != f"Bearer {DEMO_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return history_agent.get_history(DEMO_USER["id"])


@app.post("/notify")
def notify(message: Dict[str, str], authorization: Optional[str] = Header(None)):
    if not authorization or authorization != f"Bearer {DEMO_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    notification = notification_agent.notify(DEMO_USER["id"], message.get("message", ""))
    return notification

@app.get("/history/stats")
def get_history_stats(authorization: Optional[str] = Header(None)):
    if not authorization or authorization != f"Bearer {DEMO_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return history_agent.get_statistics(DEMO_USER["id"])

@app.get("/history/trends")
def get_history_trends(time_range: str = "week", authorization: Optional[str] = Header(None)):
    if not authorization or authorization != f"Bearer {DEMO_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return history_agent.get_mood_trends(DEMO_USER["id"], time_range)

@app.get("/aws/status")
def get_aws_status():
    """Check AWS services status"""
    return {
        "rekognition_enabled": os.getenv('USE_AWS_REKOGNITION', 'false').lower() == 'true',
        "dynamodb_enabled": os.getenv('USE_AWS_DYNAMODB', 'false').lower() == 'true',
        "bedrock_enabled": os.getenv('USE_AWS_BEDROCK', 'false').lower() == 'true'
    }

from pydantic import BaseModel
from typing import Dict, Optional


class Track(BaseModel):
    id: int
    name: str
    artist: str
    album: str
    image: str
    duration: int
    progress: int
    isPlaying: bool
    audio_features: Dict[str, float]


class Recommendation(Track):
    mood: str
    matchScore: float

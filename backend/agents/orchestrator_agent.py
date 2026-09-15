import logging
from typing import Dict
from .spotify_agent import SpotifyDataAgent
from .facial_agent import FacialEmotionAgent
from .mood_agent import MoodAnalyzerAgent
from .recommender_agent import RecommenderAgent
from .history_agent import HistoryAgent
from .notification_agent import NotificationAgent
from backend.sample_data import DEMO_USER, DEMO_TOKEN, MOOD_HISTORY

logger = logging.getLogger(__name__)

# Canonical audio-feature profile per detected mood. Used to drive the
# recommender's similarity term so that different moods genuinely pull
# different songs (rather than raw facial-emotion scores, which are only
# loosely correlated with audio traits).
MOOD_AUDIO_PROFILES = {
    "happy": {"energy": 0.72, "valence": 0.85, "danceability": 0.75, "acousticness": 0.15},
    "sad": {"energy": 0.3, "valence": 0.3, "danceability": 0.35, "acousticness": 0.55},
    "energetic": {"energy": 0.9, "valence": 0.7, "danceability": 0.8, "acousticness": 0.05},
    "calm": {"energy": 0.3, "valence": 0.55, "danceability": 0.4, "acousticness": 0.7},
    "romantic": {"energy": 0.45, "valence": 0.65, "danceability": 0.5, "acousticness": 0.4},
    "dreamy": {"energy": 0.5, "valence": 0.55, "danceability": 0.45, "acousticness": 0.55},
    "aggressive": {"energy": 0.9, "valence": 0.4, "danceability": 0.55, "acousticness": 0.05},
    "neutral": {"energy": 0.5, "valence": 0.5, "danceability": 0.5, "acousticness": 0.35},
}


class OrchestratorAgent:
    def __init__(self):
        self.spotify_agent = SpotifyDataAgent()
        self.facial_agent = FacialEmotionAgent()
        self.mood_agent = MoodAnalyzerAgent()
        self.recommender_agent = RecommenderAgent()
        self.history_agent = HistoryAgent()
        self.notification_agent = NotificationAgent()

    def get_demo_user(self) -> Dict:
        return DEMO_USER

    def authenticate_request(self, token: str) -> Dict:
        if token == DEMO_TOKEN:
            return DEMO_USER
        raise ValueError("Invalid token")

    def detect_mood(self, user_id: str, image_data: str) -> Dict:
        facial_result = self.facial_agent.detect_mood(image_data)
        return self.mood_agent.analyze(
            audio_features={
                "energy": facial_result["emotions"].get("energetic", 0.5),
                "valence": facial_result["emotions"].get("happy", 0.5),
                "danceability": facial_result["emotions"].get("surprised", 0.5),
                "acousticness": facial_result["emotions"].get("calm", 0.5),
            },
            emotions=facial_result["emotions"],
        )

    def _recommendation_features(self, mood: str, emotion_features: Dict) -> Dict:
        """Blend the detected mood's canonical audio profile with facial-emotion
        signals so the recommender's similarity term is genuinely mood-driven."""
        profile = MOOD_AUDIO_PROFILES.get(mood, MOOD_AUDIO_PROFILES["neutral"])
        blended = {}
        for key in ("energy", "valence", "danceability", "acousticness"):
            emotion_value = emotion_features.get(key)
            if emotion_value is None:
                blended[key] = profile[key]
            else:
                blended[key] = round(0.7 * profile[key] + 0.3 * float(emotion_value), 2)
        return blended

    def process_session(self, user_id: str, image_data: str, access_token: str | None = None) -> Dict:
        from datetime import datetime

        try:
            user_history = self.history_agent.get_history(user_id, limit=1000)
        except Exception as exc:
            raise RuntimeError(f"DynamoDB history read failed: {exc}") from exc

        try:
            mood_data = self.detect_mood(user_id, image_data)
        except ValueError:
            # User-input problems (e.g. "No faces detected in the image") must
            # keep their type so main.py maps them to HTTP 400, not a bogus 503
            # that blames the AWS service.
            raise
        except Exception as exc:
            raise RuntimeError(f"Rekognition mood analysis failed: {exc}") from exc

        try:
            listening_history = self.history_agent.get_listening_history(access_token=access_token, limit=25)
        except Exception as exc:
            logger.warning("Spotify listening history unavailable: %s", exc)
            listening_history = []
        recommendation_features = self._recommendation_features(
            mood_data["mood"],
            mood_data["details"]["audio_features"],
        )
        try:
            recommendations = self.recommender_agent.recommend(
                mood_data["mood"],
                recommendation_features,
                limit=5,
                user_history=user_history,
                listening_history=listening_history,
                access_token=access_token,
            )
        except Exception as exc:
            raise RuntimeError(f"Mistral recommendation reranking failed: {exc}") from exc
        ranked_recommendations = self.recommender_agent.rank_suggestions(recommendations, mood_data["mood"])
        mood_entry = {
            "id": len(user_history) + 1,
            "mood": mood_data["mood"],
            "intensity": mood_data["intensity"],
            "confidence": mood_data["confidence"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "emotions": mood_data["details"]["emotion_scores"],
        }
        try:
            self.history_agent.add_mood_entry(user_id, mood_entry)
            updated_history = self.history_agent.get_history(user_id, limit=10)
        except Exception as exc:
            raise RuntimeError(f"DynamoDB history write failed: {exc}") from exc
        notification = self.notification_agent.mood_alert(user_id, mood_data["mood"], mood_data["intensity"])

        return {
            "user": DEMO_USER,
            "mood": mood_data,
            "recommendations": ranked_recommendations,
            "history": updated_history,
            "notification": notification,
        }

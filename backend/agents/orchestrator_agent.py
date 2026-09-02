from typing import Dict
from .spotify_agent import SpotifyDataAgent
from .facial_agent import FacialEmotionAgent
from .mood_agent import MoodAnalyzerAgent
from .recommender_agent import RecommenderAgent
from .history_agent import HistoryAgent
from .notification_agent import NotificationAgent
from backend.sample_data import DEMO_USER, DEMO_TOKEN, MOOD_HISTORY


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

    def process_session(self, user_id: str, image_data: str) -> Dict:
        from datetime import datetime

        user_history = self.history_agent.get_history(user_id, limit=1000)
        mood_data = self.detect_mood(user_id, image_data)
        recommendations = self.recommender_agent.recommend(
            mood_data["mood"],
            mood_data["details"]["audio_features"],
            limit=5,
            user_history=user_history,
        )
        ranked_recommendations = self.recommender_agent.rank_suggestions(recommendations, mood_data["mood"])
        mood_entry = {
            "id": len(user_history) + 1,
            "mood": mood_data["mood"],
            "intensity": mood_data["intensity"],
            "confidence": mood_data["confidence"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "emotions": mood_data["details"]["emotion_scores"],
        }
        self.history_agent.add_mood_entry(user_id, mood_entry)
        updated_history = self.history_agent.get_history(user_id, limit=10)
        notification = self.notification_agent.mood_alert(user_id, mood_data["mood"], mood_data["intensity"])

        return {
            "user": DEMO_USER,
            "mood": mood_data,
            "recommendations": ranked_recommendations,
            "history": updated_history,
            "notification": notification,
        }

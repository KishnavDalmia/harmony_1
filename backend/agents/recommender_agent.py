from typing import Dict, List
from .spotify_agent import SpotifyDataAgent


class RecommenderAgent:
    def __init__(self):
        self.spotify_agent = SpotifyDataAgent()

    def recommend(self, mood: str, audio_features: Dict, limit: int = 5, user_history: List[Dict] | None = None) -> List[Dict]:
        return self.spotify_agent.get_recommendations(mood, audio_features, limit, user_history=user_history)

    def rank_suggestions(self, recommendations: List[Dict], mood: str) -> List[Dict]:
        ranked = sorted(
            recommendations,
            key=lambda item: (-item.get("matchScore", 0), item.get("mood") != mood)
        )
        return ranked

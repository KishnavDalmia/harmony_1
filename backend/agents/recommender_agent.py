import logging
from typing import Dict, List
from .mistral_agent import MistralRecommendationAgent
from .spotify_agent import SpotifyDataAgent

logger = logging.getLogger(__name__)


class RecommenderAgent:
    def __init__(self):
        self.spotify_agent = SpotifyDataAgent()
        self.mistral_agent = MistralRecommendationAgent()

    def recommend(
        self,
        mood: str,
        audio_features: Dict,
        limit: int = 5,
        user_history: List[Dict] | None = None,
        listening_history: List[Dict] | None = None,
        access_token: str | None = None,
    ) -> List[Dict]:
        # Keep Spotify search failures distinct from Mistral rerank failures so
        # callers (orchestrator -> main.py) report the correct service instead
        # of mislabelling a Spotify error as "Mistral".
        recommendations: List[Dict] | None = None
        if access_token:
            try:
                recommendations = self.spotify_agent.search_recommendations(
                    access_token,
                    mood,
                    audio_features,
                    listening_history=listening_history,
                    limit=limit,
                )
            except Exception as exc:
                # Logged-in Spotify search failed (expired token, network, ...):
                # fall back to the local song library so mood detection still
                # returns a result instead of a 503.
                logger.warning(
                    "Spotify recommendation search failed (%s: %s); "
                    "falling back to local library",
                    type(exc).__name__,
                    exc,
                )
        if recommendations is None:
            try:
                # Logged-out fallback: score the local song library.
                recommendations = self.spotify_agent.get_recommendations(
                    mood,
                    audio_features,
                    limit,
                    user_history=user_history,
                    listening_history=listening_history,
                )
            except Exception as exc:
                raise RuntimeError(f"Spotify recommendation search failed: {exc}") from exc
        try:
            return self.mistral_agent.rerank(mood, recommendations, listening_history)
        except Exception as exc:
            raise RuntimeError(f"Mistral recommendation reranking failed: {exc}") from exc

    def rank_suggestions(self, recommendations: List[Dict], mood: str) -> List[Dict]:
        ranked = sorted(
            recommendations,
            key=lambda item: (-item.get("matchScore", 0), item.get("mood") != mood)
        )
        return ranked

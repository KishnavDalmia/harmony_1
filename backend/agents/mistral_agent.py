import json
import logging
import os
from typing import Dict, List, Optional
from urllib import request

logger = logging.getLogger(__name__)

_MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"


class MistralRecommendationAgent:
    """Optional Mistral reranker with local scoring as the availability fallback.

    When ``MISTRAL_API_KEY`` is present, the recommender asks Mistral to re-order
    the locally scored tracks for the requested mood. If the model is unavailable
    or returns invalid JSON, the original (local) ranking is returned unchanged.
    """

    def __init__(self, client: Optional[object] = None):
        self.enabled = bool(os.getenv("MISTRAL_API_KEY"))
        self.model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
        self.api_key = os.getenv("MISTRAL_API_KEY")
        # Allow dependency-injecting a mock client (for tests); otherwise build
        # a thin callable wrapper over urllib.
        self.client = client or self._default_client

    def _default_client(self, body: Dict) -> Dict:
        data = json.dumps(body).encode("utf-8")
        req = request.Request(
            _MISTRAL_API_URL,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def rerank(self, mood: str, tracks: List[Dict], listening_history: Optional[List[Dict]] = None) -> List[Dict]:
        if not tracks:
            return tracks
        if not self.enabled:
            return tracks

        prompt = {
            "mood": mood,
            "tracks": [
                {"id": track["id"], "name": track["name"], "artist": track["artist"], "matchScore": track.get("matchScore", 0)}
                for track in tracks
            ],
            "recentListening": [
                {"name": entry.get("name"), "artist": entry.get("artist")}
                for entry in (listening_history or [])[:25]
            ],
        }
        body = {
            "model": self.model,
            "max_tokens": 512,
            "temperature": 0,
            "messages": [{
                "role": "user",
                "content": f"Return only a JSON array of track IDs ordered best first. Rank for the requested mood.\n{json.dumps(prompt)}",
            }],
        }
        try:
            response = self.client(body)
            content = response["choices"][0]["message"]["content"]
            ordered_ids = json.loads(content)
            by_id = {track["id"]: track for track in tracks}
            ordered = [by_id[track_id] for track_id in ordered_ids if track_id in by_id]
            ordered_set = {track["id"] for track in ordered}
            return ordered + [track for track in tracks if track["id"] not in ordered_set]
        except Exception as e:
            logger.warning(f"[fallback] Mistral rerank failed ({type(e).__name__}): {e}; using local ranking")
            return tracks
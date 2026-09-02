from typing import Dict, List
from backend.sample_data import DEMO_TOKEN, DEMO_USER, SAMPLE_TRACK, SONG_LIBRARY


class SpotifyDataAgent:
    def authenticate(self, token: str) -> bool:
        return token == DEMO_TOKEN

    def get_user_profile(self, token: str) -> Dict:
        if not self.authenticate(token):
            raise ValueError("Invalid Spotify token")
        return DEMO_USER

    def get_current_track(self, token: str) -> Dict:
        if not self.authenticate(token):
            raise ValueError("Invalid Spotify token")
        return SAMPLE_TRACK

    def get_recommendations(self, mood: str, audio_features: Dict, limit: int = 5, user_history: List[Dict] | None = None) -> List[Dict]:
        recent_moods = []
        if user_history:
            recent_moods = [entry.get("mood") for entry in user_history if entry.get("mood")]

        def score_track(track: Dict):
            features = track.get("audio_features", {})
            similarity = 0
            for key in ["energy", "valence", "danceability"]:
                similarity += abs(features.get(key, 0) - audio_features.get(key, 0))

            mood_bonus = 0 if track.get("mood") == mood else 0.6
            history_bonus = 0.0
            if track.get("mood") in recent_moods:
                history_bonus = -0.35 * recent_moods.count(track.get("mood"))

            return similarity + mood_bonus + history_bonus

        sorted_tracks = sorted(SONG_LIBRARY, key=score_track)
        recommendations = []
        for index, track in enumerate(sorted_tracks[:limit]):
            history_weight = 0.15 if track.get("mood") in recent_moods else 0.0
            base_score = max(0.0, 1 - index * 0.12) + history_weight
            recommendations.append({
                **track,
                "matchScore": round(min(0.99, base_score), 2),
            })
        return recommendations

    def refresh_token(self, token: str) -> str:
        return token

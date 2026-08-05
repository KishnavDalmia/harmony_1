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

    def get_recommendations(self, mood: str, audio_features: Dict, limit: int = 5) -> List[Dict]:
        def score_track(track: Dict):
            features = track["audio_features"]
            similarity = 0
            for key in ["energy", "valence", "danceability"]:
                similarity += abs(features.get(key, 0) - audio_features.get(key, 0))
            mood_bonus = 0 if track.get("mood") == mood else 0.5
            return similarity + mood_bonus

        sorted_tracks = sorted(SONG_LIBRARY, key=score_track)
        recommendations = []
        for score, track in enumerate(sorted_tracks[:limit]):
            base_score = max(0, 1 - score * 0.12)
            recommendations.append({
                **track,
                "matchScore": round(base_score, 2),
            })
        return recommendations

    def refresh_token(self, token: str) -> str:
        return token

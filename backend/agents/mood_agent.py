from typing import Dict


class MoodAnalyzerAgent:
    MOOD_PRIORITIES = [
        ("happy", lambda audio, emotions: audio.get("valence", 0) > 0.72 and emotions.get("happy", 0) > 0.5),
        ("energetic", lambda audio, emotions: audio.get("energy", 0) > 0.75 and emotions.get("energetic", 0) > 0.4),
        ("calm", lambda audio, emotions: audio.get("acousticness", 0) > 0.25 and emotions.get("calm", 0) > 0.5),
        ("sad", lambda audio, emotions: audio.get("valence", 0) < 0.45 and emotions.get("sad", 0) > 0.4),
        ("romantic", lambda audio, emotions: audio.get("valence", 0) > 0.65 and emotions.get("calm", 0) > 0.45),
        ("dreamy", lambda audio, emotions: audio.get("acousticness", 0) > 0.3 and emotions.get("surprised", 0) > 0.35),
    ]

    def analyze(self, audio_features: Dict, emotions: Dict) -> Dict:
        if not audio_features or not emotions:
            raise ValueError("Audio features and emotions are required")

        primary_emotion = max(emotions, key=emotions.get)
        mood = self._resolve_mood(audio_features, emotions, primary_emotion)

        intensity_score = (audio_features.get("energy", 0) + emotions.get(primary_emotion, 0)) / 2
        confidence_score = min(0.98, 0.5 + (sum(emotions.values()) / (len(emotions) * 1.5)))

        return {
            "mood": mood,
            "intensity": min(10, max(1, int(round(intensity_score * 10)))),
            "confidence": round(confidence_score, 2),
            "primary_emotion": primary_emotion,
            "reason": f"Combined audio valence {audio_features.get('valence')} with emotion {primary_emotion}",
            "details": {
                "audio_features": audio_features,
                "emotion_scores": emotions,
            },
        }

    def _resolve_mood(self, audio_features: Dict, emotions: Dict, primary_emotion: str) -> str:
        for mood_name, rule in self.MOOD_PRIORITIES:
            if rule(audio_features, emotions):
                return mood_name

        if primary_emotion in ["happy", "surprised"]:
            return "happy"
        if primary_emotion in ["sad", "fearful"]:
            return "sad"
        if primary_emotion in ["calm", "disgusted"]:
            return "calm"
        if primary_emotion == "energetic":
            return "energetic"
        return "neutral"

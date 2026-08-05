from typing import Dict


class NotificationAgent:
    def notify(self, user_id: str, message: str, metadata: Dict = None) -> Dict:
        notification = {
            "user_id": user_id,
            "message": message,
            "metadata": metadata or {},
            "delivered": True,
        }
        return notification

    def mood_alert(self, user_id: str, mood: str, intensity: int) -> Dict:
        message = f"New mood detected: {mood} with intensity {intensity}/10. Here are fresh recommendations."
        return self.notify(user_id, message, {"mood": mood, "intensity": intensity})

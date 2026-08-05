import os
from typing import Dict, List
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sample_data import USER_HISTORY

class HistoryAgent:
    def __init__(self):
        self.use_dynamodb = os.getenv('USE_AWS_DYNAMODB', 'false').lower() == 'true'
        self.fallback_enabled = True

        if self.use_dynamodb:
            self.dynamodb = boto3.resource('dynamodb')
            self.mood_history_table = self.dynamodb.Table('MoodHistory')
            self.user_prefs_table = self.dynamodb.Table('UserPreferences')

    def add_mood_entry(self, user_id: str, mood_entry: Dict) -> None:
        if not user_id or not mood_entry:
            raise ValueError("User ID and mood entry are required")

        if self.use_dynamodb:
            try:
                self._add_mood_entry_dynamodb(user_id, mood_entry)
            except Exception as e:
                print(f"DynamoDB failed, falling back to memory: {e}")
                if self.fallback_enabled:
                    self._add_mood_entry_memory(user_id, mood_entry)
                else:
                    raise
        else:
            self._add_mood_entry_memory(user_id, mood_entry)

    def _add_mood_entry_dynamodb(self, user_id: str, mood_entry: Dict) -> None:
        """Add mood entry to DynamoDB"""
        try:
            # Add timestamp if not present
            mood_entry['timestamp'] = mood_entry.get('timestamp', datetime.utcnow().isoformat() + 'Z')

            # Store in DynamoDB
            self.mood_history_table.put_item(
                Item={
                    'user_id': user_id,
                    'entry_id': mood_entry.get('id', datetime.utcnow().timestamp()),
                    'timestamp': mood_entry['timestamp'],
                    'mood': mood_entry['mood'],
                    'intensity': mood_entry['intensity'],
                    'confidence': mood_entry['confidence'],
                    'emotions': mood_entry.get('emotions', {}),
                    'metadata': mood_entry.get('metadata', {})
                }
            )
        except ClientError as e:
            raise Exception(f"DynamoDB error: {e.response['Error']['Message']}")

    def _add_mood_entry_memory(self, user_id: str, mood_entry: Dict) -> None:
        """Add mood entry to in-memory storage (fallback)"""
        if user_id not in USER_HISTORY:
            USER_HISTORY[user_id] = []
        USER_HISTORY[user_id].insert(0, mood_entry)

    def get_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        if not user_id:
            raise ValueError("User ID is required")

        if self.use_dynamodb:
            try:
                return self._get_history_dynamodb(user_id, limit)
            except Exception as e:
                print(f"DynamoDB failed, falling back to memory: {e}")
                if self.fallback_enabled:
                    return self._get_history_memory(user_id, limit)
                raise
        else:
            return self._get_history_memory(user_id, limit)

    def _get_history_dynamodb(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get mood history from DynamoDB"""
        try:
            response = self.mood_history_table.query(
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id},
                ScanIndexForward=False,  # Newest first
                Limit=limit
            )
            return response['Items']
        except ClientError as e:
            raise Exception(f"DynamoDB error: {e.response['Error']['Message']}")

    def _get_history_memory(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get mood history from in-memory storage (fallback)"""
        return USER_HISTORY.get(user_id, [])[:limit]

    def get_statistics(self, user_id: str) -> Dict:
        if not user_id:
            raise ValueError("User ID is required")

        history = self.get_history(user_id, limit=1000)
        mood_count = {}
        intensity_sum = {}
        confidence_sum = {}

        for entry in history:
            mood = entry["mood"]
            mood_count[mood] = mood_count.get(mood, 0) + 1
            intensity_sum[mood] = intensity_sum.get(mood, 0) + entry.get("intensity", 0)
            confidence_sum[mood] = confidence_sum.get(mood, 0) + entry.get("confidence", 0)

        # Calculate averages
        mood_stats = {}
        for mood in mood_count:
            count = mood_count[mood]
            mood_stats[mood] = {
                "count": count,
                "percentage": round((count / len(history)) * 100, 1) if history else 0,
                "avg_intensity": round(intensity_sum[mood] / count, 1) if count > 0 else 0,
                "avg_confidence": round(confidence_sum[mood] / count, 2) if count > 0 else 0
            }

        return {
            "total_entries": len(history),
            "moods": mood_stats,
            "time_range": {
                "first": history[-1]['timestamp'] if history else None,
                "last": history[0]['timestamp'] if history else None
            } if history else {}
        }

    def get_mood_trends(self, user_id: str, time_range: str = 'week') -> Dict:
        """Get mood trends over time"""
        history = self.get_history(user_id, limit=1000)

        # Group by time period
        trends = {}
        for entry in history:
            timestamp = entry['timestamp']
            date = timestamp.split('T')[0]  # Extract date part

            if time_range == 'week':
                # Group by day of week
                week_day = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%A')
                key = week_day
            elif time_range == 'month':
                # Group by day of month
                key = date.split('-')[2]  # Day of month
            elif time_range == 'hour':
                # Group by hour of day
                hour = timestamp.split('T')[1].split(':')[0]
                key = f"{hour}:00"
            else:
                # Default to daily
                key = date

            trends[key] = trends.get(key, {})
            mood = entry['mood']
            trends[key][mood] = trends[key].get(mood, 0) + 1

        # Convert to more usable format
        result = []
        for period, mood_counts in trends.items():
            total = sum(mood_counts.values())
            mood_percentages = {mood: round((count / total) * 100, 1) for mood, count in mood_counts.items()}
            result.append({
                "period": period,
                "total": total,
                "moods": mood_percentages
            })

        return {
            "time_range": time_range,
            "trends": sorted(result, key=lambda x: x['period'])
        }
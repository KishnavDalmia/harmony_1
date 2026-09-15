import os
import json
import logging
import time
from typing import Dict, List
from datetime import datetime
from urllib import parse, request
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
import sys

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sample_data import USER_HISTORY

logger = logging.getLogger(__name__)


def _spotify_error_detail(exc: Exception) -> str:
    """Summarize a Spotify HTTP failure with status code + body snippet.

    The previous messages logged only the exception class name (``HTTPError``),
    which made 401 (expired token) vs 400 (bad request, e.g. missing seeds) vs
    404 (deprecated endpoint) indistinguishable in the logs.
    """
    status = getattr(exc, 'code', None) or getattr(getattr(exc, 'response', None), 'status', None)
    body = ''
    try:
        raw = exc.read() if hasattr(exc, 'read') else None
        if raw:
            body = raw.decode('utf-8', 'replace')[:300] if isinstance(raw, bytes) else str(raw)[:300]
    except Exception:
        body = ''
    detail = f"{type(exc).__name__}"
    if status is not None:
        detail += f" {status}"
    if body:
        detail += f": {body}"
    else:
        str_body = str(exc)
        if str_body and str_body != detail:
            detail += f": {str_body[:300]}"
    return detail


def _to_dynamo(value):
    """Recursively turn Python values into boto3/DynamoDB-safe ones.

    DynamoDB does not accept ``float``; floats become Decimals (built from
    the string form to avoid binary-floating-point artifacts). Lists, tuples
    and dicts are converted recursively. Everything else passes through.
    """
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, (list, tuple)):
        return [_to_dynamo(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_dynamo(item) for key, item in value.items()}
    return value


def _from_dynamo(value):
    """Recursively turn DynamoDB response values back into JSON-safe Python.

    Decimals become ints when integral (e.g. ``entry_id``) and floats
    otherwise, so FastAPI's JSON encoder can serialize the result.
    """
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, (list, tuple)):
        return [_from_dynamo(item) for item in value]
    if isinstance(value, dict):
        return {key: _from_dynamo(item) for key, item in value.items()}
    return value


# In-memory storage used only when DynamoDB is explicitly disabled.
USER_PREFERENCES_STORE = {}


class HistoryAgent:
    LISTENING_CACHE_TTL = 300  # seconds

    def __init__(self):
        self.use_dynamodb = os.getenv('USE_AWS_DYNAMODB', 'false').lower() == 'true'
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self._listening_cache = None
        self._listening_cached_at = 0.0

        if self.use_dynamodb:
            self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
            self.mood_history_table = self.dynamodb.Table('MoodHistory')
            self.user_prefs_table = self.dynamodb.Table('UserPreferences')

    def get_listening_history(self, access_token: str | None = None, limit: int = 25) -> List[Dict]:
        """Recently played tracks from Spotify (empty list when unauthenticated).

        Cached briefly so per-request mood detection doesn't hit the Spotify
        API every single time.
        """
        now = time.time()
        if self._listening_cache is not None and (now - self._listening_cached_at) < self.LISTENING_CACHE_TTL:
            return self._listening_cache[:limit]

        if not access_token:
            self._listening_cache = []
            self._listening_cached_at = now
            return []

        params = parse.urlencode({'limit': str(max(limit, 25))})
        request_url = f'https://api.spotify.com/v1/me/player/recently-played?{params}'

        try:
            req = request.Request(
                request_url,
                headers={'Authorization': f'Bearer {access_token}'},
            )
            with request.urlopen(req, timeout=8) as resp:
                payload = json.loads(resp.read().decode())
        except Exception as exc:
            # HTTPError.read() consumes the body on first access, so capture
            # the status from the exception object (code attr) and only read
            # the body if it is still available.
            status = getattr(exc, 'code', None)
            body = ''
            if status is not None:
                try:
                    peek = exc.fp.read() if hasattr(exc, 'fp') and exc.fp else None
                    if peek:
                        body = (peek.decode('utf-8', 'replace') if isinstance(peek, bytes) else str(peek))[:300]
                except Exception:
                    body = ''
            if body:
                detail = f"{type(exc).__name__} {status}: {body}"
            else:
                detail = _spotify_error_detail(exc)
            raise RuntimeError(f"Spotify recently-played request failed: {detail}") from exc

        recent = []
        for item in payload.get('items', [])[:limit]:
            track = item.get('track') or {}
            album = track.get('album') or {}
            images = album.get('images', [])
            played_at = item.get('played_at') or datetime.utcnow().isoformat() + 'Z'
            recent.append({
                'id': track.get('id') or f"{track.get('name')}-{played_at}",
                'name': track.get('name') or 'Unknown track',
                'artist': ', '.join(a.get('name') for a in (track.get('artists') or []) if a.get('name')),
                'album': album.get('name') or 'Recent track',
                'image': images[0]['url'] if images else '',
                'timestamp': played_at,
                'matchScore': 1.0,
                'spotifyUrl': (track.get('external_urls') or {}).get('spotify', ''),
            })

        self._listening_cache = recent
        self._listening_cached_at = now
        return recent[:limit]

    def add_mood_entry(self, user_id: str, mood_entry: Dict) -> None:
        if not user_id or not mood_entry:
            raise ValueError("User ID and mood entry are required")

        if self.use_dynamodb:
            self._add_mood_entry_dynamodb(user_id, mood_entry)
        else:
            self._add_mood_entry_memory(user_id, mood_entry)

    def _add_mood_entry_dynamodb(self, user_id: str, mood_entry: Dict) -> None:
        """Add mood entry to DynamoDB"""
        try:
            # Add timestamp if not present
            mood_entry['timestamp'] = mood_entry.get('timestamp', datetime.utcnow().isoformat() + 'Z')

            # Store in DynamoDB (floats -> Decimal so boto3 accepts the item)
            self.mood_history_table.put_item(
                Item=_to_dynamo({
                    'user_id': user_id,
                    'entry_id': mood_entry.get('id', datetime.utcnow().timestamp()),
                    'timestamp': mood_entry['timestamp'],
                    'mood': mood_entry['mood'],
                    'intensity': mood_entry['intensity'],
                    'confidence': mood_entry['confidence'],
                    'emotions': mood_entry.get('emotions', {}),
                    'metadata': mood_entry.get('metadata', {}),
                })
            )
        except ClientError as e:
            raise Exception(f"DynamoDB error: {e.response['Error']['Message']}")

    def _add_mood_entry_memory(self, user_id: str, mood_entry: Dict) -> None:
        """Add mood entry to explicitly configured local storage."""
        mood_entry['timestamp'] = mood_entry.get('timestamp', datetime.utcnow().isoformat() + 'Z')
        if user_id not in USER_HISTORY:
            USER_HISTORY[user_id] = []
        USER_HISTORY[user_id].insert(0, mood_entry)

    def get_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        if not user_id:
            raise ValueError("User ID is required")

        if self.use_dynamodb:
            return self._get_history_dynamodb(user_id, limit)
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
            if not isinstance(response, dict) or not isinstance(response.get('Items'), list):
                raise ValueError('DynamoDB returned an invalid history response')
            return [_from_dynamo(item) for item in response['Items']]
        except ClientError as e:
            raise Exception(f"DynamoDB error: {e.response['Error']['Message']}")

    def _get_history_memory(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get mood history from explicitly configured local storage."""
        return USER_HISTORY.get(user_id, [])[:limit]

    # --- User preferences (stored in the UserPreferences table) ---

    DEFAULT_PREFERENCES = {
        'notifications_enabled': True,
        'theme': 'dark',
        'default_mood_time_range': 'week',
    }

    def save_user_preferences(self, user_id: str, preferences: Dict) -> Dict:
        """Persist a user's preferences map to the UserPreferences table.

        Uses a module-level in-memory store only when DynamoDB is explicitly
        disabled for local development.
        """
        if not user_id:
            raise ValueError("User ID is required")

        merged = {**self.DEFAULT_PREFERENCES, **(preferences or {})}

        if self.use_dynamodb:
            self.user_prefs_table.put_item(
                Item=_to_dynamo({
                    'user_id': user_id,
                    'preferences': merged,
                    'updated_at': datetime.utcnow().isoformat() + 'Z',
                })
            )
        else:
            USER_PREFERENCES_STORE[user_id] = dict(merged)

        return self.get_user_preferences(user_id)

    def get_user_preferences(self, user_id: str) -> Dict:
        """Return the user's preferences merged over the built-in defaults."""
        if not user_id:
            raise ValueError("User ID is required")

        stored = {}
        if self.use_dynamodb:
            response = self.user_prefs_table.get_item(Key={'user_id': user_id})
            item = response.get('Item') or {}
            stored = _from_dynamo(item.get('preferences')) or {}
        else:
            stored = dict(USER_PREFERENCES_STORE.get(user_id, {}))

        return {**self.DEFAULT_PREFERENCES, **stored}

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
from typing import Dict, List
from urllib import parse, request
from urllib.error import HTTPError
import json
import logging

from backend.sample_data import DEMO_TOKEN, DEMO_USER, SAMPLE_TRACK, SONG_LIBRARY

logger = logging.getLogger(__name__)

# Audio features compared when scoring a track against the requested profile.
_SIMILARITY_KEYS = ("energy", "valence", "danceability", "acousticness")


def _spotify_error_detail(exc: Exception) -> str:
    """Summarize a Spotify HTTP failure with status code + body snippet.

    Mirrors the helper in history_agent so both Spotify call sites report the
    status (401 expired token vs 400 missing seeds vs 404 deprecated endpoint)
    instead of just ``HTTPError``.
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

    def get_recommendations(
        self,
        mood: str,
        audio_features: Dict,
        limit: int = 5,
        user_history: List[Dict] | None = None,
        listening_history: List[Dict] | None = None,
    ) -> List[Dict]:
        """Mood-first recommendations over the local song library.

        Ranking signals, in order of importance:
          1. Tracks tagged with the detected mood always rank above others.
          2. Audio-feature similarity to the requested profile.
          3. A small penalty for moods that already appear often in recent history
             (so consecutive sessions don't repeat the same mood block).
          4. A bonus when the user's listening history (Spotify recently played)
             shows affinity for the artist (or the exact track).
        """
        recent_moods = [e.get("mood") for e in (user_history or []) if e.get("mood")]

        artist_counts: Dict[str, int] = {}
        listened_tracks = set()
        for entry in listening_history or []:
            artist = (entry.get("artist") or "").strip().lower()
            name = (entry.get("name") or "").strip().lower()
            if artist:
                artist_counts[artist] = artist_counts.get(artist, 0) + 1
            if artist and name:
                listened_tracks.add((artist, name))

        def _similarity(features: Dict) -> float:
            diffs = [
                abs(float(features.get(key, 0.5)) - float(audio_features.get(key, 0.5)))
                for key in _SIMILARITY_KEYS
            ]
            return 1.0 - (sum(diffs) / len(diffs))

        def _listening_bonus(track: Dict) -> float:
            artist = (track.get("artist") or "").strip().lower()
            name = (track.get("name") or "").strip().lower()
            bonus = 0.0
            if artist in artist_counts:
                bonus = min(0.18, 0.06 * artist_counts[artist])
            if (artist, name) in listened_tracks:
                bonus = max(bonus, 0.25)
            return bonus

        scored = []
        for track in SONG_LIBRARY:
            similarity = _similarity(track.get("audio_features", {}))
            mood_match = 1 if track.get("mood") == mood else 0
            mood_penalty = min(0.3, 0.12 * recent_moods.count(track.get("mood")))
            fit = similarity + 0.5 * mood_match + _listening_bonus(track) - mood_penalty
            scored.append((mood_match, fit, track))

        # Mood-matched tracks first, then by overall fit.
        scored.sort(key=lambda item: (-item[0], -item[1]))

        recommendations = []
        for _mood_match, fit, track in scored[:limit]:
            recommendations.append({
                **track,
                "matchScore": round(min(0.99, max(0.05, fit)), 2),
            })
        return recommendations

    def refresh_token(self, token: str) -> str:
        return token

    def search_recommendations(
        self,
        access_token: str,
        mood: str,
        audio_features: Dict,
        listening_history: List[Dict] | None = None,
        limit: int = 5,
    ) -> List[Dict]:
        """Live mood- and taste-aware recommendations from the Spotify API.

        Uses the user's recently-played tracks as seeds and the detected mood's
        audio profile as target features, so the returned tracks match both the
        mood and the user's taste. Falls back to the local song library only if
        the API call fails.
        """
        seed_tracks, seed_artists = self._seed_params(listening_history or [])

        if not seed_tracks and not seed_artists:
            # Spotify's recommendations endpoint requires at least one seed;
            # a seed-less call is guaranteed to fail, so skip the network round
            # trip and let the caller fall back to the local song library.
            logger.info(
                "Skipping Spotify recommendations request: no seed tracks/artists "
                "in listening history; using local library"
            )
            raise RuntimeError(
                "Spotify recommendations request skipped: no seed tracks or artists in listening history"
            )

        params = {
            'limit': str(max(limit, 50)),
            'market': 'US',
        }
        if seed_tracks:
            params['seed_tracks'] = ','.join(seed_tracks[:5])
        if seed_artists:
            params['seed_artists'] = ','.join(seed_artists[:3])
        for key in _SIMILARITY_KEYS:
            value = audio_features.get(key)
            if value is not None:
                params[f'target_{key}'] = str(value)

        req = request.Request(
            'https://api.spotify.com/v1/recommendations?' + parse.urlencode(params),
            headers={'Authorization': f'Bearer {access_token}'},
        )
        try:
            with request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
        except HTTPError as exc:
            raise RuntimeError(f"Spotify recommendations request failed: {_spotify_error_detail(exc)}") from exc
        except Exception as exc:
            raise RuntimeError(f"Spotify recommendations request failed: {_spotify_error_detail(exc)}") from exc

        tracks = data.get('tracks', [])
        if not tracks:
            return []

        # Fetch real audio features for scoring.
        features_map = self._fetch_audio_features(access_token, [t.get('id') for t in tracks])

        recommendations = []
        for track in tracks:
            tid = track.get('id')
            features = features_map.get(tid, {})
            similarity = self._similarity(features, audio_features)
            recommendations.append({
                'id': tid,
                'name': track.get('name', 'Unknown track'),
                'artist': ', '.join(a.get('name') for a in (track.get('artists') or []) if a.get('name')),
                'album': (track.get('album') or {}).get('name', 'Unknown album'),
                'image': self._album_image(track.get('album') or {}),
                'duration': int((track.get('duration_ms') or 0) / 1000),
                'progress': 0,
                'isPlaying': False,
                'spotifyUrl': (track.get('external_urls') or {}).get('spotify', ''),
                'audio_features': features,
                'mood': mood,
                'matchScore': round(min(0.99, max(0.05, similarity)), 2),
            })

        recommendations.sort(key=lambda t: t['matchScore'], reverse=True)
        return recommendations[:limit]

    def _seed_params(self, listening_history: List[Dict]):
        """Extract up to 5 track ids and up to 3 artist names from recently played."""
        seed_tracks = []
        seed_artists = []
        artist_counts: Dict[str, int] = {}
        for entry in listening_history:
            tid = entry.get('id')
            if tid and tid not in seed_tracks:
                seed_tracks.append(tid)
            artist = (entry.get('artist') or '').strip()
            if artist:
                artist_counts[artist] = artist_counts.get(artist, 0) + 1
        top_artists = sorted(artist_counts, key=artist_counts.get, reverse=True)
        return seed_tracks[:5], top_artists[:3]

    def _fetch_audio_features(self, access_token: str, track_ids: List[str]) -> Dict:
        """Fetch audio features for a batch of track ids (up to 100 per call)."""
        if not track_ids:
            return {}
        ids = [i for i in track_ids if i]
        if not ids:
            return {}
        params = parse.urlencode({'ids': ','.join(ids)})
        req = request.Request(
            f'https://api.spotify.com/v1/audio-features?{params}',
            headers={'Authorization': f'Bearer {access_token}'},
        )
        try:
            with request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
        except Exception:
            return {}
        result = {}
        for item in data.get('audio_features') or []:
            if item and item.get('id'):
                result[item['id']] = {
                    key: item.get(key) for key in _SIMILARITY_KEYS
                }
        return result

    def _similarity(self, features: Dict, target: Dict) -> float:
        diffs = [
            abs(float(features.get(key, 0.5)) - float(target.get(key, 0.5)))
            for key in _SIMILARITY_KEYS
        ]
        return 1.0 - (sum(diffs) / len(diffs))

    def _album_image(self, album: Dict) -> str:
        images = album.get('images') or []
        return images[0]['url'] if images else ''

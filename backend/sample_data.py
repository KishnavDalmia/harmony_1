from datetime import datetime, timedelta

DEMO_USER = {
    "id": "demo-user",
    "name": "Harmony Demo",
    "email": "demo@harmony.app",
    "demo": True,
}

DEMO_TOKEN = "demo_token"

SAMPLE_TRACK = {
    "id": 1,
    "name": "Blinding Lights",
    "artist": "The Weeknd",
    "album": "After Hours",
    "image": "https://i.scdn.co/image/ab67616d0000485128933b847344585462672d47",
    "duration": 200,
    "progress": 45,
    "isPlaying": True,
    "audio_features": {
        "energy": 0.85,
        "valence": 0.75,
        "danceability": 0.88,
        "tempo": 171,
        "acousticness": 0.08,
        "instrumentalness": 0.0,
    },
}

SONG_LIBRARY = [
    {
        "id": 2,
        "name": "Levitating",
        "artist": "Dua Lipa",
        "album": "Future Nostalgia",
        "image": "https://i.scdn.co/image/ab67616d00004851555137157d184471b8d447d0",
        "duration": 203,
        "progress": 0,
        "isPlaying": False,
        "audio_features": {"energy": 0.82, "valence": 0.91, "danceability": 0.85, "tempo": 103, "acousticness": 0.12, "instrumentalness": 0.0},
        "mood": "happy",
    },
    {
        "id": 3,
        "name": "Sunflower",
        "artist": "Post Malone, Swae Lee",
        "album": "Spider-Man: Into the Spider-Verse",
        "image": "https://i.scdn.co/image/ab67616d000048518863bc11d269504f94859340",
        "duration": 158,
        "progress": 0,
        "isPlaying": False,
        "audio_features": {"energy": 0.65, "valence": 0.78, "danceability": 0.72, "tempo": 90, "acousticness": 0.22, "instrumentalness": 0.0},
        "mood": "calm",
    },
    {
        "id": 4,
        "name": "Dreams",
        "artist": "Fleetwood Mac",
        "album": "Rumours",
        "image": "https://i.scdn.co/image/ab67616d00004851dc9c09620fdf0716a7b696c7",
        "duration": 258,
        "progress": 0,
        "isPlaying": False,
        "audio_features": {"energy": 0.54, "valence": 0.85, "danceability": 0.6, "tempo": 120, "acousticness": 0.35, "instrumentalness": 0.0},
        "mood": "dreamy",
    },
    {
        "id": 5,
        "name": "Don’t Start Now",
        "artist": "Dua Lipa",
        "album": "Future Nostalgia",
        "image": "https://i.scdn.co/image/ab67616d00004851f7b0d8b3fc8bb93f88cc2d8a",
        "duration": 183,
        "progress": 0,
        "isPlaying": False,
        "audio_features": {"energy": 0.91, "valence": 0.88, "danceability": 0.79, "tempo": 124, "acousticness": 0.04, "instrumentalness": 0.0},
        "mood": "energetic",
    },
    {
        "id": 6,
        "name": "All of Me",
        "artist": "John Legend",
        "album": "Love in the Future",
        "image": "https://i.scdn.co/image/ab67616d000048518efa1bf55dffb5e6f68e8306",
        "duration": 269,
        "progress": 0,
        "isPlaying": False,
        "audio_features": {"energy": 0.45, "valence": 0.72, "danceability": 0.52, "tempo": 120, "acousticness": 0.3, "instrumentalness": 0.0},
        "mood": "romantic",
    },
]

MOOD_HISTORY = [
    {
        "id": 1,
        "mood": "happy",
        "intensity": 8,
        "confidence": 0.92,
        "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",
        "emotions": {"happy": 0.92, "calm": 0.55, "energetic": 0.63},
    },
    {
        "id": 2,
        "mood": "calm",
        "intensity": 6,
        "confidence": 0.88,
        "timestamp": (datetime.utcnow() - timedelta(minutes=30)).isoformat() + "Z",
        "emotions": {"calm": 0.82, "happy": 0.4, "neutral": 0.6},
    },
    {
        "id": 3,
        "mood": "energetic",
        "intensity": 9,
        "confidence": 0.95,
        "timestamp": (datetime.utcnow() - timedelta(minutes=15)).isoformat() + "Z",
        "emotions": {"energetic": 0.9, "happy": 0.85, "surprised": 0.5},
    },
]

USER_HISTORY = {
    DEMO_USER["id"]: MOOD_HISTORY.copy(),
}

export const sampleMoodHistory = [
  { id: 1, mood: 'happy', intensity: 8, timestamp: new Date(Date.now() - 3600000).toISOString(), confidence: 0.92 },
  { id: 2, mood: 'calm', intensity: 6, timestamp: new Date(Date.now() - 1800000).toISOString(), confidence: 0.88 },
  { id: 3, mood: 'energetic', intensity: 9, timestamp: new Date(Date.now() - 900000).toISOString(), confidence: 0.95 },
];

export const sampleRecommendations = [
  {
    id: 1,
    name: 'Blinding Lights',
    artist: 'The Weeknd',
    album: 'After Hours',
    mood: 'energetic',
    matchScore: 0.94,
    audioFeatures: { energy: 0.85, valence: 0.75, danceability: 0.88 },
    image: 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=400&q=80',
    spotifyUrl: 'https://open.spotify.com/track/0VjIjW4GlUZAMYd2vXMi3b',
  },
  {
    id: 2,
    name: 'Levitating',
    artist: 'Dua Lipa',
    album: 'Future Nostalgia',
    mood: 'happy',
    matchScore: 0.91,
    audioFeatures: { energy: 0.82, valence: 0.91, danceability: 0.85 },
    image: 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=400&q=80',
    spotifyUrl: 'https://open.spotify.com/track/58SZgPQmD9wdxkpY0tTPIc',
  },
  {
    id: 3,
    name: 'Sunflower',
    artist: 'Post Malone, Swae Lee',
    album: 'Spider-Man: Into the Spider-Verse',
    mood: 'calm',
    matchScore: 0.89,
    audioFeatures: { energy: 0.65, valence: 0.78, danceability: 0.72 },
    image: 'https://images.unsplash.com/photo-1459749411175-04bf5292ceea?auto=format&fit=crop&w=400&q=80',
    spotifyUrl: 'https://open.spotify.com/track/0eIubxzEPvIoKgBawqYsih',
  },
];

export const sampleTrack = {
  id: 1,
  name: 'Blinding Lights',
  artist: 'The Weeknd',
  album: 'After Hours',
  progress: 45,
  duration: 200,
  isPlaying: true,
  image: 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=400&q=80',
  spotifyUrl: 'https://open.spotify.com/track/6gBFP58HNfVXvTnTgsa4k1?si=5e8a8e8e9e8e4a0e',
};

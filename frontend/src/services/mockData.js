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
    image: 'https://i.scdn.co/image/ab67616d0000485128933b847344585462672d47',
  },
  {
    id: 2,
    name: 'Levitating',
    artist: 'Dua Lipa',
    album: 'Future Nostalgia',
    mood: 'happy',
    matchScore: 0.91,
    audioFeatures: { energy: 0.82, valence: 0.91, danceability: 0.85 },
    image: 'https://i.scdn.co/image/ab67616d00004851555137157d184471b8d447d0',
  },
  {
    id: 3,
    name: 'Sunflower',
    artist: 'Post Malone, Swae Lee',
    album: 'Spider-Man: Into the Spider-Verse',
    mood: 'calm',
    matchScore: 0.89,
    audioFeatures: { energy: 0.65, valence: 0.78, danceability: 0.72 },
    image: 'https://i.scdn.co/image/ab67616d000048518863bc11d269504f94859340',
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
  image: 'https://i.scdn.co/image/ab67616d0000485128933b847344585462672d47',
};

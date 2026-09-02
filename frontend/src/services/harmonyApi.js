import axios from 'axios';

const BASE_URL = '';

const buildHeaders = () => {
  const token = localStorage.getItem('harmony_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const normalizeTrack = (track = {}) => {
  const image =
    track.image ||
    track.coverArt ||
    track.albumArt ||
    track.album?.images?.[0]?.url ||
    'https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=400&q=80';

  const artist =
    track.artist ||
    (Array.isArray(track.artists) ? track.artists.map((a) => a.name).join(', ') : '') ||
    'Unknown artist';

  const duration = Number(track.duration || (track.duration_ms ? track.duration_ms / 1000 : 180));

  return {
    ...track,
    id: track.id ?? track.track_id ?? 0,
    name: track.name || 'Unknown track',
    artist,
    album: track.album || track.album_name || 'Unknown album',
    image,
    duration: Number.isFinite(duration) ? duration : 180,
    progress: Number(track.progress || 0),
    isPlaying: Boolean(track.isPlaying ?? track.is_playing ?? false),
    audioFeatures: track.audioFeatures || track.audio_features || {},
    soundcloudUrl:
      track.soundcloudUrl || track.soundcloud_url || track.permalink_url || track.url || track.link || '',
  };
};

const mapTrack = (track) => normalizeTrack(track);

export async function login() {
  const response = await axios.post(`${BASE_URL}/auth`);
  const { token, user } = response.data;
  localStorage.setItem('harmony_token', token);
  return { token, user };
}

export async function logout() {
  localStorage.removeItem('harmony_token');
}

export async function getProfile() {
  const response = await axios.get(`${BASE_URL}/me`, { headers: buildHeaders() });
  return response.data;
}

export async function getCurrentTrack() {
  const response = await axios.get(`${BASE_URL}/current-track`, { headers: buildHeaders() });
  return mapTrack(response.data);
}

export async function detectMood(imageData) {
  const response = await axios.post(
    `${BASE_URL}/detect-mood`,
    { imageData },
    { headers: buildHeaders() }
  );
  return response.data;
}

export async function getHistory() {
  const response = await axios.get(`${BASE_URL}/history`, { headers: buildHeaders() });
  return response.data;
}

export async function getRecommendations(mood, audioFeatures) {
  const response = await axios.post(
    `${BASE_URL}/recommendations`,
    { mood, audioFeatures },
    { headers: buildHeaders() }
  );
  return response.data.recommendations.map(mapTrack);
}

export async function sendNotification(message) {
  const response = await axios.post(
    `${BASE_URL}/notify`,
    { message: { message } },
    { headers: buildHeaders() }
  );
  return response.data;
}

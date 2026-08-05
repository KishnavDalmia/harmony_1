import axios from 'axios';

const BASE_URL = '';

const buildHeaders = () => {
  const token = localStorage.getItem('harmony_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const mapTrack = (track) => ({
  ...track,
  audioFeatures: track.audioFeatures || track.audio_features || {},
});

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

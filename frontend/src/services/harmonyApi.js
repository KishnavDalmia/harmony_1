import axios from 'axios';

const BASE_URL = '';

// A hard ceiling on every request so that no single call (refresh, detect-mood,
// history, ...) can leave the UI spinning forever. On timeout the request fails
// with a clear error instead of hanging.
const REQUEST_TIMEOUT_MS = 20000;

// Public instance so callers/tests can attach the timeout too (JWT-style).
export const apiClient = axios;
axios.defaults.timeout = REQUEST_TIMEOUT_MS;

// OAuth token storage keys. The access token is short-lived (Spotify expires
// it after ~1 hour); the refresh token is used to obtain a new one.
const TOKEN_KEY = 'harmony_token';
const REFRESH_TOKEN_KEY = 'harmony_refresh_token';
const TOKEN_EXPIRES_KEY = 'harmony_token_expires_at';

export const FALLBACK_TRACK_IMAGE =
  'https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=400&q=80';

const TOKEN_SKEW_MS = 60 * 1000;

const isAccessTokenExpired = () => {
  const expiresAt = Number(localStorage.getItem(TOKEN_EXPIRES_KEY) || 0);
  if (!expiresAt) return false;
  return Date.now() > expiresAt - TOKEN_SKEW_MS;
};

const buildHeaders = () => {
  // Never attach a token we already know is expired: the backend forwards it
  // to Spotify (recently-played + recommendations), which rejects it and
  // produces the "Spotify listening history unavailable" / "recommendation
  // search failed" warnings. Let the request go unauthenticated (local
  // library fallback) instead of sending a doomed token.
  if (isAccessTokenExpired()) return {};
  const token = localStorage.getItem(TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const getStoredToken = () => localStorage.getItem(TOKEN_KEY);

// A session is only usable if we can renew its access token. Sessions created
// before refresh tokens existed (or with a missing refresh token) are invalid.
export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY);

export const setTokens = ({ accessToken, refreshToken, expiresIn }) => {
  if (!accessToken) return;
  localStorage.setItem(TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
  localStorage.setItem(TOKEN_EXPIRES_KEY, String(Date.now() + (Number(expiresIn) || 3600) * 1000));
};

export const clearTokens = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(TOKEN_EXPIRES_KEY);
};

let refreshPromise = null;

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  if (!refreshPromise) {
    // Use a serialized config so this refresh call bypasses the request/response
    // interceptors entirely: we must NOT retry/refresh inside a refresh, or a
    // dead/invalid refresh token produces an infinite 401 -> refresh -> 401 loop.
    refreshPromise = axios
      .post(`${BASE_URL}/spotify/refresh`, { refresh_token: refreshToken }, {
        _noInterceptors: true,
      })
      .then(({ data }) => {
        setTokens({
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          expiresIn: data.expires_in,
        });
        return data.access_token;
      });
  }

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

// Attach the stored access token to every API request. If the token is merely
// stale (past its expiry), try to refresh it first so the request still goes
// out authenticated; if the refresh fails, send the request unauthenticated
// (local-library fallback) instead of with a doomed token.
//
// CRITICAL: never proactively refresh *for* the refresh endpoint itself. If we
// did, the refresh POST would re-enter this interceptor with an expired token
// and a still-present refresh token, awaiting its own refresh promise and
// deadlocking ("infinite buffer") before the request ever leaves the browser.
// (The refresh call is dispatched with _noInterceptors, so it never reaches
// this interceptor anyway.)
axios.interceptors.request.use(async (config) => {
  if (config._noInterceptors) {
    return config;
  }
  const isRefreshCall = (config.url || '').includes('/spotify/refresh');
  const shouldRefresh = !isRefreshCall && isAccessTokenExpired() && localStorage.getItem(REFRESH_TOKEN_KEY) && !config._refreshed;
  if (shouldRefresh) {
    config._refreshed = true;
    try {
      await refreshAccessToken();
    } catch {
      // The stored refresh token is dead (revoked/expired) or the refresh call
      // failed. Discard the session so we stop sending a doomed token and don't
      // retry the refresh on every subsequent request. The UI already handles
      // the logged-out state (local-library fallback).
      clearTokens();
    }
  }
  const headers = buildHeaders();
  if (headers.Authorization) {
    config.headers.Authorization = headers.Authorization;
  } else if (config.headers) {
    delete config.headers.Authorization;
  }
  return config;
});

// On a 401, attempt a single token refresh and retry the request. If the
// refresh fails (e.g. expired refresh token or revoked access), clear stored
// tokens so the UI can fall back to the unauthenticated state. The refresh
// call itself is dispatched with _noInterceptors, so it is exempt here and can
// never feed a 401 -> refresh -> 401 loop.
axios.interceptors.response.use(null, async (error) => {
  const { config, response } = error;
  if (response && response.status === 401 && config && !config._noInterceptors && !config._retried) {
    config._retried = true;
    try {
      await refreshAccessToken();
      return axios(config);
    } catch (refreshError) {
      clearTokens();
      return Promise.reject(refreshError);
    }
  }
  return Promise.reject(error);
});

export const normalizeTrack = (track = {}) => {
  const image =
    track.image ||
    track.coverArt ||
    track.albumArt ||
    track.album?.images?.[0]?.url ||
    FALLBACK_TRACK_IMAGE;

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
    spotifyUrl: track.spotifyUrl || track.spotify_url || track.external_urls?.spotify || '',
    soundcloudUrl:
      track.soundcloudUrl || track.soundcloud_url || track.permalink_url || track.url || track.link || '',
  };
};

const mapTrack = (track) => normalizeTrack(track);

export async function logout() {
  clearTokens();
}

export async function getProfile() {
  const response = await axios.get(`${BASE_URL}/me`);
  return response.data;
}

export async function getCurrentTrack() {
  const response = await axios.get(`${BASE_URL}/current-track`);
  return mapTrack(response.data);
}

export async function detectMood(imageData) {
  const response = await axios.post(`${BASE_URL}/detect-mood`, { imageData });
  return response.data;
}

export async function getHistory() {
  const response = await axios.get(`${BASE_URL}/history`);
  return response.data;
}

export async function getRecommendations(mood, audioFeatures) {
  const response = await axios.post(`${BASE_URL}/recommendations`, { mood, audioFeatures });
  return response.data.recommendations.map(mapTrack);
}

export async function sendNotification(message) {
  const response = await axios.post(`${BASE_URL}/notify`, { message: { message } });
  return response.data;
}

// Regression test for the "infinite buffer" deadlock: the axios request
// interceptor must NEVER proactively refresh *for* the refresh endpoint itself.
// If it did, the refresh POST would re-enter the interceptor with an expired
// token and await its own refresh promise, hanging before the request leaves
// the browser.
const axios = require('axios');
const {
  setTokens,
  clearTokens,
} = require('./harmonyApi');

const EXPIRES_KEY = 'harmony_token_expires_at';

function expireAccessToken() {
  // Directly simulate an already-expired token.
  const token = localStorage.getItem('harmony_token');
  localStorage.setItem(EXPIRES_KEY, String(Number(token ? Date.now() : Date.now()) - 60 * 1000));
}

beforeEach(() => {
  clearTokens();
  setTokens({
    accessToken: 'expired-access-token',
    refreshToken: 'valid-refresh-token',
    expiresIn: 3600, // setTokens recomputes expiry from now; force-expire below
  });
  expireAccessToken();
});

afterEach(() => {
  clearTokens();
});

describe('harmonyApi request interceptor', () => {
  it('does not re-enter refresh for the refresh endpoint (no deadlock)', async () => {
    let targetUrl = null;
    let settled = false;

    const originalAdapter = axios.defaults.adapter;
    axios.defaults.adapter = async (config) => {
      targetUrl = config.url;
      return { status: 200, statusText: 'OK', data: {}, config, headers: {} };
    };

    try {
      await Promise.race([
        axios.post('/spotify/refresh', { refresh_token: 'valid-refresh-token' }),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('DEADLOCK: refresh call never settled')), 1500)
        ),
      ]);
      settled = true;
    } finally {
      axios.defaults.adapter = originalAdapter;
    }

    expect(settled).toBe(true);
    expect(targetUrl).toBe('/spotify/refresh');
  });

  it('still attaches a fresh access token to regular requests', async () => {
    clearTokens();
    setTokens({
      accessToken: 'fresh-token',
      refreshToken: 'valid-refresh-token',
      expiresIn: 3600,
    });

    let authHeader = null;
    const originalAdapter = axios.defaults.adapter;
    axios.defaults.adapter = async (config) => {
      authHeader = config.headers.Authorization;
      return { status: 200, statusText: 'OK', data: {}, config, headers: {} };
    };

    try {
      await axios.get('/detect-mood');
    } finally {
      axios.defaults.adapter = originalAdapter;
    }

    expect(authHeader).toBe('Bearer fresh-token');
  });
});
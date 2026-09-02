import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, NavLink } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import WebcamCapture from './components/WebcamCapture';
import SoundCloudPlayer from './components/SpotifyPlayer';
import Dashboard from './pages/Dashboard';
import MoodAnalysis from './pages/MoodAnalysis';
import History from './pages/History';
import Settings from './pages/Settings';
import { login as apiLogin, logout as apiLogout, getCurrentTrack } from './services/harmonyApi';
import { History as HistoryIcon, Settings as SettingsIcon, Home, TrendingUp } from 'lucide-react';

function App() {
  const [currentMood, setCurrentMood] = useState(null);
  const [moodHistory, setMoodHistory] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [, setAuthToken] = useState(localStorage.getItem('harmony_token') || null);
  const [currentTrack, setCurrentTrack] = useState(null);
  const [showWebcam, setShowWebcam] = useState(false);

  // Sample data for demo
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tokenFromUrl = params.get('token');

    if (tokenFromUrl) {
      localStorage.setItem('harmony_token', tokenFromUrl);
      window.history.replaceState({}, '', window.location.pathname);
    }

    const token = localStorage.getItem('harmony_token');
    setAuthToken(token || null);
    if (token) {
      setIsAuthenticated(true);
      getCurrentTrack().then(setCurrentTrack).catch(() => {
        setCurrentTrack({
          name: 'Blinding Lights',
          artist: 'The Weeknd',
          album: 'After Hours',
          progress: 45,
          duration: 200,
          isPlaying: true,
          image: 'https://i.scdn.co/image/ab67616d0000485128933b847344585462672d47',
        });
      });
    }
  }, []);

  const handleMoodDetected = (moodData) => {
    setCurrentMood(moodData);
    if (moodData.recommendations) {
      setRecommendations(moodData.recommendations);
    }
    if (moodData.history) {
      setMoodHistory(moodData.history);
    } else {
      setMoodHistory(prev => [
        {
          id: prev.length + 1,
          mood: moodData.mood,
          intensity: moodData.intensity,
          confidence: moodData.confidence,
          timestamp: moodData.timestamp || new Date().toISOString(),
          emotions: moodData.emotions,
        },
        ...prev.slice(0, 9)
      ]);
    }
  };

  const handleTrackSelect = (track) => {
    const nextTrack = {
      ...track,
      isPlaying: true,
      progress: Number(track.progress || 0),
    };

    setCurrentTrack(nextTrack);

  };

  const handlePlayPause = (nextState) => {
    setCurrentTrack((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        isPlaying: typeof nextState === 'boolean' ? nextState : !prev.isPlaying,
      };
    });
  };

  const handleLogin = async () => {
    try {
      const { token } = await apiLogin();

      if (token) {
        setIsAuthenticated(true);
        setAuthToken(token);
        localStorage.setItem('harmony_token', token);
        const track = await getCurrentTrack();
        setCurrentTrack(track);
      }
    } catch (error) {
      console.error('Login failed', error);
    }
  };

  const handleLogout = async () => {
    setIsAuthenticated(false);
    setAuthToken(null);
    localStorage.removeItem('harmony_token');
    await apiLogout();
    setCurrentTrack(null);
  };

  const navigation = [
    { path: '/', name: 'Home', icon: <Home size={20} /> },
    { path: '/mood-analysis', name: 'Mood Analysis', icon: <TrendingUp size={20} /> },
    { path: '/history', name: 'History', icon: <HistoryIcon size={20} /> },
    { path: '/settings', name: 'Settings', icon: <SettingsIcon size={20} /> },
  ];

  return (
    <Router>
      <div className="min-h-screen bg-spotify-dark text-white">
        {/* Mobile Navigation */}
        <nav className="fixed bottom-0 left-0 right-0 z-50 bg-spotify-black border-t border-spotify-gray md:hidden">
          <div className="flex justify-around items-center py-2">
            {navigation.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className="flex flex-col items-center p-2 text-spotify-gray hover:text-white transition-colors"
              >
                {item.icon}
                <span className="text-xs mt-1">{item.name}</span>
              </NavLink>
            ))}
          </div>
        </nav>

        {/* Desktop Sidebar */}
        <aside className="hidden md:flex fixed left-0 top-0 h-full w-64 bg-spotify-black flex-col p-6 border-r border-spotify-gray">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-spotify-green">Harmony</h1>
            <p className="text-sm text-spotify-gray">Mood Analyzer Prototype</p>
          </div>

          <nav className="flex-1">
            <ul className="space-y-2">
              {navigation.map((item) => (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center p-3 rounded-lg transition-colors ${
                        isActive ? 'bg-spotify-light text-white' : 'text-spotify-gray hover:text-white'
                      }`
                    }
                  >
                    <span className="text-spotify-gray mr-3">{item.icon}</span>
                    <span>{item.name}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>

          <div className="mt-8">
            {isAuthenticated ? (
              <motion.button
                whileTap={{ scale: 0.98 }}
                onClick={handleLogout}
                className="w-full bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-full transition-colors"
              >
                Logout
              </motion.button>
            ) : (
              <motion.button
                whileTap={{ scale: 0.98 }}
                onClick={handleLogin}
                className="w-full spotify-button transition-colors"
              >
                Connect SoundCloud
              </motion.button>
            )}
          </div>
        </aside>

        {/* Main Content */}
        <main className="pt-16 md:pt-0 md:ml-64 min-h-screen">
          <AnimatePresence mode="wait">
            <motion.div
              key={window.location.pathname}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="p-4 md:p-8"
            >
              <Routes>
                <Route
                  path="/"
                  element={
                    <Dashboard
                      currentMood={currentMood}
                      moodHistory={moodHistory}
                      recommendations={recommendations}
                      currentTrack={currentTrack}
                      isAuthenticated={isAuthenticated}
                      onLogin={handleLogin}
                      onMoodDetected={handleMoodDetected}
                      onTrackSelect={handleTrackSelect}
                      showWebcam={showWebcam}
                      setShowWebcam={setShowWebcam}
                    />
                  }
                />
                <Route
                  path="/mood-analysis"
                  element={
                    <MoodAnalysis
                      currentMood={currentMood}
                      onMoodDetected={handleMoodDetected}
                      showWebcam={showWebcam}
                      setShowWebcam={setShowWebcam}
                    />
                  }
                />
                <Route
                  path="/history"
                  element={
                    <History
                      moodHistory={moodHistory}
                      recommendations={recommendations}
                    />
                  }
                />
                <Route
                  path="/settings"
                  element={
                    <Settings
                      isAuthenticated={isAuthenticated}
                      onLogin={handleLogin}
                      onLogout={handleLogout}
                    />
                  }
                />
                <Route path="*" element={<Navigate to="/" />} />
              </Routes>
            </motion.div>
          </AnimatePresence>
        </main>


        {/* Webcam Modal */}
        {showWebcam && (
          <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="bg-spotify-light rounded-xl p-6 max-w-2xl w-full"
            >
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">Mood Detection</h2>
                <motion.button
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setShowWebcam(false)}
                  className="text-spotify-gray hover:text-white"
                >
                  Close
                </motion.button>
              </div>
              <WebcamCapture onMoodDetected={handleMoodDetected} />
            </motion.div>
          </div>
        )}

        {/* Player Bar */}
        {currentTrack && (
          <div className="fixed bottom-16 md:bottom-0 left-0 right-0 bg-spotify-black border-t border-spotify-gray p-4">
            <SoundCloudPlayer
              track={currentTrack}
              onPlayPause={handlePlayPause}
            />
          </div>
        )}
      </div>
    </Router>
  );
}

export default App;
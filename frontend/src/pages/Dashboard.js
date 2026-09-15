import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Camera, Music, History, TrendingUp, Clock, Play, Pause } from 'lucide-react';
import MoodVisualizer from '../components/MoodVisualizer';
import RecommendationCard from '../components/RecommendationCard';
import TrackImage from '../components/TrackImage';
import { format, parseISO } from 'date-fns';

function Dashboard({
  currentMood,
  moodHistory,
  recommendations,
  currentTrack,
  isAuthenticated,
  onLogin,
  onMoodDetected,
  onTrackSelect,
  showWebcam,
  setShowWebcam
}) {
  const [activeTab, setActiveTab] = useState('recommendations');
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const getGreeting = () => {
    const hour = currentTime.getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    if (hour < 21) return 'Good Evening';
    return 'Good Night';
  };

  const recentMoods = moodHistory.slice(0, 5);

  const tabs = [
    { id: 'recommendations', label: 'Recommendations', icon: <Music size={18} /> },
    { id: 'history', label: 'Recent Moods', icon: <History size={18} /> },
  ];

  const handlePlayTrack = (track) => {
    if (onTrackSelect) {
      onTrackSelect(track);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold">
            {getGreeting()}, <span className="text-spotify-green">User</span>
          </h1>
          <p className="text-spotify-gray mt-1">
            {currentMood
              ? `Your current mood: ${currentMood.mood}`
              : 'Detect your mood to get personalized recommendations'}
          </p>
        </div>

        <div className="flex gap-3">
          <motion.button
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowWebcam(true)}
            className="flex items-center gap-2 bg-white text-black font-semibold py-2 px-4 rounded-full hover:bg-gray-200 transition-colors"
          >
            <Camera size={18} />
            Detect Mood
          </motion.button>
          {!isAuthenticated && (
            <motion.button
              whileTap={{ scale: 0.98 }}
              onClick={onLogin}
              className="spotify-button"
            >
              Connect Spotify
            </motion.button>
          )}
        </div>
      </motion.div>

      {/* Current Mood Visualization */}
      {currentMood && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gradient-to-r from-spotify-light to-spotify-black rounded-2xl p-6 md:p-8"
        >
          <div className="flex flex-col md:flex-row items-center gap-8">
            <div className="flex-1">
              <MoodVisualizer
                mood={currentMood.mood}
                intensity={currentMood.intensity}
                confidence={currentMood.confidence}
                showDetails={true}
              />
            </div>

            <div className="flex-1">
              <h3 className="text-xl font-semibold mb-4">Mood Insights</h3>
              <div className="space-y-3">
                <div className="bg-spotify-light rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <TrendingUp size={16} className="text-spotify-green" />
                    <span className="font-medium">Mood Trend</span>
                  </div>
                  <p className="text-sm text-spotify-gray">
                    Your mood has been {currentMood.mood} for the past hour
                  </p>
                </div>

                <div className="bg-spotify-light rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Music size={16} className="text-spotify-green" />
                    <span className="font-medium">Music Match</span>
                  </div>
                  <p className="text-sm text-spotify-gray">
                    We found {recommendations.length} songs that match your current mood
                  </p>
                </div>

                <div className="bg-spotify-light rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Clock size={16} className="text-spotify-green" />
                    <span className="font-medium">Session Time</span>
                  </div>
                  <p className="text-sm text-spotify-gray">
                    {format(currentTime, 'h:mm a')}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Tabs */}
      <div className="bg-spotify-light rounded-xl p-1">
        <div className="flex">
          {tabs.map((tab) => (
            <motion.button
              key={tab.id}
              whileTap={{ scale: 0.98 }}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-spotify-black text-white'
                  : 'text-spotify-gray hover:text-white'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-4"
      >
        {activeTab === 'recommendations' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold">Personalized Recommendations</h3>
              <motion.button
                whileTap={{ scale: 0.98 }}
                onClick={() => setShowWebcam(true)}
                className="flex items-center gap-2 text-spotify-green hover:text-green-400 transition-colors"
              >
                <Camera size={16} />
                Update Mood
              </motion.button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {recommendations.map((track, index) => (
                <RecommendationCard
                  key={track.id}
                  track={track}
                  index={index}
                  mood={track.mood}
                  onPlay={handlePlayTrack}
                  isPlaying={currentTrack?.id === track.id}
                />
              ))}
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div>
            <h3 className="text-xl font-semibold mb-4">Recent Mood History</h3>

            {recentMoods.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-spotify-gray">No mood history yet</p>
                <motion.button
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setShowWebcam(true)}
                  className="mt-4 spotify-button"
                >
                  Detect Your Mood
                </motion.button>
              </div>
            ) : (
              <div className="space-y-4">
                {recentMoods.map((mood, index) => (
                  <motion.div
                    key={mood.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-spotify-light rounded-xl p-4 flex items-center gap-4"
                  >
                    <div className="text-center">
                      <div className="text-sm text-spotify-gray">
                        {format(parseISO(mood.timestamp), 'h:mm a')}
                      </div>
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full bg-mood-${mood.mood}`} />
                        <span className="font-medium capitalize">{mood.mood}</span>
                      </div>
                      <div className="text-sm text-spotify-gray">
                        Intensity: {mood.intensity}/10
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-sm font-medium">
                        {Math.round(mood.confidence * 100)}% confidence
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        )}
      </motion.div>

      {/* Now Playing */}
      {currentTrack && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-spotify-light rounded-xl p-4"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <TrackImage
                src={currentTrack.image}
                alt={currentTrack.name}
                className="w-12 h-12 rounded-lg object-cover"
              />
              <div>
                <h4 className="font-semibold">{currentTrack.name}</h4>
                <p className="text-sm text-spotify-gray">{currentTrack.artist}</p>
              </div>
            </div>

            <motion.button
              whileTap={{ scale: 0.9 }}
              className="p-2 bg-white rounded-full text-black hover:bg-gray-200 transition-colors"
            >
              {currentTrack.isPlaying ? <Pause size={18} /> : <Play size={18} />}
            </motion.button>
          </div>
        </motion.div>
      )}
    </div>
  );
}

export default Dashboard;
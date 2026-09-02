import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Camera, RefreshCw, Activity, Heart, BarChart3 } from 'lucide-react';
import MoodVisualizer from '../components/MoodVisualizer';

function MoodAnalysis({ currentMood, onMoodDetected, showWebcam, setShowWebcam }) {
  const [analysisData, setAnalysisData] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Sample mood trends for demo
  const moodTrends = [
    { mood: 'happy', count: 12, percentage: 30 },
    { mood: 'calm', count: 8, percentage: 20 },
    { mood: 'energetic', count: 10, percentage: 25 },
    { mood: 'sad', count: 5, percentage: 12 },
    { mood: 'neutral', count: 5, percentage: 13 }
  ];

  const moodOverTime = [
    { time: '12:00', mood: 'calm', intensity: 6 },
    { time: '14:00', mood: 'happy', intensity: 8 },
    { time: '16:00', mood: 'energetic', intensity: 9 },
    { time: '18:00', mood: 'neutral', intensity: 5 },
    { time: '20:00', mood: 'calm', intensity: 7 },
    { time: '22:00', mood: 'sad', intensity: 4 }
  ];

  useEffect(() => {
    if (currentMood) {
      setAnalysisData({
        mood: currentMood.mood,
        intensity: currentMood.intensity,
        confidence: currentMood.confidence,
        emotions: currentMood.emotions || {},
        timestamp: currentMood.timestamp
      });

    }
  }, [currentMood]);

  const handleRefresh = () => {
    setIsAnalyzing(true);
    // Simulate analysis
    setTimeout(() => {
      setIsAnalyzing(false);
      setShowWebcam(true);
    }, 500);
  };

  const getMoodColor = (mood) => {
    const colors = {
      happy: 'bg-mood-happy',
      sad: 'bg-mood-sad',
      neutral: 'bg-mood-neutral',
      energetic: 'bg-mood-energetic',
      calm: 'bg-mood-calm',
      romantic: 'bg-mood-romantic',
      aggressive: 'bg-mood-aggressive',
      dreamy: 'bg-mood-dreamy'
    };
    return colors[mood] || 'bg-spotify-gray';
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
          <h1 className="text-3xl font-bold">Mood Analysis</h1>
          <p className="text-spotify-gray mt-1">
            Real-time mood detection and analysis
          </p>
        </div>

        <motion.button
          whileTap={{ scale: 0.98 }}
          onClick={handleRefresh}
          disabled={isAnalyzing}
          className="flex items-center gap-2 bg-white text-black font-semibold py-2 px-4 rounded-full hover:bg-gray-200 transition-colors disabled:opacity-50"
        >
          <RefreshCw size={18} className={isAnalyzing ? 'animate-spin' : ''} />
          {isAnalyzing ? 'Analyzing...' : 'Analyze Mood'}
        </motion.button>
      </motion.div>

      {/* Main Analysis */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Current Mood */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gradient-to-br from-spotify-light to-spotify-black rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Current Mood</h2>
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={() => setShowWebcam(true)}
              className="flex items-center gap-2 text-spotify-green hover:text-green-400 transition-colors"
            >
              <Camera size={16} />
              Update
            </motion.button>
          </div>

          {analysisData ? (
            <MoodVisualizer
              mood={analysisData.mood}
              intensity={analysisData.intensity}
              confidence={analysisData.confidence}
              showDetails={true}
            />
          ) : (
            <div className="text-center py-8">
              <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-spotify-light flex items-center justify-center">
                <Camera size={40} className="text-spotify-gray" />
              </div>
              <p className="text-spotify-gray">No mood data available</p>
              <motion.button
                whileTap={{ scale: 0.98 }}
                onClick={() => setShowWebcam(true)}
                className="mt-4 spotify-button"
              >
                Detect Mood
              </motion.button>
            </div>
          )}
        </motion.div>

        {/* Mood Trends */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-spotify-light rounded-2xl p-6"
        >
          <h2 className="text-xl font-semibold mb-4">Mood Distribution</h2>

          <div className="space-y-4">
            {moodTrends.map((trend, index) => (
              <motion.div
                key={trend.mood}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="capitalize font-medium">{trend.mood}</span>
                  <span className="text-sm text-spotify-gray">{trend.percentage}%</span>
                </div>
                <div className="h-3 bg-spotify-black rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full ${getMoodColor(trend.mood)}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${trend.percentage}%` }}
                    transition={{ duration: 0.5, delay: index * 0.1 }}
                  />
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Mood Over Time */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-spotify-light rounded-2xl p-6"
      >
        <h2 className="text-xl font-semibold mb-4">Mood Over Time</h2>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {moodOverTime.map((item, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="text-center"
            >
              <div className={`w-12 h-12 mx-auto mb-2 rounded-full ${getMoodColor(item.mood)} flex items-center justify-center`}>
                <span className="text-white font-bold">{item.intensity}</span>
              </div>
              <div className="text-xs text-spotify-gray">{item.time}</div>
              <div className="text-sm capitalize">{item.mood}</div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Detailed Analysis */}
      {analysisData && analysisData.emotions && Object.keys(analysisData.emotions).length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="bg-spotify-light rounded-2xl p-6"
        >
          <h2 className="text-xl font-semibold mb-4">Detailed Emotion Analysis</h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(analysisData.emotions).map(([emotion, score], index) => (
              <motion.div
                key={emotion}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
                className="text-center"
              >
                <div className="relative w-20 h-20 mx-auto mb-2">
                  <svg className="w-20 h-20 transform -rotate-90">
                    <circle
                      cx="40"
                      cy="40"
                      r="36"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                      className="text-spotify-gray opacity-30"
                    />
                    <circle
                      cx="40"
                      cy="40"
                      r="36"
                      stroke={getMoodColor(emotion)}
                      strokeWidth="4"
                      fill="none"
                      strokeDasharray="226"
                      strokeDashoffset={226 - (226 * Number(score || 0))}
                      strokeLinecap="round"
                      className="origin-center"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-sm font-medium">{Math.round(Number(score || 0) * 100)}%</span>
                  </div>
                </div>
                <div className="capitalize text-sm">{emotion}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        <motion.button
          whileTap={{ scale: 0.98 }}
          onClick={() => setShowWebcam(true)}
          className="bg-spotify-light hover:bg-spotify-gray rounded-xl p-6 transition-colors group"
        >
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 bg-spotify-green rounded-full flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
              <Camera size={24} className="text-black" />
            </div>
            <span className="font-medium">Detect Mood</span>
          </div>
        </motion.button>

        <motion.button
          whileTap={{ scale: 0.98 }}
          className="bg-spotify-light hover:bg-spotify-gray rounded-xl p-6 transition-colors group"
        >
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 bg-purple-500 rounded-full flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
              <Activity size={24} className="text-white" />
            </div>
            <span className="font-medium">View History</span>
          </div>
        </motion.button>

        <motion.button
          whileTap={{ scale: 0.98 }}
          className="bg-spotify-light hover:bg-spotify-gray rounded-xl p-6 transition-colors group"
        >
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
              <BarChart3 size={24} className="text-white" />
            </div>
            <span className="font-medium">Analytics</span>
          </div>
        </motion.button>

        <motion.button
          whileTap={{ scale: 0.98 }}
          className="bg-spotify-light hover:bg-spotify-gray rounded-xl p-6 transition-colors group"
        >
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 bg-pink-500 rounded-full flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
              <Heart size={24} className="text-white" />
            </div>
            <span className="font-medium">Favorites</span>
          </div>
        </motion.button>
      </motion.div>
    </div>
  );
}

export default MoodAnalysis;
import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Smile, Frown, Meh, Heart, Zap, Wind, Sun, Moon, Music, TrendingUp, TrendingDown, Activity } from 'lucide-react';

const moodData = {
  happy: {
    icon: Smile,
    color: 'bg-mood-happy',
    textColor: 'text-mood-happy',
    description: 'Feeling joyful and positive',
    audioFeatures: { energy: 0.8, valence: 0.9, danceability: 0.85 }
  },
  sad: {
    icon: Frown,
    color: 'bg-mood-sad',
    textColor: 'text-mood-sad',
    description: 'Feeling melancholic and reflective',
    audioFeatures: { energy: 0.4, valence: 0.3, danceability: 0.5 }
  },
  neutral: {
    icon: Meh,
    color: 'bg-mood-neutral',
    textColor: 'text-mood-neutral',
    description: 'Feeling balanced and calm',
    audioFeatures: { energy: 0.5, valence: 0.5, danceability: 0.5 }
  },
  energetic: {
    icon: Music,
    color: 'bg-mood-energetic',
    textColor: 'text-mood-energetic',
    description: 'Feeling pumped and active',
    audioFeatures: { energy: 0.9, valence: 0.8, danceability: 0.9 }
  },
  calm: {
    icon: Sun,
    color: 'bg-mood-calm',
    textColor: 'text-mood-calm',
    description: 'Feeling relaxed and peaceful',
    audioFeatures: { energy: 0.3, valence: 0.7, danceability: 0.4 }
  },
  romantic: {
    icon: Heart,
    color: 'bg-mood-romantic',
    textColor: 'text-mood-romantic',
    description: 'Feeling loving and affectionate',
    audioFeatures: { energy: 0.6, valence: 0.8, danceability: 0.7 }
  },
  aggressive: {
    icon: Zap,
    color: 'bg-mood-aggressive',
    textColor: 'text-mood-aggressive',
    description: 'Feeling intense and powerful',
    audioFeatures: { energy: 0.95, valence: 0.4, danceability: 0.6 }
  },
  dreamy: {
    icon: Moon,
    color: 'bg-mood-dreamy',
    textColor: 'text-mood-dreamy',
    description: 'Feeling imaginative and whimsical',
    audioFeatures: { energy: 0.4, valence: 0.7, danceability: 0.5 }
  }
};

function MoodVisualizer({ mood, intensity = 5, confidence = 0.8, showDetails = true }) {
  const [currentMood, setCurrentMood] = useState(mood);
  const [isPulsing, setIsPulsing] = useState(true);

  useEffect(() => {
    setCurrentMood(mood);
  }, [mood]);

  const moodInfo = moodData[currentMood] || moodData.neutral;
  const MoodIcon = moodInfo.icon;

  // Calculate intensity-based size
  const iconSize = 40 + (intensity * 2);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col items-center"
    >
      {/* Mood Ring */}
      <div className="relative">
        <motion.div
          className={`w-32 h-32 rounded-full ${moodInfo.color} opacity-20`}
          animate={isPulsing ? {
            scale: [1, 1.05, 1],
            opacity: [0.2, 0.3, 0.2]
          } : {}}
          transition={{ duration: 2, repeat: Infinity }}
        />

        <motion.div
          className={`absolute inset-4 rounded-full ${moodInfo.color} opacity-40`}
          animate={isPulsing ? {
            scale: [1, 1.1, 1],
            opacity: [0.4, 0.5, 0.4]
          } : {}}
          transition={{ duration: 2.5, repeat: Infinity, delay: 0.2 }}
        />

        <motion.div
          className="absolute inset-0 flex items-center justify-center"
          whileHover={{ scale: 1.1 }}
          onHoverStart={() => setIsPulsing(false)}
          onHoverEnd={() => setIsPulsing(true)}
        >
          <div className={`p-4 rounded-full ${moodInfo.color} shadow-lg`}>
            <MoodIcon
              className="text-white"
              size={iconSize}
            />
          </div>
        </motion.div>
      </div>

      {showDetails && (
        <div className="mt-6 text-center">
          <motion.h3
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className={`text-2xl font-bold ${moodInfo.textColor}`}
          >
            {currentMood ? currentMood.charAt(0).toUpperCase() + currentMood.slice(1) : 'Unknown'}
          </motion.h3>

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-spotify-gray mt-1"
          >
            {moodInfo.description}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex items-center justify-center gap-6 mt-4"
          >
            <div className="text-center">
              <div className="text-xs text-spotify-gray mb-1">Intensity</div>
              <div className="text-lg font-semibold">{intensity}/10</div>
            </div>

            <div className="w-px h-8 bg-spotify-gray" />

            <div className="text-center">
              <div className="text-xs text-spotify-gray mb-1">Confidence</div>
              <div className="text-lg font-semibold">{(confidence * 100).toFixed(0)}%</div>
            </div>
          </motion.div>

          {/* Audio Features Visualization */}
          {moodInfo.audioFeatures && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="mt-6 grid grid-cols-3 gap-4"
            >
              {Object.entries(moodInfo.audioFeatures).map(([feature, value]) => (
                <div key={feature} className="text-center">
                  <div className="text-xs text-spotify-gray mb-2 capitalize">{feature}</div>
                  <div className="relative w-16 h-16 mx-auto">
                    <svg className="w-16 h-16 transform -rotate-90">
                      <circle
                        cx="32"
                        cy="32"
                        r="28"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                        className="text-spotify-gray opacity-30"
                      />
                      <circle
                        cx="32"
                        cy="32"
                        r="28"
                        stroke={moodInfo.textColor}
                        strokeWidth="4"
                        fill="none"
                        strokeDasharray="176"
                        strokeDashoffset={176 - (176 * value)}
                        strokeLinecap="round"
                        className="origin-center"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-sm font-medium">{Math.round(value * 100)}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </motion.div>
          )}
        </div>
      )}
    </motion.div>
  );
}

export default MoodVisualizer;
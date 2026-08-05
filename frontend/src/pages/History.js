import React from 'react';
import { motion } from 'framer-motion';
import { Clock, Heart, TrendingUp, Activity } from 'lucide-react';
import { format, parseISO } from 'date-fns';

function History({ moodHistory, recommendations }) {
  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold">History</h1>
          <p className="text-spotify-gray mt-1">Review your recent moods and recommendations.</p>
        </div>
      </motion.div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="bg-spotify-light rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <Clock size={20} className="text-spotify-green" />
            <h2 className="text-xl font-semibold">Mood Timeline</h2>
          </div>

          <div className="space-y-3">
            {moodHistory.length === 0 ? (
              <p className="text-spotify-gray">No mood history yet. Start detecting your mood to save entries.</p>
            ) : (
              moodHistory.map((entry) => (
                <motion.div
                  key={entry.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="bg-spotify-dark rounded-2xl p-4"
                >
                  <div className="flex justify-between items-center gap-4 mb-2">
                    <div>
                      <h3 className="font-semibold capitalize">{entry.mood}</h3>
                      <p className="text-xs text-spotify-gray">{format(parseISO(entry.timestamp), 'MMM d, h:mm a')}</p>
                    </div>
                    <div className="text-sm text-spotify-gray">Confidence {Math.round(entry.confidence * 100)}%</div>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-sm text-spotify-gray">
                    <div>Intensity: {entry.intensity}/10</div>
                    <div>Emotion count: {Object.keys(entry.emotions || {}).length}</div>
                    <div>Saved from sample session</div>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </div>

        <div className="bg-spotify-light rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <Heart size={20} className="text-spotify-green" />
            <h2 className="text-xl font-semibold">Recommendations</h2>
          </div>

          <div className="space-y-3">
            {recommendations.length === 0 ? (
              <p className="text-spotify-gray">No recommendations yet. Detect your mood to get personalized songs.</p>
            ) : (
              recommendations.map((track) => (
                <motion.div
                  key={track.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-spotify-dark rounded-2xl p-4 flex gap-3 items-center"
                >
                  <img src={track.image} alt={track.name} className="w-14 h-14 rounded-lg object-cover" />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold truncate">{track.name}</h3>
                    <p className="text-xs text-spotify-gray truncate">{track.artist}</p>
                  </div>
                  <span className="text-xs text-spotify-gray">{Math.round(track.matchScore * 100)}% match</span>
                </motion.div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default History;

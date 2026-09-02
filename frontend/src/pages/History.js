import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Clock, Heart } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { getHistory as fetchHistory } from '../services/harmonyApi';

function History({ moodHistory, recommendations }) {
  const [lastFmHistory, setLastFmHistory] = useState([]);

  useEffect(() => {
    let mounted = true;

    fetchHistory()
      .then((history) => {
        if (!mounted) return;
        const tracks = Array.isArray(history) ? history : history?.tracks || [];
        setLastFmHistory(tracks.slice(0, 6));
      })
      .catch(() => {
        if (mounted) setLastFmHistory([]);
      });

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold">History</h1>
          <p className="text-spotify-gray mt-1">Review your recent moods, recommendations, and Last.fm scrobbles.</p>
        </div>
      </motion.div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="bg-spotify-light rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <Clock size={20} className="text-spotify-green" />
            <h2 className="text-xl font-semibold">Last.fm Listening History</h2>
          </div>

          <div className="space-y-3">
            {lastFmHistory.length === 0 ? (
              <p className="text-spotify-gray">No Last.fm history available yet. Add your Last.fm API key and username in the environment to populate recent tracks.</p>
            ) : (
              lastFmHistory.map((entry, index) => (
                <motion.div
                  key={entry.id || `${entry.name}-${index}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="bg-spotify-dark rounded-2xl p-4"
                >
                  <div className="flex justify-between items-center gap-4 mb-2">
                    <div className="flex items-center gap-3 min-w-0">
                      <img src={entry.image} alt={entry.name} className="w-12 h-12 rounded-lg object-cover" />
                      <div className="min-w-0">
                        <h3 className="font-semibold truncate">{entry.name}</h3>
                        <p className="text-xs text-spotify-gray truncate">{entry.artist}</p>
                      </div>
                    </div>
                    <div className="text-xs text-spotify-gray whitespace-nowrap">
                      {entry.timestamp ? format(parseISO(entry.timestamp), 'MMM d, h:mm a') : 'Recently played'}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm text-spotify-gray">
                    <div>{entry.album || 'Recent track'}</div>
                    <div className="text-right">{entry.matchScore ? `${Math.round(entry.matchScore * 100)}% match` : 'Scrobbled'}</div>
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

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Clock, Heart } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { getHistory as fetchHistory, getStoredToken } from '../services/harmonyApi';
import TrackImage from '../components/TrackImage';

function History({ moodHistory, recommendations }) {
  const [spotifyHistory, setSpotifyHistory] = useState([]);
  // 'loading' | 'ready' | 'error'; lets us show an accurate message instead of a
  // generic "no history" when the request actually failed.
  const [status, setStatus] = useState('loading');
  const isAuthenticated = Boolean(getStoredToken());

  useEffect(() => {
    let mounted = true;
    setStatus('loading');

    fetchHistory()
      .then((history) => {
        if (!mounted) return;
        const tracks = Array.isArray(history) ? history : history?.tracks || [];
        setSpotifyHistory(tracks.slice(0, 6));
        setStatus('ready');
      })
      .catch(() => {
        if (mounted) {
          setSpotifyHistory([]);
          setStatus('error');
        }
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
          <p className="text-spotify-gray mt-1">Review your recent moods, recommendations, and Spotify listening history.</p>
        </div>
      </motion.div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="bg-spotify-light rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <Clock size={20} className="text-spotify-green" />
            <h2 className="text-xl font-semibold">Spotify Listening History</h2>
          </div>

          <div className="space-y-3">
            {status === 'loading' ? (
              <p className="text-spotify-gray">Loading your recent listening…</p>
            ) : status === 'error' ? (
              <p className="text-spotify-gray">
                Couldn&apos;t load your Spotify listening history right now
                {isAuthenticated ? 'from Spotify.' : '— you aren&apos;t connected (Connect Spotify in Settings).'}{' '}
                Make sure the backend is running, then try again.
              </p>
            ) : spotifyHistory.length === 0 ? (
              <p className="text-spotify-gray">
                No recently played tracks returned{isAuthenticated ? ' from Spotify yet — play a few tracks on any device, then come back.' : '. Connect Spotify in Settings to see your listening history.'}
              </p>
            ) : (
              spotifyHistory.map((entry, index) => (
                <motion.div
                  key={entry.id || `${entry.name}-${index}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="bg-spotify-dark rounded-2xl p-4"
                >
                  <div className="flex justify-between items-center gap-4 mb-2">
                    <div className="flex items-center gap-3 min-w-0">
                      <TrackImage src={entry.image} alt={entry.name} className="w-12 h-12 rounded-lg object-cover" />
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
                    <div className="text-right">{entry.matchScore ? `${Math.round(entry.matchScore * 100)}% match` : 'Played'}</div>
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
                  <TrackImage src={track.image} alt={track.name} className="w-14 h-14 rounded-lg object-cover" />
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

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, Pause, Heart, MoreVertical, TrendingUp, Clock, Music } from 'lucide-react';

function RecommendationCard({ track, index, onPlay, isPlaying, mood }) {
  const [isLiked, setIsLiked] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  const toggleLike = (e) => {
    e.stopPropagation();
    setIsLiked(!isLiked);
  };

  const handlePlay = (e) => {
    e.stopPropagation();
    if (onPlay) onPlay(track);
  };

  const handleMenuToggle = (e) => {
    e.stopPropagation();
    setShowMenu(!showMenu);
  };

  const moodColors = {
    happy: 'bg-mood-happy',
    sad: 'bg-mood-sad',
    neutral: 'bg-mood-neutral',
    energetic: 'bg-mood-energetic',
    calm: 'bg-mood-calm',
    romantic: 'bg-mood-romantic',
    aggressive: 'bg-mood-aggressive',
    dreamy: 'bg-mood-dreamy'
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      whileHover={{ y: -5 }}
      className="bg-spotify-light rounded-xl p-4 cursor-pointer group relative"
      onClick={handlePlay}
    >
      <div className="flex gap-4">
        {/* Album Art */}
        <div className="relative">
          <img
            src={track.image || 'https://via.placeholder.com/80'}
            alt={track.name}
            className="w-16 h-16 rounded-lg object-cover"
          />

          {/* Play Button Overlay */}
          <motion.div
            className="absolute inset-0 bg-black bg-opacity-50 rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
            whileHover={{ scale: 1.05 }}
          >
            {isPlaying ? (
              <Pause className="w-6 h-6 text-white" />
            ) : (
              <Play className="w-6 h-6 text-white ml-0.5" />
            )}
          </motion.div>

          {/* Mood Badge */}
          {mood && (
            <div className={`absolute -top-2 -right-2 ${moodColors[mood]} rounded-full p-1`}>
              <Music className="w-3 h-3 text-white" />
            </div>
          )}
        </div>

        {/* Track Info */}
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold truncate">{track.name}</h4>
          <p className="text-sm text-spotify-gray truncate">{track.artist}</p>

          {/* Match Score */}
          {track.matchScore && (
            <div className="flex items-center gap-2 mt-2">
              <div className="w-16 h-1 bg-spotify-gray rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-spotify-green"
                  initial={{ width: 0 }}
                  animate={{ width: `${track.matchScore * 100}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
              <span className="text-xs text-spotify-gray">{Math.round(track.matchScore * 100)}% match</span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-col items-center gap-2">
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={toggleLike}
            className={`p-1 rounded-full ${isLiked ? 'text-spotify-green' : 'text-spotify-gray hover:text-white'}`}
          >
            <Heart className="w-4 h-4" fill={isLiked ? 'currentColor' : 'none'} />
          </motion.button>

          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={handleMenuToggle}
            className="p-1 rounded-full text-spotify-gray hover:text-white"
          >
            <MoreVertical className="w-4 h-4" />
          </motion.button>
        </div>
      </div>

      {/* Audio Features */}
      {track.audioFeatures && (
        <div className="mt-3 grid grid-cols-3 gap-2">
          <div className="text-center text-xs">
            <div className="text-spotify-gray">Energy</div>
            <div className="font-medium">{Math.round(track.audioFeatures.energy * 100)}%</div>
          </div>
          <div className="text-center text-xs">
            <div className="text-spotify-gray">Valence</div>
            <div className="font-medium">{Math.round(track.audioFeatures.valence * 100)}%</div>
          </div>
          <div className="text-center text-xs">
            <div className="text-spotify-gray">Dance</div>
            <div className="font-medium">{Math.round(track.audioFeatures.danceability * 100)}%</div>
          </div>
        </div>
      )}

      {/* Menu Dropdown */}
      {showMenu && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="absolute top-full right-4 mt-2 bg-spotify-black border border-spotify-gray rounded-lg p-2 shadow-lg z-10"
        >
          <button className="w-full text-left p-2 text-sm hover:bg-spotify-light rounded transition-colors">
            Add to Queue
          </button>
          <button className="w-full text-left p-2 text-sm hover:bg-spotify-light rounded transition-colors">
            Add to Playlist
          </button>
          <button className="w-full text-left p-2 text-sm hover:bg-spotify-light rounded transition-colors">
            View Artist
          </button>
        </motion.div>
      )}
    </motion.div>
  );
}

export default RecommendationCard;
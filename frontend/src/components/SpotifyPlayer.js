import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Play, Pause, SkipBack, SkipForward, Volume2, VolumeX, Heart, Repeat, Shuffle } from 'lucide-react';

function SpotifyPlayer({ track, onNext, onPrevious, onPlayPause }) {
  const [isPlaying, setIsPlaying] = useState(track?.isPlaying || false);
  const [volume, setVolume] = useState(0.7);
  const [progress, setProgress] = useState(track?.progress || 0);
  const [isMuted, setIsMuted] = useState(false);
  const [isLiked, setIsLiked] = useState(false);
  const [isRepeating, setIsRepeating] = useState(false);
  const [isShuffling, setIsShuffling] = useState(false);

  const audioRef = useRef(null);
  const progressRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (track) {
      setIsPlaying(track.isPlaying || false);
      setProgress(track.progress || 0);
    }
  }, [track]);

  useEffect(() => {
    // Simulate progress update
    const interval = setInterval(() => {
      if (isPlaying && !isDragging) {
        setProgress(prev => {
          const newProgress = prev + 0.5;
          return newProgress > (track?.duration || 100) ? 0 : newProgress;
        });
      }
    }, 500);

    return () => clearInterval(interval);
  }, [isPlaying, isDragging, track?.duration]);

  const togglePlayPause = () => {
    const newState = !isPlaying;
    setIsPlaying(newState);
    if (onPlayPause) onPlayPause(newState);
  };

  const handleNext = () => {
    if (onNext) onNext();
  };

  const handlePrevious = () => {
    if (onPrevious) onPrevious();
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  const toggleLike = () => {
    setIsLiked(!isLiked);
  };

  const toggleRepeat = () => {
    setIsRepeating(!isRepeating);
  };

  const toggleShuffle = () => {
    setIsShuffling(!isShuffling);
  };

  const handleProgressClick = (e) => {
    if (!progressRef.current) return;

    const rect = progressRef.current.getBoundingClientRect();
    const clickPosition = e.clientX - rect.left;
    const percentage = (clickPosition / rect.width) * 100;
    const newProgress = (percentage / 100) * (track?.duration || 100);

    setProgress(newProgress);
  };

  const handleProgressDragStart = () => {
    setIsDragging(true);
  };

  const handleProgressDragEnd = () => {
    setIsDragging(false);
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
  };

  if (!track) {
    return (
      <div className="flex items-center justify-center py-4">
        <p className="text-spotify-gray">No track playing</p>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between gap-4">
      {/* Track Info */}
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <img
          src={track.image || 'https://via.placeholder.com/40'}
          alt={track.name}
          className="w-10 h-10 rounded object-cover"
        />
        <div className="min-w-0">
          <h4 className="text-sm font-semibold truncate">{track.name}</h4>
          <p className="text-xs text-spotify-gray truncate">{track.artist}</p>
        </div>
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={toggleLike}
          className={`p-1 rounded-full ${isLiked ? 'text-spotify-green' : 'text-spotify-gray hover:text-white'}`}
        >
          <Heart className="w-4 h-4" fill={isLiked ? 'currentColor' : 'none'} />
        </motion.button>
      </div>

      {/* Player Controls */}
      <div className="flex flex-col items-center gap-2">
        <div className="flex items-center gap-4">
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={toggleShuffle}
            className={`p-1 ${isShuffling ? 'text-spotify-green' : 'text-spotify-gray hover:text-white'}`}
          >
            <Shuffle className="w-4 h-4" />
          </motion.button>

          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={handlePrevious}
            className="p-1 text-spotify-gray hover:text-white"
          >
            <SkipBack className="w-5 h-5" />
          </motion.button>

          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={togglePlayPause}
            className="p-3 bg-white rounded-full text-black hover:bg-gray-200 transition-colors"
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
          </motion.button>

          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={handleNext}
            className="p-1 text-spotify-gray hover:text-white"
          >
            <SkipForward className="w-5 h-5" />
          </motion.button>

          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={toggleRepeat}
            className={`p-1 ${isRepeating ? 'text-spotify-green' : 'text-spotify-gray hover:text-white'}`}
          >
            <Repeat className="w-4 h-4" />
          </motion.button>
        </div>

        {/* Progress Bar */}
        <div className="flex items-center gap-3 w-full max-w-md">
          <span className="text-xs text-spotify-gray">{formatTime(progress)}</span>
          <div
            ref={progressRef}
            onClick={handleProgressClick}
            className="flex-1 h-1 bg-spotify-gray rounded-full cursor-pointer relative"
          >
            <div
              className="absolute left-0 top-0 h-full bg-white rounded-full"
              style={{ width: `${(progress / (track.duration || 100)) * 100}%` }}
            />
            <div
              className="absolute left-0 top-0 h-full w-2 bg-white rounded-full"
              style={{ left: `${(progress / (track.duration || 100)) * 100}%` }}
              onMouseDown={handleProgressDragStart}
              onMouseUp={handleProgressDragEnd}
            />
          </div>
          <span className="text-xs text-spotify-gray">{formatTime(track.duration || 100)}</span>
        </div>
      </div>

      {/* Volume Controls */}
      <div className="flex items-center gap-2">
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={toggleMute}
          className="p-1 text-spotify-gray hover:text-white"
        >
          {isMuted || volume === 0 ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
        </motion.button>

        <div className="w-20 h-1 bg-spotify-gray rounded-full relative">
          <div
            className="absolute left-0 top-0 h-full bg-white rounded-full"
            style={{ width: `${isMuted ? 0 : volume * 100}%` }}
          />
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={isMuted ? 0 : volume}
            onChange={(e) => {
              const newVolume = parseFloat(e.target.value);
              setVolume(newVolume);
              if (isMuted && newVolume > 0) {
                setIsMuted(false);
              }
            }}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
        </div>
      </div>
    </div>
  );
}

export default SpotifyPlayer;
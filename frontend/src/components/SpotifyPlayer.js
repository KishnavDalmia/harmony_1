import React, { useState, useEffect } from 'react';

function SoundCloudPlayer({ track }) {
  const [isPlaying, setIsPlaying] = useState(track?.isPlaying || false);
  const [progress, setProgress] = useState(track?.progress || 0);

  useEffect(() => {
    if (track) {
      setIsPlaying(track.isPlaying || false);
      setProgress(track.progress || 0);
    }
  }, [track]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (isPlaying && track?.duration) {
        setProgress(prev => {
          const next = prev + 0.5;
          return next > track.duration ? 0 : next;
        });
      }
    }, 500);

    return () => clearInterval(interval);
  }, [isPlaying, track?.duration]);

  const soundCloudUrl = track?.soundcloudUrl || 'https://soundcloud.com/m83/midnight-city';
  const embedUrl = `https://w.soundcloud.com/player/?url=${encodeURIComponent(soundCloudUrl)}&color=%23ff5500&auto_play=${isPlaying ? 1 : 0}&hide_related=true&show_comments=false&show_user=true&show_reposts=false&show_teaser=false`;

  if (!track) {
    return (
      <div className="flex items-center justify-center py-4">
        <p className="text-spotify-gray">No track playing</p>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between gap-4 relative flex-wrap">
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <img
          src={track.image || 'https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=400&q=80'}
          alt={track.name}
          className="w-10 h-10 rounded object-cover"
        />
        <div className="min-w-0">
          <h4 className="text-sm font-semibold truncate">{track.name}</h4>
          <p className="text-xs text-spotify-gray truncate">{track.artist}</p>
        </div>
      </div>

      <div className="flex-1 min-w-[240px] max-w-xl">
        <iframe
          title="SoundCloud Web Player"
          width="100%"
          height="110"
          scrolling="no"
          frameBorder="no"
          allow="autoplay"
          src={embedUrl}
          className="rounded-lg"
        />
      </div>

      <div className="flex items-center gap-2 text-xs text-spotify-gray">
        <span>{Math.floor(progress / 60)}:{String(Math.floor(progress % 60)).padStart(2, '0')}</span>
        <span>/</span>
        <span>{Math.floor((track.duration || 0) / 60)}:{String(Math.floor((track.duration || 0) % 60)).padStart(2, '0')}</span>
      </div>
    </div>
  );
}

export default SoundCloudPlayer;
import React, { useState, useEffect } from 'react';
import TrackImage from './TrackImage';

function SpotifyPlayer({ track }) {
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

  // Only build an embed URL from a real Spotify track link. Demo tracks carry
  // numeric ids and no spotifyUrl, which would otherwise 404 on the embed host.
  const getEmbedUrl = (t) => {
    const url = typeof t?.spotifyUrl === 'string' ? t.spotifyUrl.trim() : '';
    if (!url) return '';
    const match = url.match(/^https:\/\/open\.spotify\.com\/track\/([A-Za-z0-9]{22})(\?.*)?$/);
    return match
      ? `https://open.spotify.com/embed/track/${match[1]}?utm_source=generator&theme=0`
      : '';
  };

  const embedUrl = getEmbedUrl(track);

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
        <TrackImage
          src={track.image}
          alt={track.name}
          className="w-10 h-10 rounded object-cover"
        />
        <div className="min-w-0">
          <h4 className="text-sm font-semibold truncate">{track.name}</h4>
          <p className="text-xs text-spotify-gray truncate">{track.artist}</p>
        </div>
      </div>

      <div className="flex-1 min-w-[240px] max-w-xl">
        {embedUrl ? <iframe
          title="Spotify Web Player"
          width="100%"
          height="110"
          scrolling="no"
          frameBorder="no"
          allow="autoplay"
          src={embedUrl}
          className="rounded-lg"
        /> : <p className="text-xs text-spotify-gray">No Spotify embed available for this demo track</p>}
      </div>

      <div className="flex items-center gap-2 text-xs text-spotify-gray">
        <span>{Math.floor(progress / 60)}:{String(Math.floor(progress % 60)).padStart(2, '0')}</span>
        <span>/</span>
        <span>{Math.floor((track.duration || 0) / 60)}:{String(Math.floor((track.duration || 0) % 60)).padStart(2, '0')}</span>
      </div>
    </div>
  );
}

export default SpotifyPlayer;
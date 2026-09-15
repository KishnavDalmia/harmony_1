import React from 'react';
import { FALLBACK_TRACK_IMAGE } from '../services/harmonyApi';

function TrackImage({ src, alt = '', className = '' }) {
  const handleError = (e) => {
    if (e.currentTarget.src !== FALLBACK_TRACK_IMAGE) {
      e.currentTarget.onerror = null;
      e.currentTarget.src = FALLBACK_TRACK_IMAGE;
    }
  };

  return (
    <img
      src={src || FALLBACK_TRACK_IMAGE}
      alt={alt}
      className={className}
      onError={handleError}
      loading="lazy"
    />
  );
}

export default TrackImage;
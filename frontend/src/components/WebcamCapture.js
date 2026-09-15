import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { motion } from 'framer-motion';
import { detectMood as detectMoodApi } from '../services/harmonyApi';
import { normalizeMoodResult } from '../utils/moodUtils';
import { Camera, CameraOff, Loader2, Smile, Frown, Meh, Heart, Zap, Wind, Sun, Moon, Music } from 'lucide-react';

const moodIcons = {
  happy: Smile,
  sad: Frown,
  neutral: Meh,
  angry: Zap,
  surprised: Heart,
  fearful: Wind,
  disgusted: Moon,
  calm: Sun,
  energetic: Music
};

const moodColors = {
  happy: 'bg-mood-happy',
  sad: 'bg-mood-sad',
  neutral: 'bg-mood-neutral',
  angry: 'bg-red-500',
  surprised: 'bg-pink-500',
  fearful: 'bg-purple-500',
  disgusted: 'bg-yellow-500',
  calm: 'bg-mood-calm',
  energetic: 'bg-mood-energetic'
};

function WebcamCapture({ onMoodDetected }) {
  const webcamRef = useRef(null);
  const [imgSrc, setImgSrc] = useState(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [moodResult, setMoodResult] = useState(null);
  const [error, setError] = useState(null);
  const [cameraStatus, setCameraStatus] = useState('requesting');
  const [videoConstraints, setVideoConstraints] = useState({
    width: 640,
    height: 480,
    facingMode: 'user'
  });

  const capture = useCallback(() => {
    const video = webcamRef.current?.video;
    if (!video) {
      setError('Camera unavailable.');
      return null;
    }
    if (video.readyState < 2 || !video.videoWidth) {
      // Stream is connected but not producing frames yet (camera warming up
      // or just flipped). Returning null lets the caller retry.
      return null;
    }
    const imageSrc = webcamRef.current.getScreenshot();
    setImgSrc(imageSrc);
    return imageSrc;
  }, [webcamRef]);

  const detectMood = useCallback(async () => {
    try {
      setIsCapturing(true);
      setError(null);

      let imageData = null;
      for (let attempt = 0; attempt < 3 && !imageData; attempt++) {
        if (attempt > 0) {
          await new Promise((resolve) => setTimeout(resolve, 500));
        }
        imageData = capture();
      }
      if (!imageData) {
        throw new Error('Camera is still warming up. Give it a second, then try again.');
      }

      const result = await detectMoodApi(imageData);
      const moodResultData = normalizeMoodResult(result?.mood || result);

      setMoodResult(moodResultData);

      if (onMoodDetected) {
        if (result?.mood) {
          onMoodDetected({
            ...result.mood,
            recommendations: result.recommendations,
            history: result.history,
          });
        }
      }
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail || '';
      let message = err?.response
        ? 'Failed to detect mood. Please try again.'
        : (err?.message || 'Failed to detect mood. Please try again.');
      if (status === 400) {
        message = /no face/i.test(detail)
          ? 'No face detected. Center your face in the frame with good lighting, then try again.'
          : (detail || message);
      } else if (status === 503) {
        message = detail || 'AWS mood detection is unavailable. Check the backend AWS service configuration.';
      }
      setError(message);
      console.error('Mood detection error:', err);
    } finally {
      setIsCapturing(false);
    }
  }, [capture, onMoodDetected]);

  const toggleCamera = () => {
    // The stream remounts on flip; show the loading overlay until frames flow.
    setCameraStatus('requesting');
    const nextFacingMode = videoConstraints.facingMode === 'user' ? 'environment' : 'user';
    setVideoConstraints({
      width: 640,
      height: 480,
      facingMode: nextFacingMode,
    });
  };

  const retryCapture = () => {
    setImgSrc(null);
    setMoodResult(null);
    setError(null);
  };

  const MoodIcon = moodIcons[moodResult?.mood] || Smile;

  return (
    <div className="space-y-4">
      <div className="relative">
        {imgSrc ? (
          <div className="relative">
            <img
              src={imgSrc}
              alt="Captured"
              className="w-full rounded-lg"
            />
            {moodResult && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="absolute inset-0 flex flex-col items-center justify-center bg-black bg-opacity-50 rounded-lg"
              >
                <motion.div
                  className={`p-4 rounded-full ${moodColors[moodResult.mood] || 'bg-white'}`}
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                >
                  <MoodIcon className="w-12 h-12 text-white" />
                </motion.div>
                <div className="mt-4 text-center">
                  <h3 className="text-2xl font-bold capitalize">{moodResult.mood}</h3>
                  <p className="text-sm text-spotify-gray">
                    Intensity: {moodResult.intensity}/10 | Confidence: {(moodResult.confidence * 100).toFixed(1)}%
                  </p>
                </div>
              </motion.div>
            )}
          </div>
        ) : (
          <div className="relative">
            <Webcam
              audio={false}
              ref={webcamRef}
              onUserMedia={() => setCameraStatus('ready')}
              onUserMediaError={() => {
                setCameraStatus('unavailable');
                setError('Camera unavailable.');
              }}
              screenshotFormat="image/jpeg"
              videoConstraints={videoConstraints}
              className="w-full rounded-lg"
            />
            {cameraStatus === 'requesting' && !error && (
              <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 rounded-lg">
                <span className="flex items-center gap-2 text-white">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Requesting camera...
                </span>
              </div>
            )}
            <div className="absolute bottom-4 left-4 right-4 flex justify-center">
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={detectMood}
                disabled={isCapturing}
                className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white p-4 rounded-full backdrop-blur-sm transition-all"
              >
                {isCapturing ? (
                  <Loader2 className="w-6 h-6 animate-spin" />
                ) : (
                  <Camera className="w-6 h-6" />
                )}
              </motion.button>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-600 bg-opacity-20 border border-red-500 text-red-400 p-3 rounded-lg">
            {error}
          </div>
        )}
      </div>

      <div className="flex justify-center gap-4">
        {imgSrc ? (
          <>
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={retryCapture}
              className="flex items-center gap-2 bg-spotify-light hover:bg-spotify-gray px-4 py-2 rounded-full transition-colors"
            >
              <CameraOff className="w-4 h-4" />
              Retry
            </motion.button>
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={detectMood}
              disabled={isCapturing}
              className="flex items-center gap-2 spotify-button disabled:opacity-50"
            >
              {isCapturing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Smile className="w-4 h-4" />
              )}
              Analyze Mood
            </motion.button>
          </>
        ) : (
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={toggleCamera}
            className="flex items-center gap-2 bg-spotify-light hover:bg-spotify-gray px-4 py-2 rounded-full transition-colors"
          >
            <Camera className="w-4 h-4" />
            Switch Camera
          </motion.button>
        )}
      </div>

      {moodResult && moodResult.emotions && Object.keys(moodResult.emotions).length > 0 && (
        <div className="bg-spotify-light rounded-lg p-4">
          <h4 className="font-semibold mb-3">Emotion Breakdown</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {Object.entries(moodResult.emotions).map(([emotion, score]) => (
              <div key={emotion} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="capitalize">{emotion}</span>
                  <span>{(Number(score || 0) * 100).toFixed(0)}%</span>
                </div>
                <div className="h-2 bg-spotify-black rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full ${moodColors[emotion] || 'bg-white'}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${Number(score || 0) * 100}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default WebcamCapture;
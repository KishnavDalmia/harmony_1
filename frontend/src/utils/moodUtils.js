export function normalizeMoodResult(result) {
  if (!result || typeof result !== 'object') {
    return {
      mood: 'neutral',
      intensity: 5,
      confidence: 0.5,
      emotions: {},
    };
  }

  const emotions = result.emotions && typeof result.emotions === 'object'
    ? result.emotions
    : (result.details && result.details.emotion_scores && typeof result.details.emotion_scores === 'object'
      ? result.details.emotion_scores
      : {});

  return {
    mood: result.mood || 'neutral',
    intensity: typeof result.intensity === 'number' ? result.intensity : 5,
    confidence: typeof result.confidence === 'number' ? result.confidence : 0.5,
    emotions,
  };
}

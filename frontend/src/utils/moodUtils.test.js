import { normalizeMoodResult } from './moodUtils';

describe('normalizeMoodResult', () => {
  it('reads emotion scores from backend payload details', () => {
    const mood = normalizeMoodResult({
      mood: 'happy',
      intensity: 7,
      confidence: 0.9,
      details: {
        emotion_scores: {
          happy: 0.82,
          calm: 0.41,
        },
      },
    });

    expect(mood.emotions).toEqual({
      happy: 0.82,
      calm: 0.41,
    });
  });

  it('falls back to an empty object when emotion data is missing', () => {
    expect(normalizeMoodResult({ mood: 'neutral' }).emotions).toEqual({});
  });
});

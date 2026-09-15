import base64
import hashlib
import io
import uuid
import os
import logging
from typing import Dict, Optional
from PIL import Image
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class FacialEmotionAgent:
    MOOD_MAP = ["happy", "calm", "energetic", "sad", "neutral", "romantic", "dreamy", "aggressive"]
    REKOGNITION_EMOTIONS = ["HAPPY", "CALM", "SURPRISED", "SAD", "CONFUSED", "DISGUSTED", "ANGRY", "FEAR"]

    def __init__(self):
        # Configuration from environment variables
        self.s3_bucket = os.getenv('AWS_S3_BUCKET', 'harmony-frames')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.use_aws = os.getenv('USE_AWS_REKOGNITION', 'false').lower() == 'true'

        # Lazy initialization: only create AWS clients when AWS is enabled
        # and credentials are available.
        self.rekognition = None
        self.s3 = None
        if self.use_aws:
            self._init_aws_clients()

    def _init_aws_clients(self):
        """Initialize AWS clients with region and credential validation."""
        try:
            self.rekognition = boto3.client('rekognition', region_name=self.region)
            self.s3 = boto3.client('s3', region_name=self.region)
        except NoCredentialsError:
            raise RuntimeError(
                f"AWS Rekognition credentials are unavailable in region {self.region}."
            ) from None
        except Exception as e:
            raise RuntimeError(
                f"AWS Rekognition client initialization failed in region {self.region}: {e}"
            ) from e

    def detect_mood(self, image_data: str) -> Dict:
        if not image_data:
            raise ValueError("Image data is required")

        if self.use_aws:
            return self._detect_mood_with_rekognition(image_data)

        logger.info("AWS Rekognition is disabled; using mock analysis")
        return self._detect_mood_mock(image_data)

    def _detect_mood_with_rekognition(self, image_data: str) -> Dict:
        """Detect mood using AWS Rekognition"""
        try:
            encoded_image = image_data.split(',', 1)[1] if image_data.startswith('data:') else image_data
            image_bytes = base64.b64decode(encoded_image, validate=True)
            image = Image.open(io.BytesIO(image_bytes))

            response = self.rekognition.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['ALL']
            )

            if not response.get('FaceDetails'):
                raise ValueError("No faces detected in the image")

            face = response['FaceDetails'][0]
            emotions = self._process_rekognition_emotions(face)

            primary_mood = self._determine_primary_mood(emotions)
            intensity = self._calculate_intensity(emotions, face)
            confidence = self._calculate_confidence(face)

            return {
                "mood": primary_mood,
                "intensity": intensity,
                "confidence": confidence,
                "emotions": emotions,
                "source": "aws_rekognition",
                "face_details": {
                    "age_range": face.get('AgeRange', {}),
                    "gender": face.get('Gender', {}).get('Value'),
                    "smile": face.get('Smile', {}).get('Value'),
                    "eyes_open": face.get('EyesOpen', {}).get('Value'),
                    "mouth_open": face.get('MouthOpen', {}).get('Value')
                }
            }
        except ClientError as e:
            raise Exception(f"AWS Rekognition error: {e.response['Error']['Message']}")
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Facial analysis failed: {str(e)}")

    def _process_rekognition_emotions(self, face: Dict) -> Dict:
        """Convert AWS Rekognition emotions to our format"""
        emotions = {}
        rekognition_emotions = face.get('Emotions', [])

        emotion_mapping = {
            "HAPPY": "happy",
            "CALM": "calm",
            "SURPRISED": "surprised",
            "SAD": "sad",
            "CONFUSED": "neutral",
            "DISGUSTED": "disgusted",
            "ANGRY": "angry",
            "FEAR": "fearful"
        }

        for emotion in ["happy", "sad", "angry", "surprised", "fearful", "calm", "energetic", "disgusted", "neutral"]:
            emotions[emotion] = 0.1

        for rekognition_emotion in rekognition_emotions:
            emotion_type = rekognition_emotion['Type']
            confidence = rekognition_emotion['Confidence'] / 100.0

            if emotion_type in emotion_mapping:
                mapped = emotion_mapping[emotion_type]
                emotions[mapped] = max(emotions.get(mapped, 0.1), confidence)

        return {k: round(min(1.0, v), 2) for k, v in emotions.items()}

    def _determine_primary_mood(self, emotions: Dict) -> str:
        primary_emotion = max(emotions, key=emotions.get)
        mood_mapping = {
            "happy": "happy",
            "sad": "sad",
            "angry": "aggressive",
            "surprised": "energetic",
            "fearful": "sad",
            "calm": "calm",
            "disgusted": "neutral"
        }
        return mood_mapping.get(primary_emotion, "neutral")

    def _calculate_intensity(self, emotions: Dict, face: Dict) -> int:
        primary_emotion = max(emotions, key=emotions.get)
        primary_score = emotions[primary_emotion]
        intensity_factors = [
            face.get('Smile', {}).get('Value', False),
            face.get('EyesOpen', {}).get('Value', True),
            face.get('MouthOpen', {}).get('Value', False)
        ]
        base_intensity = int(round(primary_score * 10))
        if any(intensity_factors):
            base_intensity = min(10, base_intensity + 1)
        return min(10, max(1, base_intensity))

    def _calculate_confidence(self, face: Dict) -> float:
        emotions = face.get('Emotions', [])
        if emotions:
            max_confidence = max(e['Confidence'] for e in emotions) / 100.0
        else:
            max_confidence = 0.5
        face_confidence = face.get('Confidence', 90.0) / 100.0
        combined = (max_confidence * 0.6) + (face_confidence * 0.4)
        return round(min(0.98, max(0.5, combined)), 2)

    def _detect_mood_mock(self, image_data: str) -> Dict:
        """Fallback mock implementation for development/testing"""
        hasher = hashlib.sha256(image_data.encode('utf-8'))
        seed = int(hasher.hexdigest(), 16)
        index = seed % len(self.MOOD_MAP)
        primary_mood = self.MOOD_MAP[index]

        emotions = self._build_emotion_scores(primary_mood, seed)
        return {
            "mood": primary_mood,
            "intensity": min(10, 5 + (seed % 5) + 1),
            "confidence": round(0.75 + ((seed >> 8) % 25) / 100, 2),
            "emotions": emotions,
            "source": "mock"
        }

    def _build_emotion_scores(self, primary: str, seed: int) -> Dict:
        """Build emotion scores for mock implementation"""
        base = {
            "happy": 0.2,
            "sad": 0.2,
            "angry": 0.1,
            "surprised": 0.2,
            "fearful": 0.1,
            "calm": 0.2,
            "energetic": 0.2,
            "disgusted": 0.1,
        }

        for key in base:
            boost = ((seed >> (len(key) * 3)) % 30) / 100
            base[key] = min(1.0, base[key] + boost)

        if primary in base:
            base[primary] = min(1.0, base[primary] + 0.35)

        return {k: round(v, 2) for k, v in base.items()}

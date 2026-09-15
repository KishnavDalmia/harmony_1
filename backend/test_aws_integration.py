#!/usr/bin/env python3
"""
Test script for AWS integration
"""
import os
import sys
import base64
import io
import logging
import pytest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

# Load environment variables from the backend .env file
backend_dir = Path(__file__).resolve().parent
env_path = backend_dir / '.env'
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.facial_agent import FacialEmotionAgent
from agents.history_agent import HistoryAgent
from agents.mistral_agent import MistralRecommendationAgent

# Set up logging to see detailed fallback messages
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')


def test_aws_credentials_loaded():
    """Verify that AWS credentials are loaded from the .env file."""
    print("Testing AWS credential loading...")

    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION')
    use_rekognition = os.getenv('USE_AWS_REKOGNITION', 'false').lower() == 'true'
    use_mistral = bool(os.getenv('MISTRAL_API_KEY'))

    print(f"  AWS_ACCESS_KEY_ID: {'[SET]' if aws_access_key else '[MISSING]'}")
    print(f"  AWS_SECRET_ACCESS_KEY: {'[SET]' if aws_secret_key else '[MISSING]'}")
    print(f"  AWS_REGION: {aws_region or '[MISSING]'}")
    print(f"  USE_AWS_REKOGNITION: {use_rekognition}")
    print(f"  MISTRAL_API_KEY: {'[SET]' if use_mistral else '[MISSING]'}")

    if aws_access_key and aws_secret_key and aws_region:
        print("[OK] AWS credentials are available")
        return True
    else:
        print("[WARNING] AWS credentials are not fully configured. "
              "Set them in backend/.env or via environment variables.")
        return False


def test_mistral_recommendation_rerank(caplog):
    """Exercise the Mistral contract without making a paid network call."""
    os.environ['MISTRAL_API_KEY'] = 'test-key'
    mock_client = MagicMock()
    mock_client.return_value = {
        'choices': [{'message': {'content': '[2, 1]'}}]
    }
    tracks = [
        {'id': 1, 'name': 'One', 'artist': 'Artist One', 'matchScore': 0.8},
        {'id': 2, 'name': 'Two', 'artist': 'Artist Two', 'matchScore': 0.7},
    ]

    result = MistralRecommendationAgent(client=mock_client).rerank('happy', tracks)

    assert [track['id'] for track in result] == [2, 1]
    mock_client.assert_called_once()


def test_mistral_failure_falls_back():
    """A Mistral failure must not break recommendations: local ranking is kept."""
    os.environ['MISTRAL_API_KEY'] = 'test-key'
    mock_client = MagicMock()
    mock_client.side_effect = RuntimeError('Mistral unavailable')
    tracks = [{'id': 1, 'name': 'One', 'artist': 'Artist One', 'matchScore': 0.8}]

    result = MistralRecommendationAgent(client=mock_client).rerank('happy', tracks)

    assert [track['id'] for track in result] == [1]


def test_spotify_listening_history_is_normalized(monkeypatch):
    """Verify Spotify listening history is available in the shape ranking consumes."""
    payload = b'{"items":[{"track":{"id":"abc","name":"Fix You","artists":[{"name":"Coldplay"}],"album":{"name":"X&Y","images":[{"url":"https://example.com/img.jpg"}]},"external_urls":{"spotify":"https://open.spotify.com/track/abc"}},"played_at":"2026-09-04T12:00:00Z"}]}'
    
    

    class MockResponse:
        def __enter__(self):
            return self

        def __exit__(self, exception_type, exception, traceback):
            return False

        def read(self):
            return payload

    monkeypatch.setattr('urllib.request.urlopen', lambda *args, **kwargs: MockResponse())
    history = HistoryAgent().get_listening_history(access_token='test-token', limit=1)

    assert history[0]['name'] == 'Fix You'
    assert history[0]['artist'] == 'Coldplay'

    

def test_facial_agent_mock():
    """Test facial agent in mock mode"""
    print("Testing Facial Emotion Agent (Mock Mode)...")

    # Ensure AWS is disabled
    os.environ['USE_AWS_REKOGNITION'] = 'false'

    agent = FacialEmotionAgent()

    # Test with sample image data
    sample_image = "sample_image_data_123"
    result = agent.detect_mood(sample_image)

    # Verify result structure
    assert 'mood' in result
    assert 'intensity' in result
    assert 'confidence' in result
    assert 'emotions' in result
    assert 'source' in result
    assert result['source'] == 'mock'

    print(f"[OK] Mock mode working - Detected mood: {result['mood']}")
    print(f"  Intensity: {result['intensity']}, Confidence: {result['confidence']}")
    return True

def test_facial_agent_aws_failure_propagates():
    """Enabled Rekognition failures must not produce mock analysis."""
    print("Testing Facial Emotion Agent (AWS failure)...")

    # Enable AWS and provide dummy credentials so boto3 clients can be created
    os.environ['USE_AWS_REKOGNITION'] = 'true'
    os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAIOSFODNN7EXAMPLE'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
    os.environ['AWS_REGION'] = 'us-east-1'

    with patch('boto3.client') as mock_boto:
        # Mock rekognition client to fail on detect_faces
        mock_rekognition = MagicMock()
        mock_rekognition.detect_faces.side_effect = Exception("AWS Error")
        mock_s3 = MagicMock()
        mock_boto.side_effect = [mock_rekognition, mock_s3]

        agent = FacialEmotionAgent()
        image = io.BytesIO()
        Image.new('RGB', (1, 1), 'white').save(image, format='JPEG')
        data_url = 'data:image/jpeg;base64,' + base64.b64encode(image.getvalue()).decode()

        with pytest.raises(Exception, match='Facial analysis failed'):
            agent.detect_mood(data_url)

        print("[OK] AWS failure propagated without mock implementation")
        return True


def test_rekognition_accepts_webcam_data_url(caplog):
    """A react-webcam JPEG data URL must reach the AWS path as image bytes."""
    os.environ['USE_AWS_REKOGNITION'] = 'true'
    os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAIOSFODNN7EXAMPLE'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
    os.environ['AWS_REGION'] = 'us-east-1'
    image = io.BytesIO()
    Image.new('RGB', (1, 1), 'white').save(image, format='JPEG')
    data_url = 'data:image/jpeg;base64,' + base64.b64encode(image.getvalue()).decode()

    with patch('boto3.client') as mock_boto:
        mock_rekognition = MagicMock()
        mock_rekognition.detect_faces.return_value = {'FaceDetails': []}
        mock_s3 = MagicMock()
        mock_boto.side_effect = [mock_rekognition, mock_s3]

        with pytest.raises(ValueError, match='No faces detected'):
            FacialEmotionAgent().detect_mood(data_url)
        mock_rekognition.detect_faces.assert_called_once()
        assert mock_rekognition.detect_faces.call_args.kwargs['Image']['Bytes'] == image.getvalue()

def test_rekognition_handles_confused_emotion():
    """A real Rekognition face whose strongest emotion is CONFUSED must map to
    a neutral mood WITHOUT falling back to mock (regression test for the
    KeyError: 'neutral' crash in _process_rekognition_emotions)."""
    os.environ['USE_AWS_REKOGNITION'] = 'true'
    os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAIOSFODNN7EXAMPLE'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
    os.environ['AWS_REGION'] = 'us-east-1'
    image = io.BytesIO()
    Image.new('RGB', (320, 240), 'navy').save(image, format='JPEG')
    data_url = 'data:image/jpeg;base64,' + base64.b64encode(image.getvalue()).decode()

    face_details = [{
        'Confidence': 99.0,
        'AgeRange': {'Low': 20, 'High': 30},
        'Gender': {'Value': 'Male', 'Confidence': 99.0},
        'Smile': {'Value': False, 'Confidence': 98.0},
        'EyesOpen': {'Value': True, 'Confidence': 99.0},
        'MouthOpen': {'Value': False, 'Confidence': 97.0},
        'Emotions': [
            {'Type': 'CONFUSED', 'Confidence': 88.0},
            {'Type': 'CALM', 'Confidence': 40.0},
            {'Type': 'HAPPY', 'Confidence': 15.0},
        ],
    }]

    with patch('boto3.client') as mock_boto:
        mock_rekognition = MagicMock()
        mock_rekognition.detect_faces.return_value = {'FaceDetails': face_details}
        mock_s3 = MagicMock()
        mock_boto.side_effect = [mock_rekognition, mock_s3]

        result = FacialEmotionAgent().detect_mood(data_url)

    assert result['source'] == 'aws_rekognition', (
        f"Expected real Rekognition path, got source={result.get('source')}"
    )
    assert result['mood'] == 'neutral'
    mock_rekognition.detect_faces.assert_called_once()

def test_history_agent_memory():
    """Test history agent in memory mode"""
    print("Testing History Agent (Memory Mode)...")

    os.environ['USE_AWS_DYNAMODB'] = 'false'

    agent = HistoryAgent()
    user_id = "test-user"

    # Add a mood entry
    mood_entry = {
        "mood": "happy",
        "intensity": 8,
        "confidence": 0.92,
        "emotions": {"happy": 0.92, "calm": 0.55}
    }

    agent.add_mood_entry(user_id, mood_entry)

    # Get history
    history = agent.get_history(user_id)
    assert len(history) == 1
    assert history[0]['mood'] == 'happy'

    # Get statistics
    stats = agent.get_statistics(user_id)
    assert stats['total_entries'] == 1
    assert 'happy' in stats['moods']

    print("[OK] Memory mode working - History operations successful")
    print(f"  Total entries: {stats['total_entries']}")
    return True

def test_history_agent_dynamodb_failure_propagates():
    """Enabled DynamoDB failures must not write to memory history."""
    print("Testing History Agent (DynamoDB failure)...")

    os.environ['USE_AWS_DYNAMODB'] = 'true'

    with patch('boto3.resource') as mock_boto:
        # Mock DynamoDB to fail
        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception("DynamoDB Error")
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto.return_value = mock_resource

        agent = HistoryAgent()
        user_id = "test-user-2"

        mood_entry = {
            "mood": "calm",
            "intensity": 6,
            "confidence": 0.88,
            "emotions": {"calm": 0.82}
        }

        with pytest.raises(Exception, match='DynamoDB Error'):
            agent.add_mood_entry(user_id, mood_entry)

        with pytest.raises(ValueError, match='invalid history response'):
            agent.get_history(user_id)

        print("[OK] DynamoDB failure propagated without memory storage")
        return True

def test_dynamo_decimal_helpers():
    """Floats must become Decimals on the way into DynamoDB and plain numbers on the way out."""
    print("Testing DynamoDB Decimal conversion helpers...")

    from agents.history_agent import _to_dynamo, _from_dynamo

    item = {
        'user_id': 'u1',
        'entry_id': 1,
        'intensity': 8,
        'confidence': 0.92,
        'emotions': {'happy': 0.92, 'calm': 0.55},
        'metadata': {'transformed': True},
    }
    encoded = _to_dynamo(item)
    assert type(encoded['entry_id']) is int            # ints pass through
    assert type(encoded['intensity']) is int           # integral values pass through
    assert isinstance(encoded['confidence'], Decimal)  # float -> Decimal
    assert isinstance(encoded['emotions']['happy'], Decimal)

    decoded = _from_dynamo(encoded)
    assert type(decoded['entry_id']) is int
    assert type(decoded['confidence']) is float
    assert decoded['metadata']['transformed'] is True

    print("[OK] Decimal conversion helpers working")
    return True

def test_history_agent_dynamodb_put_uses_decimal():
    """put_item must receive Decimal numbers so real DynamoDB accepts the write."""
    print("Testing History Agent write path (floats -> Decimal)...")

    os.environ['USE_AWS_DYNAMODB'] = 'true'
    mock_table = MagicMock()
    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table
    with patch('boto3.resource', return_value=mock_resource):
        agent = HistoryAgent()
        agent.add_mood_entry('decimal-user', {
            'mood': 'happy',
            'intensity': 8,
            'confidence': 0.92,
            'emotions': {'happy': 0.92},
        })

    assert mock_table.put_item.called
    _, kwargs = mock_table.put_item.call_args
    item = kwargs['Item']
    assert isinstance(item['confidence'], Decimal)
    assert isinstance(item['emotions']['happy'], Decimal)

    print("[OK] Write path uses Decimal for numeric attributes")
    return True

def test_history_agent_dynamodb_read_converts_decimal():
    """get_history must convert Decimal responses back to JSON-safe numbers."""
    print("Testing History Agent read path (Decimal -> int/float)...")

    os.environ['USE_AWS_DYNAMODB'] = 'true'
    item = {
        'user_id': 'read-user',
        'entry_id': Decimal(12),
        'intensity': Decimal(8),
        'confidence': Decimal('0.92'),
        'mood': 'happy',
        'timestamp': '2024-01-01T10:00:00Z',
        'emotions': {'happy': Decimal('0.92')},
    }
    mock_table = MagicMock()
    mock_table.query.return_value = {'Items': [item]}
    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table
    with patch('boto3.resource', return_value=mock_resource):
        agent = HistoryAgent()
        history = agent.get_history('read-user', limit=10)
        stats = agent.get_statistics('read-user')

    assert len(history) == 1
    assert type(history[0]['entry_id']) is int
    assert type(history[0]['confidence']) is float
    assert type(history[0]['emotions']['happy']) is float
    assert stats['total_entries'] == 1
    assert 'happy' in stats['moods']

    print("[OK] Read path returns JSON-safe numbers")
    return True

def test_user_preferences_roundtrip():
    """UserPreferences save/get should round-trip through DynamoDB."""
    print("Testing UserPreferences table round-trip...")

    os.environ['USE_AWS_DYNAMODB'] = 'true'
    captured = {}

    def fake_put(**kwargs):
        captured['item'] = kwargs['Item']

    def fake_get(**kwargs):
        item = captured.get('item')
        return {'Item': item} if item else {}

    mock_table = MagicMock()
    mock_table.put_item.side_effect = fake_put
    mock_table.get_item.side_effect = fake_get
    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table
    with patch('boto3.resource', return_value=mock_resource):
        agent = HistoryAgent()
        saved = agent.save_user_preferences('pref-user', {
            'theme': 'light',
            'notifications_enabled': False,
        })
        fetched = agent.get_user_preferences('pref-user')

    assert saved['theme'] == 'light'
    assert fetched['theme'] == 'light'
    assert fetched['notifications_enabled'] is False
    assert fetched['default_mood_time_range'] == 'week'  # default preserved

    print("[OK] UserPreferences round-trip working")
    return True

def test_mood_trends():
    """Test mood trends functionality"""
    print("Testing Mood Trends...")

    os.environ['USE_AWS_DYNAMODB'] = 'false'

    agent = HistoryAgent()
    user_id = "trends-test-user"

    # Add some test data
    test_data = [
        {"mood": "happy", "intensity": 7, "confidence": 0.85, "timestamp": "2024-01-01T10:00:00Z"},
        {"mood": "happy", "intensity": 8, "confidence": 0.90, "timestamp": "2024-01-01T14:00:00Z"},
        {"mood": "calm", "intensity": 5, "confidence": 0.75, "timestamp": "2024-01-02T09:00:00Z"},
    ]

    for entry in test_data:
        agent.add_mood_entry(user_id, entry)

    # Test weekly trends
    trends = agent.get_mood_trends(user_id, 'week')

    assert 'trends' in trends
    assert len(trends['trends']) > 0

    print("[OK] Mood trends working")
    print(f"  Found {len(trends['trends'])} time periods")
    return True

def test_no_face_valueerror_passthrough():
    """A no-face ValueError from facial analysis must NOT be wrapped into a
    RuntimeError by the orchestrator; main.py maps ValueError to HTTP 400.
    Regression test for the bogus 'Rekognition is unavailable' 503."""
    print("Testing no-face ValueError passthrough...")
    parent_dir = os.path.dirname(str(backend_dir))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from agents.orchestrator_agent import OrchestratorAgent

    agent = OrchestratorAgent()
    agent.history_agent.get_history = lambda user_id, limit=1000: []
    agent.history_agent.add_mood_entry = lambda user_id, entry: None

    with patch.object(OrchestratorAgent, 'detect_mood', side_effect=ValueError('No faces detected in the image')):
        try:
            agent.process_session('test-user', 'data:image/jpeg;base64,AAAA')
        except ValueError as exc:
            assert 'No faces detected' in str(exc)
            print("[OK] ValueError passes through unwrapped (API returns 400, not 503)")
            return True
        except Exception as exc:
            print(f"[FAIL] Expected ValueError, got {type(exc).__name__}: {exc}")
            return False
    print("[FAIL] No exception was raised")
    return False


def main():
    """Run all tests"""
    print("Starting AWS Integration Tests\n")

    tests = [
        test_aws_credentials_loaded,
        test_facial_agent_mock,
        test_facial_agent_aws_failure_propagates,
        test_history_agent_memory,
        test_history_agent_dynamodb_failure_propagates,
        test_dynamo_decimal_helpers,
        test_history_agent_dynamodb_put_uses_decimal,
        test_history_agent_dynamodb_read_converts_decimal,
        test_user_preferences_roundtrip,
        test_mood_trends,
        test_no_face_valueerror_passthrough
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
            print()
        except Exception as e:
            print(f"[ERROR] Test failed: {e}")
            failed += 1
            print()

    print("Test Results:")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Total: {passed + failed}")

    if failed == 0:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed")
        return 1

if __name__ == "__main__":
    exit(main())
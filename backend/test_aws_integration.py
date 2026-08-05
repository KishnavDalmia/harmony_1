#!/usr/bin/env python3
"""
Test script for AWS integration
"""
import os
import sys
import base64
from unittest.mock import patch, MagicMock

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.facial_agent import FacialEmotionAgent
from agents.history_agent import HistoryAgent

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

def test_facial_agent_aws_fallback():
    """Test facial agent AWS fallback"""
    print("Testing Facial Emotion Agent (AWS Fallback)...")

    # Enable AWS but mock the failure
    os.environ['USE_AWS_REKOGNITION'] = 'true'

    with patch('boto3.client') as mock_boto:
        # Mock rekognition client to fail
        mock_rekognition = MagicMock()
        mock_rekognition.detect_faces.side_effect = Exception("AWS Error")
        mock_boto.return_value = mock_rekognition

        agent = FacialEmotionAgent()
        sample_image = "sample_image_data_456"

        # Should fall back to mock
        result = agent.detect_mood(sample_image)

        assert 'source' in result
        assert result['source'] == 'mock'

        print("[OK] AWS fallback working - Fell back to mock implementation")
        return True

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

def test_history_agent_dynamodb_fallback():
    """Test history agent DynamoDB fallback"""
    print("Testing History Agent (DynamoDB Fallback)...")

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

        # Add a mood entry - should fall back to memory
        mood_entry = {
            "mood": "calm",
            "intensity": 6,
            "confidence": 0.88,
            "emotions": {"calm": 0.82}
        }

        agent.add_mood_entry(user_id, mood_entry)

        # Verify it was stored in memory
        history = agent.get_history(user_id)
        assert len(history) == 1
        assert history[0]['mood'] == 'calm'

        print("[OK] DynamoDB fallback working - Fell back to memory storage")
        return True

def test_mood_trends():
    """Test mood trends functionality"""
    print("Testing Mood Trends...")

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

def main():
    """Run all tests"""
    print("Starting AWS Integration Tests\n")

    tests = [
        test_facial_agent_mock,
        test_facial_agent_aws_fallback,
        test_history_agent_memory,
        test_history_agent_dynamodb_fallback,
        test_mood_trends
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
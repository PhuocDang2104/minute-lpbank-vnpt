"""
Test script for Model Service API
"""
import requests
from pathlib import Path

# Configuration
API_BASE = "http://localhost:7860"  # Change to your HF Space URL
AUDIO_FILE = "test_audio.wav"  # Replace with your test audio


def test_health():
    """Test health endpoint"""
    print("🔍 Testing /health...")
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")


def test_diarization(audio_path: str):
    """Test diarization endpoint"""
    print("🔍 Testing /api/diarize...")
    
    with open(audio_path, "rb") as f:
        files = {"audio_file": f}
        response = requests.post(
            f"{API_BASE}/api/diarize",
            files=files,
            timeout=60
        )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    print(f"Duration: {result['duration']:.2f}s")
    print(f"Speakers: {result['num_speakers']}")
    print(f"Segments: {len(result['segments'])}")
    
    for seg in result["segments"][:3]:  # Show first 3
        print(f"  {seg['speaker']}: {seg['start']:.2f}s - {seg['end']:.2f}s")
    print()


def test_transcription(audio_path: str):
    """Test transcription endpoint"""
    print("🔍 Testing /api/transcribe...")
    
    with open(audio_path, "rb") as f:
        files = {"audio_file": f}
        data = {
            "language": "vi",
            "with_diarization": False
        }
        response = requests.post(
            f"{API_BASE}/api/transcribe",
            files=files,
            data=data,
            timeout=120
        )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    print(f"Language: {result['language']}")
    print(f"Duration: {result['duration']:.2f}s")
    print(f"Text: {result['text'][:200]}...")
    print(f"Segments: {len(result['segments'])}\n")


def test_speaker_embedding(audio_path: str):
    """Test speaker embedding endpoint"""
    print("🔍 Testing /api/speaker-embedding...")
    
    with open(audio_path, "rb") as f:
        files = {"audio_file": f}
        response = requests.post(
            f"{API_BASE}/api/speaker-embedding",
            files=files,
            timeout=30
        )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    print(f"Dimension: {result['dimension']}")
    print(f"Duration: {result['duration']:.2f}s")
    print(f"Embedding sample: {result['embedding'][:5]}...\n")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 MeetMate Model Service API Test")
    print("=" * 60 + "\n")
    
    # Test health
    try:
        test_health()
    except Exception as e:
        print(f"❌ Health check failed: {e}\n")
        exit(1)
    
    # Check if test audio exists
    if not Path(AUDIO_FILE).exists():
        print(f"⚠️  Test audio file not found: {AUDIO_FILE}")
        print("Please provide a test audio file to continue.")
        exit(0)
    
    # Test diarization
    try:
        test_diarization(AUDIO_FILE)
    except Exception as e:
        print(f"❌ Diarization test failed: {e}\n")
    
    # Test transcription
    try:
        test_transcription(AUDIO_FILE)
    except Exception as e:
        print(f"❌ Transcription test failed: {e}\n")
    
    # Test speaker embedding
    try:
        test_speaker_embedding(AUDIO_FILE)
    except Exception as e:
        print(f"❌ Speaker embedding test failed: {e}\n")
    
    print("✅ Tests completed!")


# 🔌 Integration Guide: Model Service ↔ MeetMate Backend

Hướng dẫn tích hợp **Model Service** (HF Space) vào **MeetMate Backend**.

---

## 📋 Overview

**Model Service** cung cấp 3 endpoints chính:
1. `/api/diarize` - Speaker diarization cho Post-Meeting
2. `/api/transcribe` - Whisper transcription (reference/fallback)
3. `/api/speaker-embedding` - Speaker verification

---

## 🔧 Backend Setup

### 1. Add Environment Variable

File: `backend/.env.local` hoặc `infra/env/.env.local`

```env
# Model Service API URL (HF Space)
MEETMATE_MODELS_API=https://YOUR_USERNAME-meetmate-models.hf.space

# Timeout settings (seconds)
MODELS_API_TIMEOUT=120
```

### 2. Update Config

File: `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Model Service
    meetmate_models_api: str = ''
    models_api_timeout: int = 120
```

---

## 📦 Create Service Client

File: `backend/app/services/model_service.py`

```python
"""
Client for MeetMate Model Service (HF Space)
"""
import httpx
from typing import Optional
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


class ModelServiceClient:
    """Client for external model service"""
    
    def __init__(self):
        self.base_url = settings.meetmate_models_api.rstrip('/')
        self.timeout = settings.models_api_timeout
    
    async def diarize_audio(
        self,
        audio_path: str,
    ) -> dict:
        """
        Diarize audio file
        
        Returns:
            {
                "segments": [...],
                "num_speakers": 2,
                "duration": 60.5
            }
        """
        if not self.base_url:
            raise ValueError("MEETMATE_MODELS_API not configured")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            with open(audio_path, 'rb') as f:
                response = await client.post(
                    f"{self.base_url}/api/diarize",
                    files={"audio_file": (Path(audio_path).name, f, "audio/wav")}
                )
            
            response.raise_for_status()
            return response.json()
    
    async def transcribe_audio(
        self,
        audio_path: str,
        language: str = "vi",
        with_diarization: bool = False,
    ) -> dict:
        """
        Transcribe audio with Whisper
        
        Returns:
            {
                "text": "...",
                "segments": [...],
                "language": "vi",
                "duration": 60.5
            }
        """
        if not self.base_url:
            raise ValueError("MEETMATE_MODELS_API not configured")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            with open(audio_path, 'rb') as f:
                response = await client.post(
                    f"{self.base_url}/api/transcribe",
                    files={"audio_file": (Path(audio_path).name, f, "audio/wav")},
                    data={
                        "language": language,
                        "with_diarization": with_diarization,
                    }
                )
            
            response.raise_for_status()
            return response.json()
    
    async def extract_speaker_embedding(
        self,
        audio_path: str,
    ) -> list[float]:
        """
        Extract speaker embedding
        
        Returns:
            List of 512 floats (embedding vector)
        """
        if not self.base_url:
            raise ValueError("MEETMATE_MODELS_API not configured")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            with open(audio_path, 'rb') as f:
                response = await client.post(
                    f"{self.base_url}/api/speaker-embedding",
                    files={"audio_file": (Path(audio_path).name, f, "audio/wav")}
                )
            
            response.raise_for_status()
            result = response.json()
            return result["embedding"]


# Singleton instance
_model_service_client: Optional[ModelServiceClient] = None


def get_model_service_client() -> ModelServiceClient:
    """Get or create model service client"""
    global _model_service_client
    
    if _model_service_client is None:
        _model_service_client = ModelServiceClient()
    
    return _model_service_client
```

---

## 🎯 Use Case 1: Post-Meeting Diarization Refinement

File: `backend/app/services/post_meeting_service.py`

```python
"""
Post-Meeting service với diarization refinement
"""
from app.services.model_service import get_model_service_client
from app.models.meeting import Meeting


async def refine_post_meeting_transcript(meeting_id: str):
    """
    Refine transcript sau meeting bằng diarization model
    
    Flow:
    1. Lấy recording_url từ meeting
    2. Download audio (hoặc dùng local path nếu đã có)
    3. Gọi Model Service để diarize
    4. Merge kết quả với transcript hiện tại
    5. Update speaker labels trong DB
    """
    # Get meeting
    meeting = get_meeting_by_id(meeting_id)
    
    if not meeting.recording_url:
        raise ValueError("Meeting has no recording")
    
    # Download audio (implement theo infra của bạn)
    audio_path = await download_audio(meeting.recording_url)
    
    # Call Model Service
    model_client = get_model_service_client()
    
    try:
        result = await model_client.diarize_audio(audio_path)
        
        # Process segments
        diarization_segments = result["segments"]
        
        # Merge with existing transcripts
        await merge_diarization_with_transcripts(
            meeting_id=meeting_id,
            diarization_segments=diarization_segments
        )
        
        print(f"✓ Refined {len(diarization_segments)} speaker segments")
        
    except Exception as e:
        print(f"Diarization failed: {e}")
        # Continue without refinement
    
    finally:
        # Cleanup
        cleanup_temp_audio(audio_path)
```

---

## 🎯 Use Case 2: Whisper Reference Transcription

File: `backend/app/services/transcript_service.py`

```python
"""
Compare SmartVoice STT với Whisper
"""
from app.services.model_service import get_model_service_client


async def generate_reference_transcript(audio_path: str) -> dict:
    """
    Generate reference transcript với Whisper
    
    Dùng để:
    - Compare accuracy với SmartVoice
    - Fallback khi SmartVoice không available
    - Quality metrics calculation
    """
    model_client = get_model_service_client()
    
    try:
        result = await model_client.transcribe_audio(
            audio_path=audio_path,
            language="vi",
            with_diarization=True  # Include speakers
        )
        
        return {
            "text": result["text"],
            "segments": result["segments"],
            "source": "whisper",
            "quality_score": calculate_quality_score(result)
        }
        
    except Exception as e:
        print(f"Whisper transcription failed: {e}")
        return None


async def compare_transcription_sources(
    smartvoice_segments: list[dict],
    whisper_segments: list[dict]
) -> dict:
    """
    Compare 2 nguồn transcript
    
    Returns:
        {
            "agreement_score": 0.85,
            "differences": [...],
            "recommended_source": "smartvoice"
        }
    """
    # Implement comparison logic
    # WER (Word Error Rate), alignment, etc.
    pass
```

---

## 🎯 Use Case 3: Speaker Verification

File: `backend/app/services/speaker_verification_service.py`

```python
"""
Speaker verification service
"""
from app.services.model_service import get_model_service_client
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class SpeakerVerification:
    """Verify speaker identity across meetings"""
    
    def __init__(self):
        self.model_client = get_model_service_client()
        self.threshold = 0.75  # Cosine similarity threshold
    
    async def register_speaker(
        self,
        user_id: str,
        audio_path: str
    ) -> dict:
        """
        Register speaker profile
        
        Store embedding in user profile for future verification
        """
        embedding = await self.model_client.extract_speaker_embedding(audio_path)
        
        # Store in DB
        await store_speaker_profile(
            user_id=user_id,
            embedding=embedding
        )
        
        return {
            "user_id": user_id,
            "embedding_dimension": len(embedding),
            "registered_at": datetime.utcnow()
        }
    
    async def verify_speaker(
        self,
        audio_path: str,
        claimed_user_id: str
    ) -> dict:
        """
        Verify if audio matches claimed user
        
        Returns:
            {
                "verified": True,
                "confidence": 0.89,
                "user_id": "..."
            }
        """
        # Get test embedding
        test_embedding = await self.model_client.extract_speaker_embedding(audio_path)
        
        # Get stored profile
        stored_profile = await get_speaker_profile(claimed_user_id)
        
        if not stored_profile:
            return {"verified": False, "reason": "No profile found"}
        
        # Calculate similarity
        similarity = cosine_similarity(
            [test_embedding],
            [stored_profile["embedding"]]
        )[0][0]
        
        verified = similarity >= self.threshold
        
        return {
            "verified": verified,
            "confidence": float(similarity),
            "user_id": claimed_user_id if verified else None
        }
```

---

## 📊 Error Handling

```python
async def safe_model_service_call(func, *args, **kwargs):
    """
    Wrapper để handle errors gracefully
    """
    try:
        return await func(*args, **kwargs)
    
    except httpx.TimeoutException:
        print("Model service timeout - falling back")
        return None
    
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 503:
            print("Model service unavailable (cold start?)")
        else:
            print(f"Model service error: {e}")
        return None
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

---

## 🧪 Testing

File: `backend/tests/test_model_service.py`

```python
"""
Test model service integration
"""
import pytest
from app.services.model_service import get_model_service_client


@pytest.mark.asyncio
async def test_diarization():
    """Test diarization endpoint"""
    client = get_model_service_client()
    
    result = await client.diarize_audio("tests/resources/test.wav")
    
    assert "segments" in result
    assert "num_speakers" in result
    assert len(result["segments"]) > 0


@pytest.mark.asyncio
async def test_transcription():
    """Test transcription endpoint"""
    client = get_model_service_client()
    
    result = await client.transcribe_audio(
        "tests/resources/test.wav",
        language="vi"
    )
    
    assert "text" in result
    assert "segments" in result
    assert len(result["text"]) > 0
```

---

## 📈 Monitoring

Add to backend metrics:

```python
# Metrics to track
- model_service_calls_total
- model_service_latency_seconds
- model_service_errors_total
- model_service_cache_hit_rate

# Example with Prometheus
from prometheus_client import Counter, Histogram

model_service_calls = Counter(
    'model_service_calls_total',
    'Total calls to model service',
    ['endpoint']
)

model_service_latency = Histogram(
    'model_service_latency_seconds',
    'Model service latency',
    ['endpoint']
)
```

---

## ✅ Checklist

Deployment:
- [ ] Model Service deployed on HF Space
- [ ] `MEETMATE_MODELS_API` configured in backend
- [ ] Test connectivity from backend
- [ ] Error handling implemented
- [ ] Monitoring/logging added

Integration:
- [ ] Post-meeting diarization working
- [ ] Whisper reference transcript implemented (optional)
- [ ] Speaker verification setup (optional)

---

**Ready to integrate! 🎉**


"""
Diarization Service
Call external diarization API to identify speakers in audio
"""
import logging
import httpx
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


async def diarize_audio(
    audio_path: str | Path,
    diarization_api_url: Optional[str] = None,
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Call external diarization API to identify speakers.
    
    Args:
        audio_path: Path to audio file (WAV format)
        diarization_api_url: URL of diarization API endpoint (default: from settings)
        min_speakers: Minimum number of speakers
        max_speakers: Maximum number of speakers
        
    Returns:
        List of speaker segments with keys: speaker, start, end, confidence
        
    Raises:
        RuntimeError if API call fails
    """
    from app.core.config import get_settings
    
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Get API URL from parameter, settings, or environment
    settings = get_settings()
    api_url = diarization_api_url or settings.diarization_api_url
    if not api_url:
        import os
        api_url = os.getenv("DIARIZATION_API_URL")
    if not api_url:
        raise RuntimeError(
            "Diarization API URL not configured. "
            "Set DIARIZATION_API_URL environment variable or diarization_api_url in settings. "
            "Example: https://anhoaithai345-meetmate.hf.space/api/diarize"
        )
    
    # Read audio file as bytes
    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
    except Exception as e:
        logger.error(f"Failed to read audio file: {e}")
        raise RuntimeError(f"Failed to read audio file: {e}")
    
    # Prepare request
    files = {"audio": (audio_path.name, audio_bytes, "audio/wav")}
    data = {}
    if min_speakers is not None:
        data["min_speakers"] = min_speakers
    if max_speakers is not None:
        data["max_speakers"] = max_speakers
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
            response = await client.post(api_url, files=files, data=data)
            response.raise_for_status()
            result = response.json()
            
            # Parse response - expected format: {"segments": [{"speaker": "SPEAKER_00", "start": 0.0, "end": 5.2, "confidence": 0.9}]}
            segments = result.get("segments", [])
            if not segments:
                logger.warning("Diarization API returned empty segments")
                return []
            
            # Normalize segments format
            normalized_segments = []
            for seg in segments:
                normalized_segments.append({
                    "speaker": seg.get("speaker", "SPEAKER_00"),
                    "start": float(seg.get("start", 0.0)),
                    "end": float(seg.get("end", 0.0)),
                    "confidence": float(seg.get("confidence", 1.0)),
                })
            
            logger.info(f"Diarization completed: {len(normalized_segments)} segments")
            return normalized_segments
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Diarization API error: {e.response.status_code} - {e.response.text}")
        raise RuntimeError(f"Diarization API error: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Diarization API request failed: {e}")
        raise RuntimeError(f"Diarization API request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during diarization: {e}")
        raise RuntimeError(f"Diarization failed: {str(e)}")


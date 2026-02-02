"""
Audio Processing Service
Extract audio from video files and process audio for transcription
"""
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import wave

logger = logging.getLogger(__name__)


def extract_audio_from_video(
    video_path: str | Path,
    output_path: Optional[str | Path] = None,
    sample_rate: int = 16000,
    channels: int = 1,
) -> Path:
    """
    Extract audio from video file using ffmpeg.
    
    Args:
        video_path: Path to video file
        output_path: Optional output path for audio file. If None, creates temp file.
        sample_rate: Target sample rate (default: 16000 Hz for VNPT STT)
        channels: Number of audio channels (1 for mono, 2 for stereo)
        
    Returns:
        Path to extracted audio file (WAV format)
        
    Raises:
        RuntimeError if ffmpeg fails or video file not found
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if output_path is None:
        # Create temporary WAV file
        temp_dir = Path(tempfile.gettempdir())
        output_path = temp_dir / f"audio_{video_path.stem}.wav"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # ffmpeg command to extract audio and convert to WAV
    # -i: input file
    # -ar: audio sample rate
    # -ac: audio channels (1 = mono)
    # -f wav: output format
    # -y: overwrite output file
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-f", "wav",
        "-y",  # Overwrite output file
        str(output_path),
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"Audio extracted from {video_path} to {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg failed: {e.stderr}")
        raise RuntimeError(f"Failed to extract audio: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found. Please install ffmpeg.")


def get_audio_info(audio_path: str | Path) -> dict:
    """
    Get audio file information.
    
    Args:
        audio_path: Path to audio file (WAV format)
        
    Returns:
        dict with sample_rate, channels, duration_seconds, frames
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    try:
        with wave.open(str(audio_path), "rb") as wf:
            return {
                "sample_rate": wf.getframerate(),
                "channels": wf.getnchannels(),
                "duration_seconds": wf.getnframes() / wf.getframerate(),
                "frames": wf.getnframes(),
                "sample_width": wf.getsampwidth(),
            }
    except Exception as e:
        logger.error(f"Failed to read audio file: {e}")
        raise RuntimeError(f"Failed to read audio file: {e}")


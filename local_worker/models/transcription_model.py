"""
Whisper Transcription Model
Using OpenAI Whisper for speech-to-text
"""
import torch
import whisper
from typing import Optional


class TranscriptionModel:
    """Whisper transcription model"""
    
    def __init__(
        self,
        model_size: str = "base",  # tiny, base, small, medium, large
        device: str = None,
    ):
        """
        Initialize Whisper model
        
        Args:
            model_size: Model size (tiny/base/small/medium/large)
            device: Device to run on (cuda/cpu). Auto-detect if None.
        """
        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.device = device
        
        # Load model
        print(f"Loading Whisper {model_size} model on {device}...")
        self.model = whisper.load_model(model_size, device=device)
        
        print(f"✓ Whisper {model_size} loaded on {device}")
    
    def transcribe(
        self,
        waveform: torch.Tensor,
        sample_rate: int = 16000,
        language: Optional[str] = None,  # vi, en, or None for auto-detect
        **kwargs
    ) -> dict:
        """
        Transcribe audio
        
        Args:
            waveform: Audio tensor [1, samples]
            sample_rate: Sample rate (Whisper expects 16kHz)
            language: Language code (vi/en) or None for auto-detect
            **kwargs: Additional whisper.transcribe() arguments
        
        Returns:
            {
                "text": "Full transcription",
                "segments": [
                    {
                        "text": "Segment text",
                        "start": 0.0,
                        "end": 2.5
                    },
                    ...
                ],
                "language": "vi"
            }
        """
        # Convert to numpy for Whisper
        audio_numpy = waveform.squeeze().cpu().numpy()
        
        # Transcribe
        options = {
            "language": language,
            "task": "transcribe",  # Not translate
            "verbose": False,
            **kwargs
        }
        
        result = self.model.transcribe(audio_numpy, **options)
        
        # Format segments
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "text": seg["text"].strip(),
                "start": seg["start"],
                "end": seg["end"],
            })
        
        return {
            "text": result["text"].strip(),
            "segments": segments,
            "language": result.get("language", language or "unknown"),
        }


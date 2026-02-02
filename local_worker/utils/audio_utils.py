"""
Audio processing utilities
"""
import torch
import torchaudio
from pathlib import Path


def convert_audio_to_16khz_mono(audio_path: str) -> tuple[torch.Tensor, int]:
    """
    Load audio file and convert to 16kHz mono
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        (waveform, sample_rate) where waveform is [1, samples]
    """
    # Load audio
    waveform, sample_rate = torchaudio.load(audio_path)
    
    # Convert to mono if stereo
    if waveform.shape[0] > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)
    
    # Resample to 16kHz if needed
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(
            orig_freq=sample_rate,
            new_freq=16000,
        )
        waveform = resampler(waveform)
        sample_rate = 16000
    
    return waveform, sample_rate


def get_audio_duration(waveform: torch.Tensor, sample_rate: int) -> float:
    """Get audio duration in seconds"""
    return waveform.shape[1] / sample_rate


def normalize_audio(waveform: torch.Tensor) -> torch.Tensor:
    """Normalize audio to [-1, 1] range"""
    max_val = torch.abs(waveform).max()
    if max_val > 0:
        waveform = waveform / max_val
    return waveform


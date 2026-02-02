"""
Speaker Embedding Model
Extract speaker embeddings for verification/identification
"""
import os
import torch
from pyannote.audio import Model
from pyannote.audio.pipelines.utils import get_model


class SpeakerEmbeddingModel:
    """Extract speaker embeddings using pyannote.audio"""
    
    def __init__(
        self,
        model_name: str = "pyannote/embedding",
        device: str = None,
    ):
        """
        Initialize speaker embedding model
        
        Args:
            model_name: HuggingFace model name
            device: Device to run on (cuda/cpu). Auto-detect if None.
        """
        # Get HF token
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN environment variable is required")
        
        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.device = device
        
        # Load model
        print(f"Loading speaker embedding model {model_name} on {device}...")
        self.model = Model.from_pretrained(
            model_name,
            use_auth_token=hf_token,
        )
        
        # Move to device
        if device == "cuda":
            self.model = self.model.to(torch.device("cuda"))
        
        print(f"✓ Speaker embedding model loaded on {device}")
    
    def extract_embedding(
        self,
        waveform: torch.Tensor,
        sample_rate: int = 16000,
    ) -> torch.Tensor:
        """
        Extract speaker embedding from audio
        
        Best used with audio containing single speaker (3-10 seconds recommended)
        
        Args:
            waveform: Audio tensor [1, samples]
            sample_rate: Sample rate (default 16kHz)
        
        Returns:
            Embedding vector (typically 512-d or 768-d depending on model)
        """
        # Prepare input
        audio_dict = {
            "waveform": waveform,
            "sample_rate": sample_rate,
        }
        
        # Extract embedding
        with torch.no_grad():
            embedding = self.model(audio_dict)
        
        # Return as 1D tensor
        if embedding.dim() > 1:
            embedding = embedding.squeeze()
        
        return embedding.cpu()


"""
MeetMate Model Service - Hugging Face Space
FastAPI service cho voice diarization, transcription, và speaker embedding
"""
import os
import tempfile
from pathlib import Path
from typing import Optional

import torch
import torchaudio
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from models.diarization_model import DiarizationModel
from models.transcription_model import TranscriptionModel
from models.speaker_embedding_model import SpeakerEmbeddingModel
from utils.audio_utils import convert_audio_to_16khz_mono

# ============================================================================
# App Configuration
# ============================================================================

app = FastAPI(
    title="MeetMate Model Service",
    description="Voice diarization, transcription, and speaker embedding API",
    version="1.0.0",
    docs_url="/",  # Swagger UI at root
    redoc_url="/redoc",
)

# CORS for MeetMate backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # HF Space sẽ có domain riêng
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Models Initialization
# ============================================================================

print("🚀 Initializing models...")

# Lazy loading - models sẽ được load khi gọi endpoint đầu tiên
diarization_model: Optional[DiarizationModel] = None
transcription_model: Optional[TranscriptionModel] = None
speaker_embedding_model: Optional[SpeakerEmbeddingModel] = None


def get_diarization_model() -> DiarizationModel:
    global diarization_model
    if diarization_model is None:
        print("Loading diarization model...")
        diarization_model = DiarizationModel()
    return diarization_model


def get_transcription_model() -> TranscriptionModel:
    global transcription_model
    if transcription_model is None:
        print("Loading transcription model...")
        transcription_model = TranscriptionModel()
    return transcription_model


def get_speaker_embedding_model() -> SpeakerEmbeddingModel:
    global speaker_embedding_model
    if speaker_embedding_model is None:
        print("Loading speaker embedding model...")
        speaker_embedding_model = SpeakerEmbeddingModel()
    return speaker_embedding_model


# ============================================================================
# Request/Response Models
# ============================================================================

class DiarizationSegment(BaseModel):
    speaker: str = Field(..., description="Speaker label (SPEAKER_00, SPEAKER_01, ...)")
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    confidence: float = Field(..., description="Confidence score [0-1]")


class DiarizationResponse(BaseModel):
    segments: list[DiarizationSegment]
    num_speakers: int
    duration: float


class TranscriptionSegment(BaseModel):
    text: str
    start: float
    end: float
    speaker: Optional[str] = None  # Nếu có diarization


class TranscriptionResponse(BaseModel):
    text: str
    segments: list[TranscriptionSegment]
    language: str
    duration: float


class SpeakerEmbeddingResponse(BaseModel):
    embedding: list[float]
    dimension: int
    duration: float


class HealthResponse(BaseModel):
    status: str
    models: dict[str, bool]
    gpu_available: bool


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        models={
            "diarization": diarization_model is not None,
            "transcription": transcription_model is not None,
            "speaker_embedding": speaker_embedding_model is not None,
        },
        gpu_available=torch.cuda.is_available()
    )


@app.post("/api/diarize", response_model=DiarizationResponse)
async def diarize_audio(
    audio_file: UploadFile = File(..., description="Audio file (wav, mp3, m4a, flac)")
):
    """
    Perform speaker diarization on audio file
    
    Returns:
        - segments: List of speaker segments with timestamps
        - num_speakers: Number of detected speakers
        - duration: Audio duration in seconds
    """
    # Validate file type
    allowed_types = ["audio/wav", "audio/mpeg", "audio/mp4", "audio/x-m4a", "audio/flac"]
    if audio_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type. Allowed: {allowed_types}"
        )
    
    try:
        # Save uploaded file to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio_file.filename).suffix) as tmp:
            content = await audio_file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Convert to 16kHz mono
        waveform, sample_rate = convert_audio_to_16khz_mono(tmp_path)
        
        # Run diarization
        model = get_diarization_model()
        segments = model.diarize(waveform, sample_rate)
        
        # Cleanup
        os.unlink(tmp_path)
        
        # Calculate duration
        duration = waveform.shape[1] / sample_rate
        
        # Count unique speakers
        speakers = set(seg["speaker"] for seg in segments)
        
        return DiarizationResponse(
            segments=[DiarizationSegment(**seg) for seg in segments],
            num_speakers=len(speakers),
            duration=duration
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diarization failed: {str(e)}")


@app.post("/api/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file"),
    language: str = "vi",  # vi, en, auto
    with_diarization: bool = False,  # Có chạy diarization không?
):
    """
    Transcribe audio file with Whisper
    
    Args:
        audio_file: Audio file to transcribe
        language: Language code (vi, en, auto)
        with_diarization: Include speaker diarization
    
    Returns:
        - text: Full transcription
        - segments: List of text segments with timestamps
        - language: Detected/specified language
        - duration: Audio duration
    """
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio_file.filename).suffix) as tmp:
            content = await audio_file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Convert audio
        waveform, sample_rate = convert_audio_to_16khz_mono(tmp_path)
        
        # Run transcription
        model = get_transcription_model()
        result = model.transcribe(
            waveform,
            sample_rate,
            language=language if language != "auto" else None
        )
        
        # Optional: Add diarization
        if with_diarization:
            diarization_model = get_diarization_model()
            diarization_segments = diarization_model.diarize(waveform, sample_rate)
            
            # Merge transcription với diarization
            result["segments"] = merge_transcription_with_diarization(
                result["segments"],
                diarization_segments
            )
        
        # Cleanup
        os.unlink(tmp_path)
        
        duration = waveform.shape[1] / sample_rate
        
        return TranscriptionResponse(
            text=result["text"],
            segments=[TranscriptionSegment(**seg) for seg in result["segments"]],
            language=result.get("language", language),
            duration=duration
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/api/speaker-embedding", response_model=SpeakerEmbeddingResponse)
async def extract_speaker_embedding(
    audio_file: UploadFile = File(..., description="Audio file (single speaker recommended)")
):
    """
    Extract speaker embedding from audio
    
    Used for speaker verification/identification
    Returns 512-dimensional embedding vector
    """
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio_file.filename).suffix) as tmp:
            content = await audio_file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Convert audio
        waveform, sample_rate = convert_audio_to_16khz_mono(tmp_path)
        
        # Extract embedding
        model = get_speaker_embedding_model()
        embedding = model.extract_embedding(waveform, sample_rate)
        
        # Cleanup
        os.unlink(tmp_path)
        
        duration = waveform.shape[1] / sample_rate
        
        return SpeakerEmbeddingResponse(
            embedding=embedding.tolist(),
            dimension=len(embedding),
            duration=duration
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding extraction failed: {str(e)}")


# ============================================================================
# Helper Functions
# ============================================================================

def merge_transcription_with_diarization(
    transcription_segments: list[dict],
    diarization_segments: list[dict]
) -> list[dict]:
    """
    Merge transcription segments với diarization segments
    
    Simple overlap-based matching
    """
    merged = []
    
    for trans_seg in transcription_segments:
        trans_start = trans_seg["start"]
        trans_end = trans_seg["end"]
        
        # Find overlapping diarization segment
        best_speaker = None
        max_overlap = 0
        
        for dia_seg in diarization_segments:
            # Calculate overlap
            overlap_start = max(trans_start, dia_seg["start"])
            overlap_end = min(trans_end, dia_seg["end"])
            overlap = max(0, overlap_end - overlap_start)
            
            if overlap > max_overlap:
                max_overlap = overlap
                best_speaker = dia_seg["speaker"]
        
        merged.append({
            **trans_seg,
            "speaker": best_speaker
        })
    
    return merged


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Load models on startup (optional - comment out for lazy loading)"""
    print("🎯 MeetMate Model Service started!")
    print(f"📍 GPU Available: {torch.cuda.is_available()}")
    
    # Uncomment to preload models:
    # get_diarization_model()
    # get_transcription_model()
    # get_speaker_embedding_model()
    
    print("✅ Ready to serve requests!")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "7860"))  # HF Space default port
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # No reload in production
    )


---

title: MeetMate AI API
sdk: docker
app_port: 7860
---

Backend AI microservice for MeetMate.

# 🎙️ MeetMate Model Service

**Microservice API** cho voice diarization, transcription, và speaker embedding - deploy trên **Hugging Face Spaces**.

---

## 📦 Tổng quan

Service này cung cấp 3 model chính:

1. **Speaker Diarization** (pyannote.audio) - Phân biệt người nói
2. **Speech Transcription** (Whisper) - Chuyển giọng nói thành text
3. **Speaker Embedding** (pyannote.audio) - Trích xuất voice fingerprint

---

## 🚀 Quickstart - Local Development

### 1. Install Dependencies

```bash
pip install -r requirements_hf.txt
```

### 2. Setup Environment

```bash
# Copy example env
cp .env.example .env

# Edit .env and add your HF token
# Get token from: https://huggingface.co/settings/tokens
nano .env
```

**Accept model licenses:**
- [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
- [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

### 3. Run Server

```bash
python app.py
```

Visit: http://localhost:7860 (Swagger UI)

---

## 🧪 Testing

```bash
# Test with your audio file
python test_api.py

# Or use curl
curl -X POST "http://localhost:7860/api/diarize" \
  -F "audio_file=@test_audio.wav"
```

---

## ☁️ Deploy to Hugging Face Spaces

### Option 1: Via Web UI

1. Create Space: https://huggingface.co/new-space
2. Choose **Docker SDK**
3. Upload all files from `local_worker/`
4. Add secret: `HF_TOKEN`
5. Space auto-builds! 🎉

### Option 2: Via CLI

```bash
# Install huggingface_hub
pip install huggingface_hub

# Login
huggingface-cli login

# Create space
huggingface-cli repo create meetmate-models --type space --space_sdk docker

# Upload files
cd local_worker
git init
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/meetmate-models
git add .
git commit -m "Initial commit"
git push --force space main
```

---

## 📖 API Documentation

### 1. Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "models": {
    "diarization": true,
    "transcription": true,
    "speaker_embedding": false
  },
  "gpu_available": false
}
```

---

### 2. Speaker Diarization

```bash
POST /api/diarize
Content-Type: multipart/form-data

audio_file: <file>
```

**Response:**
```json
{
  "segments": [
    {
      "speaker": "SPEAKER_00",
      "start": 0.5,
      "end": 3.2,
      "confidence": 1.0
    }
  ],
  "num_speakers": 2,
  "duration": 10.5
}
```

---

### 3. Transcription

```bash
POST /api/transcribe
Content-Type: multipart/form-data

audio_file: <file>
language: vi  # vi, en, or auto
with_diarization: false  # true to include speakers
```

**Response:**
```json
{
  "text": "Xin chào các bạn...",
  "segments": [
    {
      "text": "Xin chào các bạn",
      "start": 0.0,
      "end": 2.5,
      "speaker": null
    }
  ],
  "language": "vi",
  "duration": 10.5
}
```

---

### 4. Speaker Embedding

```bash
POST /api/speaker-embedding
Content-Type: multipart/form-data

audio_file: <file>
```

**Response:**
```json
{
  "embedding": [0.123, -0.456, ...],
  "dimension": 512,
  "duration": 5.2
}
```

---

## 🔌 Integration với MeetMate Backend

### Backend Configuration

Add to `backend/.env`:

```env
MEETMATE_MODELS_API=https://YOUR_USERNAME-meetmate-models.hf.space
```

### Example Usage

```python
# backend/app/services/model_service.py
import httpx
from app.core.config import get_settings

settings = get_settings()


async def diarize_post_meeting_audio(audio_file_path: str) -> list[dict]:
    """
    Diarize audio file sau cuộc họp
    
    Used in Post-Meeting để refine transcripts
    """
    async with httpx.AsyncClient(timeout=120.0) as client:
        with open(audio_file_path, "rb") as f:
            response = await client.post(
                f"{settings.meetmate_models_api}/api/diarize",
                files={"audio_file": ("audio.wav", f, "audio/wav")}
            )
        
        response.raise_for_status()
        result = response.json()
        
        return result["segments"]


async def transcribe_with_whisper(audio_file_path: str) -> dict:
    """
    Transcribe audio với Whisper (reference cho Post-Meeting)
    
    So sánh với SmartVoice STT để improve accuracy
    """
    async with httpx.AsyncClient(timeout=180.0) as client:
        with open(audio_file_path, "rb") as f:
            response = await client.post(
                f"{settings.meetmate_models_api}/api/transcribe",
                files={"audio_file": ("audio.wav", f, "audio/wav")},
                data={
                    "language": "vi",
                    "with_diarization": True
                }
            )
        
        response.raise_for_status()
        return response.json()
```

---

## 📊 Performance

| Task | Model | CPU (1 min audio) | GPU T4 (1 min audio) |
|------|-------|-------------------|----------------------|
| Diarization | pyannote 3.1 | ~120s | ~12s |
| Transcription | Whisper base | ~30s | ~6s |
| Embedding | pyannote emb | <1s | <0.5s |

**Recommendations:**
- **Free Tier (CPU):** Testing only
- **GPU T4 ($0.60/hr):** Production-ready
- **Process shorter chunks:** Split long meetings into 5-10 min segments

---

## 🎯 Use Cases in MeetMate

### 1. **Post-Meeting Refinement**
- Diarize full meeting audio
- Cross-check với realtime STT
- Merge speakers thành consistent labels

### 2. **Whisper Reference**
- Transcribe sau họp với Whisper
- So sánh accuracy với SmartVoice
- Use as ground truth for quality metrics

### 3. **Speaker Verification**
- Extract embeddings từ audio samples
- Match speakers across meetings
- Build speaker profiles

---

## 🔧 Troubleshooting

### Models không load được

```
❌ Error: HF_TOKEN is required
```

**Fix:** Set `HF_TOKEN` environment variable

---

### Out of memory

```
❌ CUDA out of memory
```

**Fix:**
- Process shorter audio segments
- Use smaller Whisper model (`tiny`, `base`)
- Upgrade Space to larger GPU

---

### Slow inference on CPU

**Fix:**
- Upgrade to GPU Space
- Enable `accelerate` library
- Use quantized models

---

## 📂 Project Structure

```
local_worker/
├── app.py                   # Main FastAPI app
├── Dockerfile               # HF Space Docker config
├── requirements_hf.txt      # Dependencies
├── README.md               # This file
├── README_HF.md            # HF Space README
├── test_api.py             # Test script
├── .env.example            # Environment template
│
├── models/
│   ├── __init__.py
│   ├── diarization_model.py      # Pyannote diarization
│   ├── transcription_model.py    # Whisper
│   └── speaker_embedding_model.py # Speaker embeddings
│
└── utils/
    ├── __init__.py
    └── audio_utils.py        # Audio processing

# Legacy files (no longer used for HF Space):
├── worker.py              # Old streaming worker
├── audio_buffer.py        # Old buffer
├── api_client.py          # Old client
└── speaker_registry.py    # Old registry
```

---

## 🆘 Support

- **HF Spaces Docs:** https://huggingface.co/docs/hub/spaces
- **pyannote.audio:** https://github.com/pyannote/pyannote-audio
- **Whisper:** https://github.com/openai/whisper

---

## 📜 License

Apache 2.0

---

**Built for VNPT AI Hackathon 2025 | MeetMate Project** 🚀

=======
title: Meetmate
emoji: 👀
colorFrom: purple
colorTo: indigo
sdk: docker
pinned: false
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
>>>>>>> 4e3325fdf8225a31d45dec28174441e4ec6c0842

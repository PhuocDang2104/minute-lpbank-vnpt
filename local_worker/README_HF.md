# 🎙️ MeetMate Model Service

**Hugging Face Space** for voice diarization, transcription, and speaker embedding.

[![Open in Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-sm.svg)](https://huggingface.co/spaces/YOUR_USERNAME/meetmate-models)

---

## 🚀 Features

### 1. **Speaker Diarization** 
Who spoke when? Powered by `pyannote.audio`

**Endpoint:** `POST /api/diarize`

```bash
curl -X POST "https://YOUR_SPACE.hf.space/api/diarize" \
  -F "audio_file=@meeting.wav"
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
    },
    {
      "speaker": "SPEAKER_01",
      "start": 3.5,
      "end": 6.8,
      "confidence": 1.0
    }
  ],
  "num_speakers": 2,
  "duration": 10.5
}
```

---

### 2. **Speech Transcription**
Convert speech to text with **OpenAI Whisper**

**Endpoint:** `POST /api/transcribe`

```bash
curl -X POST "https://YOUR_SPACE.hf.space/api/transcribe" \
  -F "audio_file=@meeting.wav" \
  -F "language=vi" \
  -F "with_diarization=true"
```

**Response:**
```json
{
  "text": "Full transcription text...",
  "segments": [
    {
      "text": "Xin chào các bạn",
      "start": 0.0,
      "end": 2.5,
      "speaker": "SPEAKER_00"
    }
  ],
  "language": "vi",
  "duration": 10.5
}
```

---

### 3. **Speaker Embedding**
Extract speaker voice fingerprint for verification

**Endpoint:** `POST /api/speaker-embedding`

```bash
curl -X POST "https://YOUR_SPACE.hf.space/api/speaker-embedding" \
  -F "audio_file=@speaker.wav"
```

**Response:**
```json
{
  "embedding": [0.123, -0.456, ...],  // 512-d vector
  "dimension": 512,
  "duration": 5.2
}
```

---

## 📦 Deployment on Hugging Face Spaces

### Step 1: Create Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Choose:
   - **Space name:** `meetmate-models`
   - **License:** Apache 2.0
   - **Space SDK:** Docker
   - **Space hardware:** CPU Basic (free) or GPU (paid)

### Step 2: Upload Files

Upload these files to your Space:

```
meetmate-models/
├── app.py
├── Dockerfile
├── requirements_hf.txt
├── README.md
├── models/
│   ├── __init__.py
│   ├── diarization_model.py
│   ├── transcription_model.py
│   └── speaker_embedding_model.py
└── utils/
    ├── __init__.py
    └── audio_utils.py
```

### Step 3: Set Secrets

In Space Settings → **Repository secrets**, add:

```
HF_TOKEN=your_huggingface_read_token
```

### Step 4: Deploy

Space will auto-build and deploy! 🎉

Access your API at: `https://YOUR_USERNAME-meetmate-models.hf.space`

---

## 🧪 Testing Locally

```bash
# Install dependencies
pip install -r requirements_hf.txt

# Set environment variable
export HF_TOKEN=your_token

# Run server
python app.py
```

Visit: http://localhost:7860 (Swagger UI)

---

## 🔧 Integration with MeetMate Backend

Add to backend `.env`:

```env
MEETMATE_MODELS_API=https://YOUR_USERNAME-meetmate-models.hf.space
```

Example usage in backend:

```python
import httpx

async def diarize_audio(audio_file_path: str):
    async with httpx.AsyncClient() as client:
        with open(audio_file_path, "rb") as f:
            response = await client.post(
                f"{MEETMATE_MODELS_API}/api/diarize",
                files={"audio_file": f},
                timeout=60.0
            )
        return response.json()
```

---

## 📊 Performance

| Model | Size | Speed (CPU) | Speed (GPU) |
|-------|------|-------------|-------------|
| Diarization | 120MB | ~2x realtime | ~10x realtime |
| Whisper base | 140MB | ~5x realtime | ~20x realtime |
| Speaker Emb | 20MB | <100ms | <50ms |

---

## 🎯 Recommended Hardware

- **Free Tier (CPU Basic):** Good for testing, ~2-5x slower than realtime
- **Upgraded (GPU T4):** $0.60/hr, ~10-20x faster, production-ready

---

## 📝 API Documentation

Full interactive docs available at:
- **Swagger UI:** https://YOUR_SPACE.hf.space/
- **ReDoc:** https://YOUR_SPACE.hf.space/redoc

---

## 🆘 Troubleshooting

### Model loading fails
- Check HF_TOKEN is set correctly
- Verify you have accepted model licenses:
  - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
  - [pyannote/embedding](https://huggingface.co/pyannote/embedding)

### Out of memory
- Reduce batch size
- Upgrade to GPU Space
- Process shorter audio chunks

### Slow inference
- Use GPU Space for production
- Consider Whisper "tiny" or "base" instead of "large"

---

## 📜 License

Apache 2.0

---

## 🤝 Credits

Built for **VNPT AI Hackathon 2025 - MeetMate Project**

Powered by:
- [pyannote.audio](https://github.com/pyannote/pyannote-audio)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [Hugging Face 🤗](https://huggingface.co)


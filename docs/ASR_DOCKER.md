# MINUTE ASR (whisper.cpp) - Docker Guide

Tai lieu nay huong dan setup ASR cho tieng Viet va pipeline tao bien ban.

## Kien truc
- `asr` service: FastAPI + whisper.cpp + ffmpeg (`services/asr`)
- `backend` goi `POST /transcribe` qua `ASR_URL`
- Ket qua duoc luu vao `transcript_chunk`

## Endpoint
- `GET /health`
- `POST /transcribe` (`multipart/form-data`: `file`, `language`)
- `POST /visual-ingest` (keyframe + OCR + optional caption)

## Bien moi truong quan trong

### Backend
```env
ASR_URL=http://asr:9000
ASR_LANGUAGE=vi
```

### ASR container runtime
```env
WHISPER_MODEL=/models/ggml-base.bin
WHISPER_LANGUAGE=vi
WHISPER_THREADS=2
```

### ASR image build-time (model source)
```env
WHISPER_MODEL_URL=https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
WHISPER_MODEL_FILE=ggml-base.bin
```

## Chay nhanh

```bash
cd infra
docker compose up -d --build asr backend
curl http://localhost:9000/health
```

## Test transcribe

```bash
curl -X POST "http://localhost:9000/transcribe" \
  -F "file=@/path/to/audio.wav" \
  -F "language=vi"
```

## Nang cap do chinh xac tieng Viet

Mac dinh image dung `ggml-base.bin` (multilingual). Neu hop dai/nhieu accent:

```bash
cd infra
WHISPER_MODEL_URL=https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin \
WHISPER_MODEL_FILE=ggml-medium.bin \
docker compose build asr
docker compose up -d asr
```

## Luu y chat luong
- Luon chuan hoa audio 16kHz mono.
- Tang `WHISPER_THREADS` theo so core CPU.
- Neu transcript thieu dau cau, uu tien xu ly punctuation trong LLM stage.

## Troubleshooting
- `model not found`: kiem tra `WHISPER_MODEL`.
- ASR tra ve loi `whisper` stage: model/threads khong hop le hoac out-of-memory.
- Transcript ra sai ngon ngu: dam bao `ASR_LANGUAGE=vi` va `WHISPER_LANGUAGE=vi`.

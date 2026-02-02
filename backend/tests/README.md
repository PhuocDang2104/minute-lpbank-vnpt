# Testing Guide

## Overview

This directory contains unit tests and integration tests for the MeetMate backend.

## Test Structure

```
tests/
├── unit/              # Unit tests for services
│   ├── test_agenda_service.py
│   └── test_document_service.py
├── integration/      # Integration tests for API endpoints
│   ├── test_agenda_api.py
│   ├── test_documents_api.py
│   └── test_minutes_api.py
├── conftest.py       # Pytest fixtures
└── __init__.py
```

## Running Tests

### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/unit/test_agenda_service.py
pytest tests/integration/test_agenda_api.py
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run with Verbose Output

```bash
pytest -v
```

## Google Meet → MeetMate bridge (SmartVoice)

Script: `backend/tests/gmeet_bridge_ingest.py`

What it does:
- Creates a MeetMate realtime session (`POST /api/v1/sessions`) and fetches `audio_ingest_token`.
- Opens WS `/api/v1/ws/audio/{session_id}?token=...&stt=1` to stream audio into backend → SmartVoice.
- Audio source:
  - Real Google Meet Media API: implement in `_gmeet_audio_frames` (recv-only PCM16 16k mono).
  - Fallback (dev/demo): set `BRIDGE_WAV_PATH` to a local WAV/MP3; it streams as if from Meet.

Env:
- `MEET_URL` (required): Google Meet link.
- `MEETMATE_HTTP_BASE`: e.g., `https://vnpt-ai-hackathon-meetmate.onrender.com`
- `MEETMATE_LANGUAGE_CODE`: default `vi-VN`
- `MEETMATE_FRAME_MS`: default `250`
- `MEETMATE_TARGET_SR`: default `16000`
- `MEETMATE_SESSION_ID`: optional fixed session id
- `MEETMATE_STT`: `1` to force STT
- `BRIDGE_WAV_PATH`: optional, to use local audio instead of Meet stream.

Run (fallback WAV demo):
```powershell
cd backend/tests
$env:MEET_URL="https://meet.google.com/your-link"
$env:BRIDGE_WAV_PATH="C:\Users\ADMIN\Desktop\vnpt_meetmate\vnpt_ai_hackathon\backend\tests\resources\Chapter-1-Conversation-2.mp3"
python gmeet_bridge_ingest.py
```

To go live with Google Meet Media API:
- Replace `_gmeet_audio_frames` with actual SDK code that yields 250ms PCM16 mono 16k frames.
- Keep the start message schema and frame size unchanged.

## Test Categories

### Unit Tests

Test individual service functions in isolation:
- `test_agenda_service.py` - Agenda service CRUD operations
- `test_document_service.py` - Document service CRUD operations

### Integration Tests

Test API endpoints end-to-end:
- `test_agenda_api.py` - Agenda API endpoints
- `test_documents_api.py` - Documents API endpoints
- `test_minutes_api.py` - Minutes API endpoints

## Notes

- Services using in-memory storage (documents, agenda) use mock database sessions
- Integration tests use FastAPI TestClient for HTTP testing
- Some tests may fail if external services (Gemini AI) are unavailable - this is expected

## Writing New Tests

1. Create test file in appropriate directory (`unit/` or `integration/`)
2. Use fixtures from `conftest.py`
3. Follow naming convention: `test_*.py` for files, `test_*` for functions
4. Use `@pytest.mark.asyncio` for async tests


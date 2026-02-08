# In-Meeting Video Capture API Handoff

Tai lieu nay dung de ban giao cho team in-meeting tich hop luong xu ly video capture vao MINUTE backend + ASR service.

## 1. Scope

Muc tieu:
- Nhan video recording tu in-meeting.
- Trich xuat transcript (audio -> ASR).
- Trich xuat visual context (keyframe + OCR + object heuristic).
- Luu vao DB de RAG chat/minutes su dung theo meeting session.

Ket qua du lieu:
- `transcript_chunk` (noi dung noi, timecode)
- `visual_event` (moc frame quan trong + OCR/description)
- `visual_object_event` (doi tuong/nhan dien theo timestamp)

## 2. End-to-End Flow

1. In-meeting upload file video vao backend endpoint `POST /api/v1/meetings/{meeting_id}/upload-video`.
2. Backend luu file vao storage (Supabase S3) hoac local fallback.
3. In-meeting goi `POST /api/v1/meetings/{meeting_id}/trigger-inference`.
4. Backend goi ASR service:
- `POST /visual-ingest` de lay keyframe + OCR + object.
- `POST /transcribe` de lay transcript tu audio.
5. Backend persist visual + transcript vao DB.
6. Minutes/RAG chat query context theo meeting session.

## 3. Public API for In-Meeting Team (backend)

### 3.1 Upload recording

Endpoint:
- `POST /api/v1/meetings/{meeting_id}/upload-video`

Request:
- `multipart/form-data`
- Field `video`: file (`mp4`, `mov`, `avi`, `webm`, `mkv`)
- Field `uploaded_by` (optional): UUID string

Example:
```bash
curl -X POST "https://minute-api.onrender.com/api/v1/meetings/<meeting_id>/upload-video" \
  -F "video=@/path/to/meeting.mp4" \
  -F "uploaded_by=00000000-0000-0000-0000-000000000001"
```

Response (200):
```json
{
  "recording_id": "uuid",
  "recording_url": "https://..." ,
  "message": "Video uploaded successfully",
  "file_size": 12345678,
  "storage_key": "videos/<meeting_id>/...",
  "provider": "supabase"
}
```

### 3.2 Trigger inference (transcript + visual capture)

Endpoint:
- `POST /api/v1/meetings/{meeting_id}/trigger-inference`
- Query `template_id` (optional)

Example:
```bash
curl -X POST "https://minute-api.onrender.com/api/v1/meetings/<meeting_id>/trigger-inference"
```

Response (200):
```json
{
  "status": "completed",
  "message": "Video processing completed successfully",
  "transcript_count": 120,
  "visual_event_count": 42,
  "visual_object_count": 75,
  "minutes_id": "uuid-or-null",
  "pdf_url": "url-or-null"
}
```

## 4. Internal ASR API Contract (backend -> ASR)

Luu y:
- Endpoint nay la internal/service-to-service.
- Khuyen nghi in-meeting team KHONG goi truc tiep, ma di qua backend `trigger-inference`.

### 4.1 Visual ingest

Endpoint:
- `POST /visual-ingest`

Request:
- `multipart/form-data`
- `file`: video file
- `meeting_id` (optional): string
- `scene_threshold` (optional, default `0.35`): float `(0,1)`
- `max_keyframes` (optional, default `60`): int, max 200
- `run_ocr` (optional, default `true`): bool
- `run_caption` (optional, default `false`): bool (vision caption)

Example:
```bash
curl -X POST "https://<asr-host>/visual-ingest" \
  -F "file=@/path/to/meeting.mp4" \
  -F "meeting_id=<meeting_id>" \
  -F "scene_threshold=0.35" \
  -F "max_keyframes=60" \
  -F "run_ocr=true" \
  -F "run_caption=false"
```

Response:
```json
{
  "meeting_id": "...",
  "total_keyframes": 42,
  "settings": {
    "scene_threshold": 0.35,
    "max_keyframes": 60,
    "run_ocr": true,
    "run_caption": false
  },
  "visual_events": [
    {
      "frame_index": 1,
      "timestamp": 12.340,
      "event_type": "slide_change",
      "description": "",
      "ocr_text": "Sprint plan Q2...",
      "image_name": "key_00001.jpg"
    }
  ],
  "visual_objects": [
    {
      "timestamp": 12.340,
      "object_label": "table",
      "confidence": 0.6,
      "ocr_text": "Sprint plan Q2...",
      "source": "heuristic"
    }
  ]
}
```

### 4.2 Audio transcription

Endpoint:
- `POST /transcribe`

Request:
- `multipart/form-data`
- `file`: audio/video file

Response:
- JSON whisper output (segments/transcription/text)

## 5. DB Mapping (sau inference)

Backend luu ket qua visual vao:

### 5.1 `visual_event`
- `id`
- `meeting_id`
- `timestamp`
- `image_url` (hien luu image name tu ASR)
- `description`
- `ocr_text`
- `event_type`
- `created_at`, `updated_at`

### 5.2 `visual_object_event`
- `id`
- `meeting_id`
- `visual_event_id` (gan event gan nhat theo timestamp)
- `timestamp`
- `object_label`
- `confidence`
- `ocr_text`
- `source`
- `frame_url` (neu co)
- `created_at`, `updated_at`

## 6. Config Required

### 6.1 Backend env
- `ASR_URL` (vi du: `https://<space>.hf.space`)
- `MAX_VIDEO_FILE_SIZE_MB` (default 100)
- Storage env (Supabase S3) neu muon luu cloud

### 6.2 ASR env
- `WHISPER_MODEL`
- `WHISPER_BIN`
- `FFMPEG_BIN`
- `WHISPER_THREADS`
- `SCENE_THRESHOLD`
- `MAX_KEYFRAMES`
- `FALLBACK_FRAME_STEP_SEC`
- `OCR_BIN` (default `tesseract`)
- `OCR_ENABLED`
- `LLM_VISION_PROVIDER` (optional, default `gemini`)
- `LLM_VISION_API_KEY` (optional)
- `LLM_VISION_MODEL` (optional)
- Alias cu van ho tro: `GEMINI_VISION_API_KEY`, `GEMINI_VISION_MODEL`

Runtime dependency quan trong:
- `ffmpeg`
- `tesseract-ocr`

## 7. Resource Guidance (Render free / MVP)

De on dinh voi 512MB RAM, 0.1 CPU:
- `run_caption=false` (de tat vision caption).
- `max_keyframes` de `20-60`.
- Khuyen nghi preprocess video 720p, duration ngan.
- Khong chay dong thoi qua nhieu request inference.

## 8. Error Handling Contract

Backend `trigger-inference` co the tra 500 neu:
- Video khong ton tai/khong doc duoc.
- DB schema chua migrate du (`visual_event`, `visual_object_event`, `knowledge_chunk`, ...).
- ASR service timeout/SSL/domain sai.

Khuyen nghi client in-meeting:
- Retry toi da 2 lan voi backoff (2s, 5s).
- Hien thi loi chi tiet tu `detail` neu backend tra ve.
- Neu `visual_event_count=0` nhung `transcript_count>0` thi cho phep tiep tuc luong transcript-only.

## 9. Handoff Test Checklist

1. Upload video thanh cong (`upload-video` tra `recording_url`).
2. Trigger inference thanh cong (`status=completed`).
3. `transcript_count > 0`.
4. `visual_event_count > 0` cho video co thay doi frame/slide.
5. DB co ban ghi:
- `SELECT COUNT(*) FROM visual_event WHERE meeting_id = '<meeting_id>';`
- `SELECT COUNT(*) FROM visual_object_event WHERE meeting_id = '<meeting_id>';`
6. Chat RAG hoi ve noi dung slide/visual co the tra loi theo context.

## 10. Related Source Files

- `backend/app/api/v1/endpoints/meetings.py`
- `backend/app/services/video_inference_service.py`
- `backend/app/services/asr_service.py`
- `services/asr/app/main.py`
- `services/asr/Dockerfile`
- `backend/app/services/knowledge_service.py`

## 11. Practical Test Runbook (copy-paste)

Muc tieu:
- Team in-meeting co the test end-to-end khong can doc code.
- Xac nhan du lieu transcript + visual context duoc persist va dung duoc cho RAG/minutes.

### 11.1 Chuan bi bien moi truong

```bash
export API_BASE="https://minute-api.onrender.com"
export ASR_BASE="https://<your-asr-host>" # optional, chi dung neu test truc tiep ASR
export MEETING_ID="<meeting_uuid>"
export VIDEO_PATH="/absolute/path/to/test_meeting.mp4"
```

Luu y:
- `MEETING_ID` phai ton tai trong bang `meeting`.
- Video nen co slide change ro rang de de thay `visual_event_count > 0`.

### 11.2 Health check nhanh

```bash
curl -sS "$API_BASE/health" | jq .
curl -sS "$ASR_BASE/health" | jq .   # neu test ASR truc tiep
```

Expected:
- API backend tra `ok/healthy`.
- ASR tra `{ "ok": true }`.

### 11.3 Upload video vao meeting

```bash
curl -sS -X POST "$API_BASE/api/v1/meetings/$MEETING_ID/upload-video" \
  -F "video=@$VIDEO_PATH" \
  -F "uploaded_by=00000000-0000-0000-0000-000000000001" | jq .
```

Expected:
- HTTP `200`
- JSON co `recording_id`, `recording_url`, `provider`, `file_size`.

### 11.4 Trigger inference

```bash
curl -sS -X POST "$API_BASE/api/v1/meetings/$MEETING_ID/trigger-inference" | jq .
```

Expected:
- `status = "completed"`
- `transcript_count > 0`
- `visual_event_count >= 0`
- `visual_object_count >= 0`

Neu video co slide/change frame:
- `visual_event_count > 0` la ky vong chinh.

### 11.5 Verify transcript + visual bang API

Transcript:
```bash
curl -sS "$API_BASE/api/v1/transcripts/$MEETING_ID?limit=20" | jq '.total, .chunks[0]'
```

Minutes latest:
```bash
curl -sS "$API_BASE/api/v1/minutes/$MEETING_ID/latest" | jq .
```

Expected:
- Transcript list co du lieu.
- Minutes co the co/no tuy flow generate, nhung endpoint phai tra json hop le.

### 11.6 Verify du lieu bang SQL (DB cloud)

```sql
SELECT COUNT(*) AS transcript_chunks
FROM transcript_chunk
WHERE meeting_id = '<meeting_id>';

SELECT COUNT(*) AS visual_events
FROM visual_event
WHERE meeting_id = '<meeting_id>';

SELECT COUNT(*) AS visual_objects
FROM visual_object_event
WHERE meeting_id = '<meeting_id>';
```

Expected:
- `transcript_chunks > 0`
- `visual_events >= 0`
- `visual_objects >= 0`

### 11.7 Verify tren UI

Checklist:
1. Mo meeting session tren frontend.
2. Transcript panel co noi dung moi.
3. Chat hoi ve noi dung vua noi trong video -> AI tra loi dung context.
4. Neu co visual events: hoi ve slide/chart -> AI co citation/noi dung lien quan.

### 11.8 Test matrix toi thieu

1. Video ngan (1-3 phut), co slide change.
2. Video ngan, khong slide (speaker cam).
3. Video chi audio (man hinh it thay doi).
4. Video co text tren slide (de OCR bat duoc).

### 11.9 Failure playbook nhanh

1. `upload-video` fail:
- Check `MAX_VIDEO_FILE_SIZE_MB`.
- Check storage env (Supabase S3/public URL).

2. `trigger-inference` fail 500:
- Check `ASR_URL` dung domain + SSL.
- Check ASR logs (`/transcribe` hoac `/visual-ingest` fail stage nao).
- Check DB schema da migrate du.

3. `transcript_count > 0` nhung visual = 0:
- Video it thay doi frame.
- Thu giam `scene_threshold` (vd `0.25`) va tang `max_keyframes`.

4. UI khong thay du lieu:
- Hard refresh frontend.
- Verify API response truoc (khong debug UI khi API dang rong).

### 11.10 Optional: Test truc tiep ASR service

Visual ingest:
```bash
curl -sS -X POST "$ASR_BASE/visual-ingest" \
  -F "file=@$VIDEO_PATH" \
  -F "meeting_id=$MEETING_ID" \
  -F "scene_threshold=0.35" \
  -F "max_keyframes=60" \
  -F "run_ocr=true" \
  -F "run_caption=false" | jq '.total_keyframes, .visual_events[0], .visual_objects[0]'
```

Transcribe:
```bash
curl -sS -X POST "$ASR_BASE/transcribe" \
  -F "file=@$VIDEO_PATH" | jq '.text, .segments[0]'
```

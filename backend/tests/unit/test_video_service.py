import io
from types import SimpleNamespace

import pytest
from starlette.datastructures import Headers, UploadFile

from app.services import video_service


class _FakeResult:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


@pytest.mark.asyncio
async def test_upload_video_still_succeeds_when_meeting_recording_table_missing(monkeypatch):
    meeting_id = "7d8f9a3f-7dad-46d2-a48f-bd3baeb5ad90"

    monkeypatch.setattr(
        video_service.meeting_service,
        "get_meeting",
        lambda db, mid: SimpleNamespace(id=mid) if mid == meeting_id else None,
    )
    monkeypatch.setattr(video_service, "is_storage_configured", lambda: True)
    monkeypatch.setattr(video_service, "build_object_key", lambda filename, prefix: f"{prefix}/demo.mp4")
    monkeypatch.setattr(video_service, "upload_bytes_to_storage", lambda data, key, content_type=None: key)
    monkeypatch.setattr(
        video_service,
        "generate_presigned_get_url",
        lambda key, expires_in=3600: f"https://cdn.example.com/{key}",
    )

    class FakeDb:
        def __init__(self):
            self.commit_count = 0
            self.rollback_count = 0

        def execute(self, stmt, params=None):
            sql = str(stmt)
            if "UPDATE meeting" in sql:
                return _FakeResult(("ok",))
            if "INSERT INTO meeting_recording" in sql:
                raise Exception('relation "meeting_recording" does not exist')
            raise AssertionError(f"Unexpected SQL: {sql}")

        def commit(self):
            self.commit_count += 1

        def rollback(self):
            self.rollback_count += 1

    db = FakeDb()
    upload_file = UploadFile(
        file=io.BytesIO(b"fake-video-bytes"),
        filename="demo.mp4",
        headers=Headers({"content-type": "video/mp4"}),
    )

    result = await video_service.upload_meeting_video(
        db=db,
        meeting_id=meeting_id,
        file=upload_file,
        uploaded_by=None,
    )

    assert result["recording_url"] == "https://cdn.example.com/videos/7d8f9a3f-7dad-46d2-a48f-bd3baeb5ad90/demo.mp4"
    assert result["provider"] == "supabase"
    assert result["metadata_persisted"] is False
    assert db.commit_count == 1
    assert db.rollback_count == 1

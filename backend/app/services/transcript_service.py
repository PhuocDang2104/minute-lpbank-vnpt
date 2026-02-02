"""
Transcript Service
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.transcript import (
    TranscriptChunkCreate, TranscriptChunkUpdate, 
    TranscriptChunkResponse, TranscriptChunkList,
    LiveRecapSnapshot
)


def list_transcript_chunks(
    db: Session, 
    meeting_id: str,
    from_index: Optional[int] = None,
    to_index: Optional[int] = None,
    limit: int = 100
) -> TranscriptChunkList:
    """List transcript chunks for a meeting"""
    
    conditions = ["meeting_id = :meeting_id"]
    params = {'meeting_id': meeting_id, 'limit': limit}
    
    if from_index is not None:
        conditions.append("chunk_index >= :from_index")
        params['from_index'] = from_index
    if to_index is not None:
        conditions.append("chunk_index <= :to_index")
        params['to_index'] = to_index
    
    where_clause = " AND ".join(conditions)
    
    query = text(f"""
        SELECT 
            tc.id::text, tc.meeting_id::text, tc.chunk_index,
            COALESCE(tc.start_time, tc.time_start, 0.0) as start_time,
            COALESCE(tc.end_time, tc.time_end, 0.0) as end_time,
            tc.speaker,
            tc.speaker_user_id::text, tc.text, tc.confidence,
            COALESCE(tc.language, tc.lang, 'vi') as language, tc.created_at,
            u.display_name as speaker_name
        FROM transcript_chunk tc
        LEFT JOIN user_account u ON tc.speaker_user_id = u.id
        WHERE {where_clause}
        ORDER BY tc.chunk_index ASC
        LIMIT :limit
    """)
    
    result = db.execute(query, params)
    rows = result.fetchall()
    
    chunks = []
    for row in rows:
        chunks.append(TranscriptChunkResponse(
            id=row[0],
            meeting_id=row[1],
            chunk_index=row[2],
            start_time=row[3],
            end_time=row[4],
            speaker=row[5],
            speaker_user_id=row[6],
            text=row[7],
            confidence=row[8],
            language=row[9],
            created_at=row[10],
            speaker_name=row[11]
        ))
    
    return TranscriptChunkList(chunks=chunks, total=len(chunks))


def get_full_transcript(db: Session, meeting_id: str) -> str:
    """Get full transcript text for a meeting"""
    query = text("""
        SELECT speaker, text
        FROM transcript_chunk
        WHERE meeting_id = :meeting_id
        ORDER BY chunk_index ASC
    """)
    
    result = db.execute(query, {'meeting_id': meeting_id})
    rows = result.fetchall()
    
    transcript_lines = []
    for row in rows:
        speaker = row[0] or "Unknown"
        text_content = row[1]
        transcript_lines.append(f"[{speaker}]: {text_content}")
    
    return "\n".join(transcript_lines)


def create_transcript_chunk(db: Session, data: TranscriptChunkCreate) -> TranscriptChunkResponse:
    """Create a new transcript chunk"""
    chunk_id = str(uuid4())
    now = datetime.utcnow()
    
    # Insert into primary columns (start_time, end_time, language)
    # Database may also have time_start, time_end, lang, is_final columns
    # We'll use the primary columns and let the database handle defaults if needed
    query = text("""
        INSERT INTO transcript_chunk (
            id, meeting_id, chunk_index, start_time, end_time,
            speaker, speaker_user_id, text, confidence, language, created_at
        )
        VALUES (
            :id, :meeting_id, :chunk_index, :start_time, :end_time,
            :speaker, :speaker_user_id, :text, :confidence, :language, :created_at
        )
        RETURNING id::text
    """)
    
    db.execute(query, {
        'id': chunk_id,
        'meeting_id': data.meeting_id,
        'chunk_index': data.chunk_index,
        'start_time': data.start_time,
        'end_time': data.end_time,
        'speaker': data.speaker,
        'speaker_user_id': data.speaker_user_id,
        'text': data.text,
        'confidence': data.confidence,
        'language': data.language,
        'created_at': now
    })
    db.commit()
    
    return TranscriptChunkResponse(
        id=chunk_id,
        meeting_id=data.meeting_id,
        chunk_index=data.chunk_index,
        start_time=data.start_time,
        end_time=data.end_time,
        speaker=data.speaker,
        speaker_user_id=data.speaker_user_id,
        text=data.text,
        confidence=data.confidence,
        language=data.language,
        created_at=now
    )


def create_batch_transcript_chunks(
    db: Session, 
    meeting_id: str, 
    chunks: List[TranscriptChunkCreate]
) -> TranscriptChunkList:
    """Create multiple transcript chunks at once"""
    created_chunks = []
    
    for chunk in chunks:
        chunk.meeting_id = meeting_id
        created_chunk = create_transcript_chunk(db, chunk)
        created_chunks.append(created_chunk)
    
    return TranscriptChunkList(chunks=created_chunks, total=len(created_chunks))


def update_transcript_chunk(
    db: Session, 
    chunk_id: str, 
    data: TranscriptChunkUpdate
) -> Optional[TranscriptChunkResponse]:
    """Update a transcript chunk"""
    updates = []
    params = {'chunk_id': chunk_id}
    
    if data.text is not None:
        updates.append("text = :text")
        params['text'] = data.text
    if data.speaker is not None:
        updates.append("speaker = :speaker")
        params['speaker'] = data.speaker
    if data.speaker_user_id is not None:
        updates.append("speaker_user_id = :speaker_user_id")
        params['speaker_user_id'] = data.speaker_user_id
    
    if not updates:
        return None
    
    query = text(f"""
        UPDATE transcript_chunk
        SET {', '.join(updates)}
        WHERE id = :chunk_id
        RETURNING id::text, meeting_id::text, chunk_index,
            COALESCE(start_time, time_start, 0.0) as start_time,
            COALESCE(end_time, time_end, 0.0) as end_time,
            speaker, speaker_user_id::text,
            text, confidence,
            COALESCE(language, lang, 'vi') as language, created_at
    """)
    
    result = db.execute(query, params)
    db.commit()
    row = result.fetchone()
    
    if not row:
        return None
    
    return TranscriptChunkResponse(
        id=row[0],
        meeting_id=row[1],
        chunk_index=row[2],
        start_time=row[3],
        end_time=row[4],
        speaker=row[5],
        speaker_user_id=row[6],
        text=row[7],
        confidence=row[8],
        language=row[9],
        created_at=row[10]
    )


def delete_transcript_chunks(db: Session, meeting_id: str) -> int:
    """Delete all transcript chunks for a meeting"""
    query = text("""
        DELETE FROM transcript_chunk 
        WHERE meeting_id = :meeting_id
        RETURNING id
    """)
    
    result = db.execute(query, {'meeting_id': meeting_id})
    db.commit()
    
    return len(result.fetchall())


# ============================================
# Live Recap
# ============================================

def get_live_recap(db: Session, meeting_id: str) -> Optional[LiveRecapSnapshot]:
    """Get the latest live recap for a meeting"""
    query = text("""
        SELECT id::text, meeting_id::text, snapshot_time, summary, 
            key_points, created_at
        FROM live_recap_snapshot
        WHERE meeting_id = :meeting_id
        ORDER BY snapshot_time DESC
        LIMIT 1
    """)
    
    result = db.execute(query, {'meeting_id': meeting_id})
    row = result.fetchone()
    
    if not row:
        return None
    
    return LiveRecapSnapshot(
        id=row[0],
        meeting_id=row[1],
        snapshot_time=row[2],
        summary=row[3],
        key_points=row[4],
        created_at=row[5]
    )


def create_live_recap(
    db: Session, 
    meeting_id: str, 
    summary: str, 
    key_points: Optional[List[str]] = None
) -> LiveRecapSnapshot:
    """Create a new live recap snapshot"""
    recap_id = str(uuid4())
    now = datetime.utcnow()
    
    import json
    
    query = text("""
        INSERT INTO live_recap_snapshot (
            id, meeting_id, snapshot_time, summary, key_points, created_at
        )
        VALUES (
            :id, :meeting_id, :snapshot_time, :summary, :key_points, :created_at
        )
        RETURNING id::text
    """)
    
    db.execute(query, {
        'id': recap_id,
        'meeting_id': meeting_id,
        'snapshot_time': now,
        'summary': summary,
        'key_points': json.dumps(key_points) if key_points else None,
        'created_at': now
    })
    db.commit()
    
    return LiveRecapSnapshot(
        id=recap_id,
        meeting_id=meeting_id,
        snapshot_time=now,
        summary=summary,
        key_points=key_points,
        created_at=now
    )


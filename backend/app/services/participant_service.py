"""
Meeting Participant Service
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.participant import (
    ParticipantAdd, ParticipantUpdate,
    ParticipantResponse, ParticipantList
)


def list_participants(db: Session, meeting_id: str) -> ParticipantList:
    """List all participants for a meeting"""
    query = text("""
        SELECT 
            mp.meeting_id::text, mp.user_id::text, mp.role,
            mp.response_status, mp.attended, mp.joined_at, mp.left_at,
            u.display_name as user_name, u.email as user_email, u.avatar_url as user_avatar
        FROM meeting_participant mp
        JOIN user_account u ON mp.user_id = u.id
        WHERE mp.meeting_id = :meeting_id
        ORDER BY 
            CASE mp.role 
                WHEN 'organizer' THEN 1 
                WHEN 'required' THEN 2 
                WHEN 'optional' THEN 3 
                ELSE 4 
            END,
            u.display_name
    """)
    
    result = db.execute(query, {'meeting_id': meeting_id})
    rows = result.fetchall()
    
    participants = []
    for row in rows:
        participants.append(ParticipantResponse(
            meeting_id=row[0],
            user_id=row[1],
            role=row[2],
            response_status=row[3],
            attended=row[4] or False,
            joined_at=row[5],
            left_at=row[6],
            user_name=row[7],
            user_email=row[8],
            user_avatar=row[9]
        ))
    
    return ParticipantList(participants=participants, total=len(participants))


def add_participant(db: Session, meeting_id: str, data: ParticipantAdd) -> Optional[ParticipantResponse]:
    """Add a participant to a meeting"""
    # Check if participant already exists
    check_query = text("""
        SELECT 1 FROM meeting_participant 
        WHERE meeting_id = :meeting_id AND user_id = :user_id
    """)
    existing = db.execute(check_query, {
        'meeting_id': meeting_id, 
        'user_id': data.user_id
    }).fetchone()
    
    if existing:
        # Update existing participant
        return update_participant(db, meeting_id, data.user_id, ParticipantUpdate(
            role=data.role,
            response_status=data.response_status
        ))
    
    # Insert new participant
    query = text("""
        INSERT INTO meeting_participant (meeting_id, user_id, role, response_status)
        VALUES (:meeting_id, :user_id, :role, :response_status)
        RETURNING meeting_id::text, user_id::text
    """)
    
    db.execute(query, {
        'meeting_id': meeting_id,
        'user_id': data.user_id,
        'role': data.role,
        'response_status': data.response_status
    })
    db.commit()
    
    # Get full participant info
    return get_participant(db, meeting_id, data.user_id)


def get_participant(db: Session, meeting_id: str, user_id: str) -> Optional[ParticipantResponse]:
    """Get a specific participant"""
    query = text("""
        SELECT 
            mp.meeting_id::text, mp.user_id::text, mp.role,
            mp.response_status, mp.attended, mp.joined_at, mp.left_at,
            u.display_name as user_name, u.email as user_email, u.avatar_url as user_avatar
        FROM meeting_participant mp
        JOIN user_account u ON mp.user_id = u.id
        WHERE mp.meeting_id = :meeting_id AND mp.user_id = :user_id
    """)
    
    result = db.execute(query, {'meeting_id': meeting_id, 'user_id': user_id})
    row = result.fetchone()
    
    if not row:
        return None
    
    return ParticipantResponse(
        meeting_id=row[0],
        user_id=row[1],
        role=row[2],
        response_status=row[3],
        attended=row[4] or False,
        joined_at=row[5],
        left_at=row[6],
        user_name=row[7],
        user_email=row[8],
        user_avatar=row[9]
    )


def update_participant(
    db: Session, 
    meeting_id: str, 
    user_id: str, 
    data: ParticipantUpdate
) -> Optional[ParticipantResponse]:
    """Update a participant"""
    updates = []
    params = {'meeting_id': meeting_id, 'user_id': user_id}
    
    if data.role is not None:
        updates.append("role = :role")
        params['role'] = data.role
    if data.response_status is not None:
        updates.append("response_status = :response_status")
        params['response_status'] = data.response_status
    if data.attended is not None:
        updates.append("attended = :attended")
        params['attended'] = data.attended
    
    if not updates:
        return get_participant(db, meeting_id, user_id)
    
    query = text(f"""
        UPDATE meeting_participant
        SET {', '.join(updates)}
        WHERE meeting_id = :meeting_id AND user_id = :user_id
        RETURNING meeting_id::text, user_id::text
    """)
    
    result = db.execute(query, params)
    db.commit()
    
    if not result.fetchone():
        return None
    
    return get_participant(db, meeting_id, user_id)


def remove_participant(db: Session, meeting_id: str, user_id: str) -> bool:
    """Remove a participant from a meeting"""
    query = text("""
        DELETE FROM meeting_participant 
        WHERE meeting_id = :meeting_id AND user_id = :user_id
        RETURNING meeting_id
    """)
    
    result = db.execute(query, {'meeting_id': meeting_id, 'user_id': user_id})
    db.commit()
    
    return result.fetchone() is not None


def mark_attendance(
    db: Session, 
    meeting_id: str, 
    user_id: str, 
    attended: bool = True,
    joined_at: Optional[datetime] = None,
    left_at: Optional[datetime] = None
) -> Optional[ParticipantResponse]:
    """Mark attendance for a participant"""
    updates = ["attended = :attended"]
    params = {
        'meeting_id': meeting_id, 
        'user_id': user_id, 
        'attended': attended
    }
    
    if joined_at:
        updates.append("joined_at = :joined_at")
        params['joined_at'] = joined_at
    
    if left_at:
        updates.append("left_at = :left_at")
        params['left_at'] = left_at
    
    query = text(f"""
        UPDATE meeting_participant
        SET {', '.join(updates)}
        WHERE meeting_id = :meeting_id AND user_id = :user_id
        RETURNING meeting_id::text
    """)
    
    result = db.execute(query, params)
    db.commit()
    
    if not result.fetchone():
        return None
    
    return get_participant(db, meeting_id, user_id)


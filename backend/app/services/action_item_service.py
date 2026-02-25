"""
Action Item, Decision, Risk Services
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.action_item import (
    ActionItemCreate, ActionItemUpdate, ActionItemResponse, ActionItemList,
    DecisionItemCreate, DecisionItemUpdate, DecisionItemResponse, DecisionItemList,
    RiskItemCreate, RiskItemUpdate, RiskItemResponse, RiskItemList,
)


# ============================================
# ACTION ITEM CRUD
# ============================================

def list_all_action_items(
    db: Session, 
    status: Optional[str] = None,
    priority: Optional[str] = None,
    owner_user_id: Optional[str] = None,
    overdue_only: bool = False,
    project_id: Optional[str] = None
) -> ActionItemList:
    """List all action items with optional filters"""
    conditions = []
    params = {}
    
    if status:
        conditions.append("ai.status = :status")
        params['status'] = status
    if priority:
        conditions.append("ai.priority = :priority")
        params['priority'] = priority
    if owner_user_id:
        conditions.append("ai.owner_user_id = :owner_user_id")
        params['owner_user_id'] = owner_user_id
    if overdue_only:
        conditions.append("ai.deadline < :now AND ai.status != 'completed'")
        params['now'] = datetime.utcnow()
    if project_id:
        conditions.append("ai.project_id = :project_id")
        params['project_id'] = project_id
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    query = text(f"""
        SELECT 
            ai.id::text, ai.meeting_id::text, ai.owner_user_id::text,
            ai.description, ai.deadline, ai.priority, ai.status,
            ai.source_chunk_id::text, ai.source_text, ai.external_task_link,
            ai.external_task_id, ai.confirmed_by::text, ai.confirmed_at,
            ai.created_at, ai.updated_at,
            u.display_name as owner_name,
            m.title as meeting_title
        FROM action_item ai
        LEFT JOIN user_account u ON ai.owner_user_id = u.id
        LEFT JOIN meeting m ON ai.meeting_id = m.id
        {where_clause}
        ORDER BY 
            CASE ai.priority 
                WHEN 'critical' THEN 1 
                WHEN 'high' THEN 2 
                WHEN 'medium' THEN 3 
                ELSE 4 
            END,
            ai.deadline ASC NULLS LAST,
            ai.created_at DESC
    """)
    
    result = db.execute(query, params)
    rows = result.fetchall()
    
    items = []
    for row in rows:
        items.append(ActionItemResponse(
            id=row[0],
            meeting_id=row[1],
            owner_user_id=row[2],
            description=row[3],
            deadline=row[4],
            priority=row[5],
            status=row[6],
            source_chunk_id=row[7],
            source_text=row[8],
            external_task_link=row[9],
            external_task_id=row[10],
            confirmed_by=row[11],
            confirmed_at=row[12],
            created_at=row[13],
            updated_at=row[14],
            owner_name=row[15],
            meeting_title=row[16]
        ))
    
    return ActionItemList(items=items, total=len(items))


def list_action_items(db: Session, meeting_id: str) -> ActionItemList:
    """List all action items for a meeting"""
    query = text("""
        SELECT 
            ai.id::text, ai.meeting_id::text, ai.owner_user_id::text,
            ai.description, ai.deadline, ai.priority, ai.status,
            ai.source_chunk_id::text, ai.source_text, ai.external_task_link,
            ai.external_task_id, ai.confirmed_by::text, ai.confirmed_at,
            ai.created_at, ai.updated_at,
            u.display_name as owner_name
        FROM action_item ai
        LEFT JOIN user_account u ON ai.owner_user_id = u.id
        WHERE ai.meeting_id = :meeting_id
        ORDER BY ai.created_at DESC
    """)
    
    result = db.execute(query, {'meeting_id': meeting_id})
    rows = result.fetchall()
    
    items = []
    for row in rows:
        items.append(ActionItemResponse(
            id=row[0],
            meeting_id=row[1],
            owner_user_id=row[2],
            description=row[3],
            deadline=row[4],
            priority=row[5],
            status=row[6],
            source_chunk_id=row[7],
            source_text=row[8],
            external_task_link=row[9],
            external_task_id=row[10],
            confirmed_by=row[11],
            confirmed_at=row[12],
            created_at=row[13],
            updated_at=row[14],
            owner_name=row[15]
        ))
    
    return ActionItemList(items=items, total=len(items))


def get_action_item(db: Session, item_id: str) -> Optional[ActionItemResponse]:
    """Get a single action item"""
    query = text("""
        SELECT 
            ai.id::text, ai.meeting_id::text, ai.owner_user_id::text,
            ai.description, ai.deadline, ai.priority, ai.status,
            ai.source_chunk_id::text, ai.source_text, ai.external_task_link,
            ai.external_task_id, ai.confirmed_by::text, ai.confirmed_at,
            ai.created_at, ai.updated_at,
            u.display_name as owner_name
        FROM action_item ai
        LEFT JOIN user_account u ON ai.owner_user_id = u.id
        WHERE ai.id = :item_id
    """)
    
    result = db.execute(query, {'item_id': item_id})
    row = result.fetchone()
    
    if not row:
        return None
    
    return ActionItemResponse(
        id=row[0],
        meeting_id=row[1],
        owner_user_id=row[2],
        description=row[3],
        deadline=row[4],
        priority=row[5],
        status=row[6],
        source_chunk_id=row[7],
        source_text=row[8],
        external_task_link=row[9],
        external_task_id=row[10],
        confirmed_by=row[11],
        confirmed_at=row[12],
        created_at=row[13],
        updated_at=row[14],
        owner_name=row[15]
    )


def create_action_item(db: Session, data: ActionItemCreate) -> ActionItemResponse:
    """Create a new action item"""
    item_id = str(uuid4())
    now = datetime.utcnow()
    project_id = None

    # inherit project_id from meeting if available
    if data.meeting_id:
        res = db.execute(text("SELECT project_id::text FROM meeting WHERE id = :mid"), {'mid': data.meeting_id})
        row = res.fetchone()
        if row:
            project_id = row[0]
    
    query = text("""
        INSERT INTO action_item (
            id, meeting_id, project_id, owner_user_id, description, deadline, priority, 
            status, source_text, external_task_link, created_at, updated_at
        )
        VALUES (
            :id, :meeting_id, :project_id, :owner_user_id, :description, :deadline, :priority,
            :status, :source_text, :external_task_link, :created_at, :updated_at
        )
        RETURNING id::text
    """)
    
    db.execute(query, {
        'id': item_id,
        'meeting_id': data.meeting_id,
        'project_id': project_id,
        'owner_user_id': data.owner_user_id,
        'description': data.description,
        'deadline': data.deadline,
        'priority': data.priority,
        'status': data.status,
        'source_text': data.source_text,
        'external_task_link': data.external_task_link,
        'created_at': now,
        'updated_at': now
    })
    db.commit()
    
    return get_action_item(db, item_id)


def update_action_item(db: Session, item_id: str, data: ActionItemUpdate) -> Optional[ActionItemResponse]:
    """Update an action item"""
    updates = []
    params = {'item_id': item_id, 'updated_at': datetime.utcnow()}
    
    if data.description is not None:
        updates.append("description = :description")
        params['description'] = data.description
    if data.owner_user_id is not None:
        updates.append("owner_user_id = :owner_user_id")
        params['owner_user_id'] = data.owner_user_id
    if data.deadline is not None:
        updates.append("deadline = :deadline")
        params['deadline'] = data.deadline
    if data.priority is not None:
        updates.append("priority = :priority")
        params['priority'] = data.priority
    if data.status is not None:
        updates.append("status = :status")
        params['status'] = data.status
    if data.external_task_link is not None:
        updates.append("external_task_link = :external_task_link")
        params['external_task_link'] = data.external_task_link
    if data.external_task_id is not None:
        updates.append("external_task_id = :external_task_id")
        params['external_task_id'] = data.external_task_id
    
    if not updates:
        return get_action_item(db, item_id)
    
    updates.append("updated_at = :updated_at")
    
    query = text(f"""
        UPDATE action_item
        SET {', '.join(updates)}
        WHERE id = :item_id
        RETURNING id::text
    """)
    
    result = db.execute(query, params)
    db.commit()
    
    if not result.fetchone():
        return None
    
    return get_action_item(db, item_id)


def confirm_action_item(db: Session, item_id: str, confirmed_by: str) -> Optional[ActionItemResponse]:
    """Confirm an action item"""
    query = text("""
        UPDATE action_item
        SET status = 'confirmed', confirmed_by = :confirmed_by, 
            confirmed_at = :confirmed_at, updated_at = :updated_at
        WHERE id = :item_id
        RETURNING id::text
    """)
    
    now = datetime.utcnow()
    result = db.execute(query, {
        'item_id': item_id,
        'confirmed_by': confirmed_by,
        'confirmed_at': now,
        'updated_at': now
    })
    db.commit()
    
    if not result.fetchone():
        return None
    
    return get_action_item(db, item_id)


def delete_action_item(db: Session, item_id: str) -> bool:
    """Delete an action item"""
    query = text("DELETE FROM action_item WHERE id = :item_id RETURNING id")
    result = db.execute(query, {'item_id': item_id})
    db.commit()
    return result.fetchone() is not None


# ============================================
# DECISION ITEM CRUD
# ============================================

def list_decision_items(db: Session, meeting_id: str) -> DecisionItemList:
    """List all decision items for a meeting"""
    query = text("""
        SELECT 
            id::text, meeting_id::text, description, rationale,
            source_chunk_id::text, source_text, status,
            confirmed_by::text, confirmed_at, created_at
        FROM decision_item
        WHERE meeting_id = :meeting_id
        ORDER BY created_at DESC
    """)
    
    result = db.execute(query, {'meeting_id': meeting_id})
    rows = result.fetchall()
    
    items = []
    for row in rows:
        items.append(DecisionItemResponse(
            id=row[0],
            meeting_id=row[1],
            description=row[2],
            rationale=row[3],
            source_chunk_id=row[4],
            source_text=row[5],
            status=row[6],
            confirmed_by=row[7],
            confirmed_at=row[8],
            created_at=row[9]
        ))
    
    return DecisionItemList(items=items, total=len(items))


def get_decision_item(db: Session, item_id: str) -> Optional[DecisionItemResponse]:
    """Get a single decision item by id"""
    query = text("""
        SELECT
            id::text, meeting_id::text, description, rationale,
            source_chunk_id::text, source_text, status,
            confirmed_by::text, confirmed_at, created_at
        FROM decision_item
        WHERE id = :item_id
        LIMIT 1
    """)

    row = db.execute(query, {'item_id': item_id}).fetchone()
    if not row:
        return None

    return DecisionItemResponse(
        id=row[0],
        meeting_id=row[1],
        description=row[2],
        rationale=row[3],
        source_chunk_id=row[4],
        source_text=row[5],
        status=row[6],
        confirmed_by=row[7],
        confirmed_at=row[8],
        created_at=row[9]
    )


def create_decision_item(db: Session, data: DecisionItemCreate) -> DecisionItemResponse:
    """Create a new decision item"""
    item_id = str(uuid4())
    now = datetime.utcnow()
    
    query = text("""
        INSERT INTO decision_item (
            id, meeting_id, description, rationale, source_text, status, created_at
        )
        VALUES (
            :id, :meeting_id, :description, :rationale, :source_text, :status, :created_at
        )
        RETURNING id::text
    """)
    
    db.execute(query, {
        'id': item_id,
        'meeting_id': data.meeting_id,
        'description': data.description,
        'rationale': data.rationale,
        'source_text': data.source_text,
        'status': data.status,
        'created_at': now
    })
    db.commit()
    
    return DecisionItemResponse(
        id=item_id,
        meeting_id=data.meeting_id,
        description=data.description,
        rationale=data.rationale,
        source_text=data.source_text,
        status=data.status,
        created_at=now
    )


def update_decision_item(db: Session, item_id: str, data: DecisionItemUpdate) -> Optional[DecisionItemResponse]:
    """Update a decision item"""
    updates = []
    params = {'item_id': item_id}
    
    if data.description is not None:
        updates.append("description = :description")
        params['description'] = data.description
    if data.rationale is not None:
        updates.append("rationale = :rationale")
        params['rationale'] = data.rationale
    if data.status is not None:
        updates.append("status = :status")
        params['status'] = data.status
    
    if not updates:
        return None
    
    query = text(f"""
        UPDATE decision_item
        SET {', '.join(updates)}
        WHERE id = :item_id
        RETURNING id::text, meeting_id::text, description, rationale,
            source_chunk_id::text, source_text, status,
            confirmed_by::text, confirmed_at, created_at
    """)
    
    result = db.execute(query, params)
    db.commit()
    row = result.fetchone()
    
    if not row:
        return None
    
    return DecisionItemResponse(
        id=row[0],
        meeting_id=row[1],
        description=row[2],
        rationale=row[3],
        source_chunk_id=row[4],
        source_text=row[5],
        status=row[6],
        confirmed_by=row[7],
        confirmed_at=row[8],
        created_at=row[9]
    )


def delete_decision_item(db: Session, item_id: str) -> bool:
    """Delete a decision item"""
    query = text("DELETE FROM decision_item WHERE id = :item_id RETURNING id")
    result = db.execute(query, {'item_id': item_id})
    db.commit()
    return result.fetchone() is not None


# ============================================
# RISK ITEM CRUD
# ============================================

def list_risk_items(db: Session, meeting_id: str) -> RiskItemList:
    """List all risk items for a meeting"""
    query = text("""
        SELECT 
            ri.id::text, ri.meeting_id::text, ri.description, ri.severity,
            ri.mitigation, ri.source_chunk_id::text, ri.source_text,
            ri.status, ri.owner_user_id::text, ri.created_at,
            u.display_name as owner_name
        FROM risk_item ri
        LEFT JOIN user_account u ON ri.owner_user_id = u.id
        WHERE ri.meeting_id = :meeting_id
        ORDER BY 
            CASE ri.severity 
                WHEN 'critical' THEN 1 
                WHEN 'high' THEN 2 
                WHEN 'medium' THEN 3 
                ELSE 4 
            END,
            ri.created_at DESC
    """)
    
    result = db.execute(query, {'meeting_id': meeting_id})
    rows = result.fetchall()
    
    items = []
    for row in rows:
        items.append(RiskItemResponse(
            id=row[0],
            meeting_id=row[1],
            description=row[2],
            severity=row[3],
            mitigation=row[4],
            source_chunk_id=row[5],
            source_text=row[6],
            status=row[7],
            owner_user_id=row[8],
            created_at=row[9],
            owner_name=row[10]
        ))
    
    return RiskItemList(items=items, total=len(items))


def get_risk_item(db: Session, item_id: str) -> Optional[RiskItemResponse]:
    """Get a single risk item by id"""
    query = text("""
        SELECT
            ri.id::text, ri.meeting_id::text, ri.description, ri.severity,
            ri.mitigation, ri.source_chunk_id::text, ri.source_text,
            ri.status, ri.owner_user_id::text, ri.created_at,
            u.display_name as owner_name
        FROM risk_item ri
        LEFT JOIN user_account u ON ri.owner_user_id = u.id
        WHERE ri.id = :item_id
        LIMIT 1
    """)

    row = db.execute(query, {'item_id': item_id}).fetchone()
    if not row:
        return None

    return RiskItemResponse(
        id=row[0],
        meeting_id=row[1],
        description=row[2],
        severity=row[3],
        mitigation=row[4],
        source_chunk_id=row[5],
        source_text=row[6],
        status=row[7],
        owner_user_id=row[8],
        created_at=row[9],
        owner_name=row[10]
    )


def create_risk_item(db: Session, data: RiskItemCreate) -> RiskItemResponse:
    """Create a new risk item"""
    item_id = str(uuid4())
    now = datetime.utcnow()
    
    query = text("""
        INSERT INTO risk_item (
            id, meeting_id, description, severity, mitigation,
            source_text, status, owner_user_id, created_at
        )
        VALUES (
            :id, :meeting_id, :description, :severity, :mitigation,
            :source_text, :status, :owner_user_id, :created_at
        )
        RETURNING id::text
    """)
    
    db.execute(query, {
        'id': item_id,
        'meeting_id': data.meeting_id,
        'description': data.description,
        'severity': data.severity,
        'mitigation': data.mitigation,
        'source_text': data.source_text,
        'status': data.status,
        'owner_user_id': data.owner_user_id,
        'created_at': now
    })
    db.commit()
    
    return RiskItemResponse(
        id=item_id,
        meeting_id=data.meeting_id,
        description=data.description,
        severity=data.severity,
        mitigation=data.mitigation,
        source_text=data.source_text,
        status=data.status,
        owner_user_id=data.owner_user_id,
        created_at=now
    )


def update_risk_item(db: Session, item_id: str, data: RiskItemUpdate) -> Optional[RiskItemResponse]:
    """Update a risk item"""
    updates = []
    params = {'item_id': item_id}
    
    if data.description is not None:
        updates.append("description = :description")
        params['description'] = data.description
    if data.severity is not None:
        updates.append("severity = :severity")
        params['severity'] = data.severity
    if data.mitigation is not None:
        updates.append("mitigation = :mitigation")
        params['mitigation'] = data.mitigation
    if data.status is not None:
        updates.append("status = :status")
        params['status'] = data.status
    if data.owner_user_id is not None:
        updates.append("owner_user_id = :owner_user_id")
        params['owner_user_id'] = data.owner_user_id
    
    if not updates:
        return None
    
    query = text(f"""
        UPDATE risk_item
        SET {', '.join(updates)}
        WHERE id = :item_id
        RETURNING id::text
    """)
    
    result = db.execute(query, params)
    db.commit()

    if not result.fetchone():
        return None

    fetch_query = text("""
        SELECT
            ri.id::text, ri.meeting_id::text, ri.description, ri.severity,
            ri.mitigation, ri.source_chunk_id::text, ri.source_text,
            ri.status, ri.owner_user_id::text, ri.created_at,
            u.display_name as owner_name
        FROM risk_item ri
        LEFT JOIN user_account u ON ri.owner_user_id = u.id
        WHERE ri.id = :item_id
        LIMIT 1
    """)
    row = db.execute(fetch_query, {'item_id': item_id}).fetchone()
    if not row:
        return None

    return RiskItemResponse(
        id=row[0],
        meeting_id=row[1],
        description=row[2],
        severity=row[3],
        mitigation=row[4],
        source_chunk_id=row[5],
        source_text=row[6],
        status=row[7],
        owner_user_id=row[8],
        created_at=row[9],
        owner_name=row[10]
    )


def delete_risk_item(db: Session, item_id: str) -> bool:
    """Delete a risk item"""
    query = text("DELETE FROM risk_item WHERE id = :item_id RETURNING id")
    result = db.execute(query, {'item_id': item_id})
    db.commit()
    return result.fetchone() is not None

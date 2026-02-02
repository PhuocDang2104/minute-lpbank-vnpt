from typing import Optional, Tuple, List
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectList,
    ProjectMember,
    ProjectMemberList,
)


def list_projects(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    department_id: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> Tuple[List[Project], int]:
    query = """
        SELECT id::text, name, code, description, objective, organization_id::text, department_id::text,
               created_at, updated_at
        FROM project
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) FROM project WHERE 1=1"
    params = {}

    if search:
        query += " AND (name ILIKE :search OR code ILIKE :search)"
        count_query += " AND (name ILIKE :search OR code ILIKE :search)"
        params['search'] = f"%{search}%"

    if department_id:
        query += " AND department_id = :department_id"
        count_query += " AND department_id = :department_id"
        params['department_id'] = department_id

    if organization_id:
        query += " AND organization_id = :organization_id"
        count_query += " AND organization_id = :organization_id"
        params['organization_id'] = organization_id

    query += " ORDER BY created_at DESC NULLS LAST LIMIT :limit OFFSET :skip"
    params['limit'] = limit
    params['skip'] = skip

    rows = db.execute(text(query), params).fetchall()
    total = db.execute(text(count_query), {k: v for k, v in params.items() if k not in ['limit', 'skip']}).scalar()

    projects = [
        Project(
            id=row[0],
            name=row[1],
            code=row[2],
            description=row[3],
            objective=row[4],
            organization_id=row[5],
            department_id=row[6],
            created_at=row[7],
            updated_at=row[8],
        )
        for row in rows
    ]

    return projects, total


def get_project(db: Session, project_id: str) -> Optional[Project]:
    query = text("""
        SELECT id::text, name, code, description, objective, organization_id::text, department_id::text,
               created_at, updated_at
        FROM project
        WHERE id = :project_id
    """)
    row = db.execute(query, {'project_id': project_id}).fetchone()
    if not row:
        return None
    return Project(
        id=row[0],
        name=row[1],
        code=row[2],
        description=row[3],
        objective=row[4],
        organization_id=row[5],
        department_id=row[6],
        created_at=row[7],
        updated_at=row[8],
    )


def create_project(db: Session, data: ProjectCreate) -> Project:
    project_id = str(uuid4())
    query = text("""
        INSERT INTO project (
            id, name, code, description, objective, organization_id, department_id, created_at, updated_at
        ) VALUES (
            :id, :name, :code, :description, :objective, :organization_id, :department_id, now(), now()
        )
        RETURNING id::text, name, code, description, objective, organization_id::text, department_id::text, created_at, updated_at
    """)
    row = db.execute(query, {
        'id': project_id,
        'name': data.name,
        'code': data.code,
        'description': data.description,
        'objective': data.objective,
        'organization_id': data.organization_id,
        'department_id': data.department_id,
    }).fetchone()
    db.commit()

    # Add owner as member if provided
    if data.owner_id:
        add_member(db, project_id, data.owner_id, role='owner')

    return Project(
        id=row[0], name=row[1], code=row[2], description=row[3],
        objective=row[4], organization_id=row[5], department_id=row[6],
        created_at=row[7], updated_at=row[8]
    )


def update_project(db: Session, project_id: str, data: ProjectUpdate) -> Optional[Project]:
    updates = []
    params = {'project_id': project_id, 'updated_at': None}
    params['updated_at'] = text("now()")

    if data.name is not None:
        updates.append("name = :name")
        params['name'] = data.name
    if data.code is not None:
        updates.append("code = :code")
        params['code'] = data.code
    if data.description is not None:
        updates.append("description = :description")
        params['description'] = data.description
    if data.objective is not None:
        updates.append("objective = :objective")
        params['objective'] = data.objective
    if data.organization_id is not None:
        updates.append("organization_id = :organization_id")
        params['organization_id'] = data.organization_id
    if data.department_id is not None:
        updates.append("department_id = :department_id")
        params['department_id'] = data.department_id

    if not updates:
        return get_project(db, project_id)

    updates.append("updated_at = now()")
    query = text(f"""
        UPDATE project
        SET {', '.join(updates)}
        WHERE id = :project_id
        RETURNING id::text, name, code, description, objective, organization_id::text, department_id::text, created_at, updated_at
    """)
    row = db.execute(query, params).fetchone()
    db.commit()
    if not row:
        return None

    return Project(
        id=row[0], name=row[1], code=row[2], description=row[3],
        objective=row[4], organization_id=row[5], department_id=row[6],
        created_at=row[7], updated_at=row[8]
    )


def delete_project(db: Session, project_id: str) -> bool:
    try:
        # Delete knowledge chunks/documents tied to project
        db.execute(
            text(
                "DELETE FROM knowledge_chunk WHERE document_id IN "
                "(SELECT id FROM knowledge_document WHERE project_id = :pid)"
            ),
            {"pid": project_id},
        )
        db.execute(
            text("DELETE FROM knowledge_document WHERE project_id = :pid"),
            {"pid": project_id},
        )
        # Delete meeting participants then meetings
        db.execute(
            text(
                "DELETE FROM meeting_participant "
                "WHERE meeting_id IN (SELECT id FROM meeting WHERE project_id = :pid)"
            ),
            {"pid": project_id},
        )
        db.execute(
            text("DELETE FROM meeting WHERE project_id = :pid"),
            {"pid": project_id},
        )
        # Delete project members
        db.execute(
            text("DELETE FROM project_member WHERE project_id = :pid"),
            {"pid": project_id},
        )
        # Delete project
        result = db.execute(
            text("DELETE FROM project WHERE id = :project_id RETURNING id"),
            {"project_id": project_id},
        )
        db.commit()
        return result.fetchone() is not None
    except Exception as exc:
        db.rollback()
        raise


# Members
def list_members(db: Session, project_id: str) -> ProjectMemberList:
    query = text("""
        SELECT 
            pm.project_id::text,
            pm.user_id::text,
            pm.role,
            pm.joined_at,
            u.display_name,
            u.email
        FROM project_member pm
        LEFT JOIN user_account u ON pm.user_id = u.id
        WHERE pm.project_id = :project_id
        ORDER BY pm.role, u.display_name
    """)
    rows = db.execute(query, {'project_id': project_id}).fetchall()
    members = [
        ProjectMember(
            project_id=row[0],
            user_id=row[1],
            role=row[2],
            joined_at=row[3],
            display_name=row[4],
            email=row[5],
        )
        for row in rows
    ]
    return ProjectMemberList(members=members, total=len(members))


def add_member(db: Session, project_id: str, user_id: str, role: str = 'member') -> ProjectMember:
    db.execute(text("""
        INSERT INTO project_member (project_id, user_id, role, joined_at)
        VALUES (:project_id, :user_id, :role, now())
        ON CONFLICT (project_id, user_id) DO UPDATE SET role = :role
    """), {'project_id': project_id, 'user_id': user_id, 'role': role})
    db.commit()
    return list_members(db, project_id).members[-1]


def remove_member(db: Session, project_id: str, user_id: str) -> bool:
    result = db.execute(text("""
        DELETE FROM project_member
        WHERE project_id = :project_id AND user_id = :user_id
        RETURNING project_id
    """), {'project_id': project_id, 'user_id': user_id})
    db.commit()
    return result.fetchone() is not None

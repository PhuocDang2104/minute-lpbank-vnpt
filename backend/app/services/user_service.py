from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.user import User, UserList, Department


def get_user_stub() -> User:
    """Stub user for testing"""
    return User(
        id='u0000001-0000-0000-0000-000000000001',
        email='nguyenvana@lpbank.vn',
        display_name='Nguyễn Văn A',
        role='PMO',
        department_name='PMO'
    )


def list_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    department_id: Optional[str] = None
) -> Tuple[List[User], int]:
    """List all users with optional filters"""
    
    query = """
        SELECT 
            u.id::text, u.email, u.display_name, u.role,
            u.department_id::text, u.avatar_url,
            u.organization_id::text, u.created_at,
            u.last_login_at, u.is_active,
            d.name as department_name
        FROM user_account u
        LEFT JOIN department d ON u.department_id = d.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) FROM user_account u WHERE 1=1"
    params = {}
    
    if search:
        query += " AND (u.display_name ILIKE :search OR u.email ILIKE :search)"
        count_query += " AND (u.display_name ILIKE :search OR u.email ILIKE :search)"
        params['search'] = f'%{search}%'
    
    if department_id:
        query += " AND u.department_id = :department_id"
        count_query += " AND u.department_id = :department_id"
        params['department_id'] = department_id
    
    query += " ORDER BY u.display_name LIMIT :limit OFFSET :skip"
    params['limit'] = limit
    params['skip'] = skip
    
    result = db.execute(text(query), params)
    rows = result.fetchall()
    
    count_result = db.execute(text(count_query), {k: v for k, v in params.items() if k not in ['limit', 'skip']})
    total = count_result.scalar()
    
    users = []
    for row in rows:
        users.append(User(
            id=row[0],
            email=row[1],
            display_name=row[2],
            role=row[3] or 'user',
            department_id=row[4],
            avatar_url=row[5],
            organization_id=row[6],
            created_at=row[7],
            last_login_at=row[8],
            is_active=row[9] if row[9] is not None else True,
            department_name=row[10]
        ))
    
    return users, total


def get_user(db: Session, user_id: str) -> Optional[User]:
    """Get a user by ID"""
    query = text("""
        SELECT 
            u.id::text, u.email, u.display_name, u.role,
            u.department_id::text, u.avatar_url,
            u.organization_id::text, u.created_at,
            u.last_login_at, u.is_active,
            d.name as department_name
        FROM user_account u
        LEFT JOIN department d ON u.department_id = d.id
        WHERE u.id = :user_id
    """)
    
    result = db.execute(query, {'user_id': user_id})
    row = result.fetchone()
    
    if not row:
        return None
    
    return User(
        id=row[0],
        email=row[1],
        display_name=row[2],
        role=row[3] or 'user',
        department_id=row[4],
        avatar_url=row[5],
        organization_id=row[6],
        created_at=row[7],
        last_login_at=row[8],
        is_active=row[9] if row[9] is not None else True,
        department_name=row[10]
    )


def update_user_role(db: Session, user_id: str, new_role: str) -> Optional[User]:
    """Update user role and return updated user"""
    update_query = text("""
        UPDATE user_account
        SET role = :role, updated_at = now()
        WHERE id = :user_id
        RETURNING id::text
    """)
    result = db.execute(update_query, {'role': new_role, 'user_id': user_id})
    row = result.fetchone()
    if not row:
        db.rollback()
        return None
    db.commit()
    return get_user(db, user_id)


def update_user_status(db: Session, user_id: str, is_active: bool) -> Optional[User]:
    """Activate/deactivate user"""
    update_query = text("""
        UPDATE user_account
        SET is_active = :is_active, updated_at = now()
        WHERE id = :user_id
        RETURNING id::text
    """)
    result = db.execute(update_query, {'is_active': is_active, 'user_id': user_id})
    row = result.fetchone()
    if not row:
        db.rollback()
        return None
    db.commit()
    return get_user(db, user_id)


def list_departments(db: Session) -> Tuple[List[Department], int]:
    """List all departments"""
    query = text("""
        SELECT id::text, name, organization_id::text
        FROM department
        ORDER BY name
    """)
    
    result = db.execute(query)
    rows = result.fetchall()
    
    departments = [
        Department(id=row[0], name=row[1], organization_id=row[2])
        for row in rows
    ]
    
    return departments, len(departments)

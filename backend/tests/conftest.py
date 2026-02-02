"""
Pytest configuration and fixtures
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.db.session import get_db


# In-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    # For services using in-memory storage (documents, agenda),
    # we can use a mock session
    db = MagicMock()
    db.execute = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    db.close = MagicMock()
    return db


@pytest.fixture
def override_get_db(db_session):
    """Override get_db dependency"""
    def _get_db():
        try:
            yield db_session
        finally:
            pass
    return _get_db


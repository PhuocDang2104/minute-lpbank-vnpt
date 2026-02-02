import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at fields"""
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class UUIDMixin:
    """Mixin for UUID primary key"""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
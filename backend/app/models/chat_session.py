import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey('meetings.id'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    last_activity = Column(DateTime(timezone=True))
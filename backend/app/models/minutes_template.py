"""
Minutes Template Model
"""
import uuid
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class MinutesTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = 'minutes_template'
    
    # Basic Info
    name = Column(String, nullable=False)
    code = Column(String, unique=True)
    description = Column(Text)
    
    # Template Structure
    structure = Column(JSONB, nullable=False)
    sample_data = Column(JSONB)
    
    # Usage
    meeting_types = Column(ARRAY(String))
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey('user_account.id'))
    updated_by = Column(UUID(as_uuid=True), ForeignKey('user_account.id'))
    
    # Versioning
    version = Column(Integer, default=1)
    parent_template_id = Column(UUID(as_uuid=True), ForeignKey('minutes_template.id'))
    
    # Relationships
    parent_template = relationship("MinutesTemplate", remote_side=[Base.id], backref="child_templates")
    creator = relationship("UserAccount", foreign_keys=[created_by], backref="created_templates")
    updater = relationship("UserAccount", foreign_keys=[updated_by], backref="updated_templates")


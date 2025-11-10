"""
Session Model - User conversation sessions

Tracks active conversations/interactions with the chatbot.
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator
import json

from app.db.database import Base


class JSONType(TypeDecorator):
    """Cross-database JSON type"""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is not None and dialect.name != 'postgresql':
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and dialect.name != 'postgresql':
            value = json.loads(value)
        return value


class Session(Base):
    """
    Session - User conversation/interaction
    
    Tracks context and history for ongoing conversations.
    """
    __tablename__ = "sessions"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Unique session identifier (UUID)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Foreign Keys
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("tenant_users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Session data
    context = Column(JSONType, nullable=True, default=dict)
    # Example: {"language": "he", "theme": "dark", "last_query": "Show sales", "history": [...]}
    
    # Activity tracking
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="sessions")
    user = relationship("TenantUser", back_populates="sessions")
    
    @property
    def is_active(self):
        """Check if session is active (last activity within 1 hour)"""
        if not self.last_activity:
            return False
        return datetime.utcnow() - self.last_activity < timedelta(hours=1)
    
    def __repr__(self):
        return f"<Session {self.session_id}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "context": self.context,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
        }

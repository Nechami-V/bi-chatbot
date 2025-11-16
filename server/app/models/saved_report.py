"""
SavedReport Model - Saved/scheduled report definitions

Stores user-defined reports for repeated execution or scheduling.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
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


class SavedReport(Base):
    """
    SavedReport - User-defined report with optional scheduling
    
    Allows users to save queries for repeated execution or daily/weekly runs.
    """
    __tablename__ = "saved_reports"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("tenant_users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Report definition
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    question = Column(Text, nullable=False)  # Original natural language question
    sql_query = Column(Text, nullable=False)  # Generated SQL for export
    parameters = Column(JSONType, nullable=True, default=dict)  # {"year": 2025, "region": "North"}
    
    # Scheduling
    schedule_cron = Column(String(100), nullable=True)  # e.g., "0 9 * * 1" (every Monday 9 AM)
    is_scheduled = Column(Boolean, default=False, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="saved_reports")
    creator = relationship("TenantUser", back_populates="saved_reports", foreign_keys=[created_by])
    report_runs = relationship("ReportRun", back_populates="report", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SavedReport {self.name}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "created_by": self.created_by,
            "name": self.name,
            "description": self.description,
            "question": self.question,
            "sql_query": self.sql_query,
            "parameters": self.parameters,
            "schedule_cron": self.schedule_cron,
            "is_scheduled": self.is_scheduled,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
        }

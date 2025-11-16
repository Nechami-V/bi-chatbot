"""
Tenant Model - Multi-tenant organization/client entity

Represents a single organization using the BI Chatbot system.
Each tenant has isolated data and can have multiple users.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator
import json

from app.db.database import Base


class JSONType(TypeDecorator):
    """
    Cross-database JSON type
    - SQLite: stores as TEXT with JSON serialization
    - PostgreSQL: uses native JSONB
    """
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


class Tenant(Base):
    """
    Tenant - Organization/Client
    
    Main entity for multi-tenancy. All user data is scoped to a tenant.
    """
    __tablename__ = "tenants"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Core fields
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Configuration (JSON)
    config = Column(JSONType, nullable=True, default=dict)
    # Example config: {"max_tokens_per_month": 1000000, "features": ["export", "scheduling"]}
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="tenant", cascade="all, delete-orphan")
    saved_reports = relationship("SavedReport", back_populates="tenant", cascade="all, delete-orphan")
    report_runs = relationship("ReportRun", back_populates="tenant", cascade="all, delete-orphan")
    usage_records = relationship("UsageDaily", back_populates="tenant", cascade="all, delete-orphan")
    quota = relationship("Quota", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant {self.name}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "config": self.config,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

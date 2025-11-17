"""
TenantUser Model - Multi-tenant user entity

Represents users within the multi-tenant system (separate from auth User).
Each TenantUser belongs to a specific Tenant and has scoped permissions.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class TenantUser(Base):
    """
    TenantUser - User within a tenant organization
    
    Separate from the auth User model.
    Represents actual users who interact with the BI system within their tenant.
    """
    __tablename__ = "tenant_users"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # User identity
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    
    # Optional password (if not using external auth)
    hashed_password = Column(String(255), nullable=True)
    
    # Role within tenant
    role = Column(String(50), nullable=False, default="user")  # "admin", "user", "viewer"
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Session tracking
    last_session_id = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    saved_reports = relationship("SavedReport", back_populates="creator", cascade="all, delete-orphan")
    usage_records = relationship("UsageDaily", back_populates="user", cascade="all, delete-orphan")
    external_identities = relationship("ExternalIdentity", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TenantUser {self.email}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
            "last_session_id": self.last_session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

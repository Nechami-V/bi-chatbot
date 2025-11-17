"""
ExternalIdentity Model - External authentication/SSO integration

Maps external identity providers (SAML, OAuth, AD) to internal users.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint
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


class ExternalIdentity(Base):
    """
    ExternalIdentity - External authentication provider mapping
    
    Links users to external identity systems (SAML, OAuth2, Active Directory).
    Multiple external identities can map to the same user.
    """
    __tablename__ = "external_identities"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    user_id = Column(Integer, ForeignKey("tenant_users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # External provider details
    provider = Column(String(50), nullable=False, index=True)  # "saml", "oauth2", "azure_ad", "google"
    external_id = Column(String(255), nullable=False, index=True)  # Provider's unique user ID
    external_email = Column(String(255), nullable=True)
    
    # Additional metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    provider_metadata = Column(JSONType, nullable=True, default=dict)
    # Example: {"department": "Sales", "employee_id": "E12345", "groups": ["managers"]}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("TenantUser", back_populates="external_identities")
    
    # Unique constraint: one external_id per provider
    __table_args__ = (
        UniqueConstraint('provider', 'external_id', name='uix_external_identity'),
    )
    
    def __repr__(self):
        return f"<ExternalIdentity {self.provider}:{self.external_id}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "provider": self.provider,
            "external_id": self.external_id,
            "external_email": self.external_email,
            "provider_metadata": self.provider_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

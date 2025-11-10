"""
UsageDaily Model - Daily token usage tracking

Aggregates daily usage per tenant/user/model for monitoring and billing.
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base


class UsageDaily(Base):
    """
    UsageDaily - Daily token consumption tracking
    
    One record per (date, tenant, user, model) combination.
    Updated incrementally throughout the day.
    """
    __tablename__ = "usage_daily"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Composite unique key
    usage_date = Column(Date, nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("tenant_users.id", ondelete="CASCADE"), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)  # e.g., "gpt-4", "gpt-3.5-turbo"
    
    # Usage counters
    total_tokens = Column(Integer, nullable=False, default=0)
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    calls_count = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="usage_records")
    user = relationship("TenantUser", back_populates="usage_records")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('usage_date', 'tenant_id', 'user_id', 'model', name='uix_usage_daily'),
    )
    
    def __repr__(self):
        return f"<UsageDaily {self.usage_date} T:{self.tenant_id} U:{self.user_id} M:{self.model}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "usage_date": self.usage_date.isoformat() if self.usage_date else None,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "model": self.model,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "calls_count": self.calls_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

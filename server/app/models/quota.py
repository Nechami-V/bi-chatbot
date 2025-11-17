"""
Quota Model - Tenant usage quotas and limits

Defines monthly token limits and tracks current usage for billing/throttling.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.db.database import Base


class Quota(Base):
    """
    Quota - Monthly usage limits per tenant
    
    One-to-one relationship with Tenant.
    Tracks monthly token allowance and current usage.
    """
    __tablename__ = "quotas"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key (one-to-one with Tenant)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Quota limits
    monthly_token_limit = Column(Integer, nullable=False, default=1000000)  # 1M tokens/month
    
    # Current month usage (reset monthly)
    current_month_tokens = Column(Integer, nullable=False, default=0)
    current_month_start = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Hard limit enforcement
    enforce_limit = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="quota")
    
    @property
    def usage_percentage(self):
        """Calculate current usage as percentage of limit"""
        if self.monthly_token_limit == 0:
            return 100.0
        return (self.current_month_tokens / self.monthly_token_limit) * 100
    
    @property
    def is_over_limit(self):
        """Check if current usage exceeds limit"""
        return self.current_month_tokens >= self.monthly_token_limit
    
    @property
    def remaining_tokens(self):
        """Calculate remaining tokens for current month"""
        return max(0, self.monthly_token_limit - self.current_month_tokens)
    
    def __repr__(self):
        return f"<Quota Tenant:{self.tenant_id} {self.current_month_tokens}/{self.monthly_token_limit}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "monthly_token_limit": self.monthly_token_limit,
            "current_month_tokens": self.current_month_tokens,
            "current_month_start": self.current_month_start.isoformat() if self.current_month_start else None,
            "enforce_limit": self.enforce_limit,
            "usage_percentage": round(self.usage_percentage, 2),
            "is_over_limit": self.is_over_limit,
            "remaining_tokens": self.remaining_tokens,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

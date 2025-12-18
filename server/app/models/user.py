from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..db.database import Base

# Optional bcrypt verification via bcrypt library only (avoid passlib incompat issues)
try:
    import bcrypt as _BCRYPT  # type: ignore
    _BCRYPT_AVAILABLE = True
except Exception:
    _BCRYPT = None
    _BCRYPT_AVAILABLE = False

class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    # External users integration fields
    permission_group = Column(String, default="user", nullable=False)
    is_manager = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username}>"

    # Compatibility helpers for external user integration
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "phone": getattr(self, "phone", None),
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "permission_group": self.permission_group,
            "is_manager": self.is_manager,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash.

        Supports bcrypt when stored hash starts with "$2" (using bcrypt module),
        otherwise falls back to raw equality for legacy/pre-hashed inputs.
        """
        if (
            isinstance(self.hashed_password, str)
            and self.hashed_password
            and self.hashed_password.startswith("$2")
            and _BCRYPT_AVAILABLE
        ):
            try:
                return _BCRYPT.checkpw(password.encode("utf-8"), self.hashed_password.encode("utf-8"))
            except Exception:
                return False
        # Fallback: compare as-is (expects caller to hash consistently elsewhere)
        return self.hashed_password == password


class APIKey(Base):
    """API Key model for programmatic access."""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey {self.key[:8]}...>"

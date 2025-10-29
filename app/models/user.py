from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean
from ..db.database import Base
import hashlib

# Optional bcrypt verification if available
try:
    import bcrypt as _bcrypt
    _BCRYPT_AVAILABLE = True
except Exception:
    _BCRYPT_AVAILABLE = False


class User(Base):
    """User model used as a DTO for auth as well.

    Note: In external DB mode we may hydrate instances from raw queries
    rather than persisting via this ORM mapping.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False, comment="First name")
    last_name = Column(String(100), nullable=False, comment="Last name")
    phone = Column(String(20), nullable=True, comment="Phone number")
    email = Column(String(150), nullable=False, unique=True, comment="Email address")
    password = Column(String(255), nullable=False, comment="Password hash or bcrypt hash")
    is_manager = Column(Boolean, default=False, comment="Manager flag (T/F)")
    permission_group = Column(String(50), nullable=False, comment="Permission group")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash.

        - If the stored value looks like a bcrypt hash ($2b$...), verify with bcrypt (when available).
        - Otherwise, fall back to comparing SHA256(password).
        """
        stored = self.password or ""

        if isinstance(stored, str) and stored.startswith("$2") and _BCRYPT_AVAILABLE:
            try:
                return _bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
            except Exception:
                return False

        # Fallback to legacy SHA256
        return stored == self.hash_password(password)

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': getattr(self, 'first_name', None),
            'last_name': getattr(self, 'last_name', None),
            'full_name': self.full_name,
            'email': getattr(self, 'email', None),
            'phone': getattr(self, 'phone', None),
            'is_manager': getattr(self, 'is_manager', False),
            'permission_group': getattr(self, 'permission_group', None)
        }

    def __repr__(self):
        return f"<User {self.full_name} ({self.permission_group})>"

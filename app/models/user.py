from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean
from ..db.database import Base
import hashlib

class User(Base):
    """User model with exact columns as requested"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False, comment="First name")
    last_name = Column(String(100), nullable=False, comment="Last name")
    phone = Column(String(20), nullable=True, comment="Phone number")
    email = Column(String(150), nullable=False, unique=True, comment="Email address")
    password = Column(String(255), nullable=False, comment="Password hash")
    is_manager = Column(Boolean, default=False, comment="Manager flag (T/F)")
    permission_group = Column(String(50), nullable=False, comment="Permission group")
    
    @property 
    def full_name(self):
        """Full name property"""
        return f"{self.first_name} {self.last_name}"
    
    def check_password(self, password: str) -> bool:
        """Check password against hash"""
        return self.password == self.hash_password(password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'is_manager': self.is_manager,
            'permission_group': self.permission_group
        }
    
    def __repr__(self):
        return f"<User {self.full_name} ({self.permission_group})>"

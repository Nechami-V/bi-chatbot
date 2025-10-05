"""
Database manager for user authentication
Creates and manages user database with sample Hebrew users
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.user import User, Base
import os
from typing import List, Optional

class UserDatabase:
    """User database manager"""
    
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        # Initialize with sample data
        self.init_sample_users()
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def init_sample_users(self):
        """Initialize database with sample Hebrew users"""
        session = self.get_session()
        
        # Check if users already exist
        if session.query(User).count() > 0:
            session.close()
            return
        
        # Sample Hebrew users with different permission groups
        sample_users = [
            {
                "first_name": "דוד",
                "last_name": "כהן", 
                "phone": "050-1234567",
                "email": "david.cohen@company.com",
                "password": "123456",
                "is_manager": True,
                "permission_group": "admin"
            },
            {
                "first_name": "שרה",
                "last_name": "לוי",
                "phone": "052-2345678", 
                "email": "sarah.levi@company.com",
                "password": "123456",
                "is_manager": True,
                "permission_group": "sales_manager"
            },
            {
                "first_name": "מיכאל",
                "last_name": "אברמוביץ",
                "phone": "053-3456789",
                "email": "michael.abramovich@company.com", 
                "password": "123456",
                "is_manager": False,
                "permission_group": "sales"
            },
            {
                "first_name": "רחל",
                "last_name": "שמואלי",
                "phone": "054-4567890",
                "email": "rachel.shmueli@company.com",
                "password": "123456", 
                "is_manager": False,
                "permission_group": "marketing"
            },
            {
                "first_name": "יוסף",
                "last_name": "רוזנברג",
                "phone": "055-5678901",
                "email": "yosef.rosenberg@company.com",
                "password": "123456",
                "is_manager": False,
                "permission_group": "finance"
            },
            {
                "first_name": "מרים",
                "last_name": "גולדשטיין", 
                "phone": "056-6789012",
                "email": "miriam.goldstein@company.com",
                "password": "123456",
                "is_manager": False,
                "permission_group": "readonly"
            }
        ]
        
        try:
            for user_data in sample_users:
                # Hash password
                user_data["password"] = User.hash_password(user_data["password"])
                
                user = User(**user_data)
                session.add(user)
            
            session.commit()
            # Successfully created users - silent initialization
            
        except Exception as e:
            session.rollback()
            # Silent error handling - users already exist or database issue
        finally:
            session.close()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email).first()
            return user
        finally:
            session.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            return user
        finally:
            session.close()
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password"""
        user = self.get_user_by_email(email)
        if user and user.check_password(password):
            return user
        return None
    
    def get_all_users(self) -> List[User]:
        """Get all users"""
        session = self.get_session()
        try:
            users = session.query(User).all()
            return users
        finally:
            session.close()

# Global database instance
user_db = UserDatabase()
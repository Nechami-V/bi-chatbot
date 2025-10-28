"""
External User Database Manager

Handles connection to SQL Server for user authentication.
Separates user management from the main BI database.
"""

import logging
from sqlalchemy import create_engine , text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional, List
from app.simple_config import config
from app.models.user import User

logger = logging.getLogger(__name__)

class UserDatabaseManager:
    """Manager for external SQL Server user database"""
    
    def __init__(self):
        """Initialize connection to external user database"""
        self.user_db_url = config.USER_DATABASE_URL
        logger.info(f"Connecting to user database: {self.user_db_url[:50]}...")
        
        try:
            # Create engine for user database
            self.user_engine = create_engine(
                self.user_db_url,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,   # Recycle connections every hour
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self.UserSessionLocal = sessionmaker(
                autocommit=False, 
                autoflush=False, 
                bind=self.user_engine
            )
            
            # Test connection
            self._test_connection()
            logger.info("✅ User database connection established successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to user database: {e}")
            raise
    
    def _test_connection(self):
        """Test database connection"""
        try:
            with self.user_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
        except Exception as e:
            raise ConnectionError(f"Cannot connect to user database: {e}")
    
    def get_user_session(self):
        """Get database session for user operations"""
        session = self.UserSessionLocal()
        try:
            yield session
        except Exception as e:
            logger.error(f"User database session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user against SQL Server database"""
        try:
            session = next(self.get_user_session())
            
            # Find user by email
            user = session.query(User).filter(User.email == email).first()
            
            if user and user.check_password(password):
                logger.info(f"✅ User authenticated: {user.email}")
                return user
            else:
                logger.warning(f"❌ Authentication failed for: {email}")
                return None
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID from SQL Server"""
        try:
            session = next(self.get_user_session())
            user = session.query(User).filter(User.id == user_id).first()
            return user
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email from SQL Server"""
        try:
            session = next(self.get_user_session())
            user = session.query(User).filter(User.email == email).first()
            return user
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    def get_all_users(self) -> List[User]:
        """Get all users from SQL Server (for admin purposes)"""
        try:
            session = next(self.get_user_session())
            users = session.query(User).all()
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def check_user_permission(self, user: User, required_permission: str) -> bool:
        """Check if user has required permission"""
        try:
            # Simple permission check based on permission_group
            user_permissions = {
                'admin': ['read', 'write', 'delete', 'manage_users'],
                'manager': ['read', 'write', 'delete'],
                'user': ['read', 'write'],
                'viewer': ['read']
            }
            
            user_group = user.permission_group.lower()
            allowed_permissions = user_permissions.get(user_group, [])
            
            return required_permission.lower() in allowed_permissions
            
        except Exception as e:
            logger.error(f"Error checking permissions for user {user.id}: {e}")
            return False

# Global instance
user_db_manager = UserDatabaseManager()
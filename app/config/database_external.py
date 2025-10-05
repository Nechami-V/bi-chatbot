# External Database Configuration Example
import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ExternalUserService:
    """User service for external database"""
    
    def __init__(self):
        # SQL Server example
        server = os.getenv('DB_SERVER', 'your-server.database.windows.net')
        database = os.getenv('DB_NAME', 'your_database')
        username = os.getenv('DB_USER', 'your_username')
        password = os.getenv('DB_PASSWORD', 'your_password')
        
        connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_user_by_email(self, email: str):
        """Get user from external database"""
        session = self.SessionLocal()
        try:
            # Query existing users table
            result = session.execute("""
                SELECT 
                    user_id,
                    first_name, 
                    last_name,
                    email,
                    password_hash,
                    is_manager,
                    department
                FROM company_users 
                WHERE email = :email AND is_active = 1
            """, {'email': email}).fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'first_name': result[1],
                    'last_name': result[2], 
                    'email': result[3],
                    'password_hash': result[4],
                    'is_manager': result[5],
                    'permission_group': result[6]
                }
            return None
        finally:
            session.close()
    
    def authenticate_user(self, email: str, password: str):
        """Authenticate against external system"""
        user_data = self.get_user_by_email(email)
        
        if user_data:
            # Verify password (depends on external system)
            if self.verify_password(password, user_data['password_hash']):
                return user_data
        return None
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password - adapt to your system"""
        # Example - adapt to your system
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == hashed

# Alternative: Active Directory Integration
class ADUserService:
    """Active Directory authentication"""
    
    def authenticate_user(self, email: str, password: str):
        """Authenticate against Active Directory"""
        try:
            import ldap3
            
            server = ldap3.Server('your-ad-server.com')
            conn = ldap3.Connection(server, user=email, password=password)
            
            if conn.bind():
                # Get user info from AD
                conn.search('dc=company,dc=com', 
                           f'(userPrincipalName={email})',
                           attributes=['displayName', 'department', 'memberOf'])
                
                if conn.entries:
                    user = conn.entries[0]
                    return {
                        'email': email,
                        'full_name': str(user.displayName),
                        'department': str(user.department),
                        'is_manager': 'Managers' in str(user.memberOf)
                    }
            return None
        except Exception as e:
            print(f"AD Authentication failed: {e}")
            return None
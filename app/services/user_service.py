from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.simple_config import config

class UserDatabase:
    def __init__(self):
        self.engine = create_engine(config.USER_DB_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_user_by_email(self, email: str):
        try:
            with self.SessionLocal() as session:
                result = session.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email})
                row = result.fetchone()
                if row:
                    return {"id": row[0], "first_name": row[1], "last_name": row[2], "phone": row[3], "email": row[4], "password": row[5], "is_manager": row[6], "permission_group": row[7]}
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None

user_db = UserDatabase()
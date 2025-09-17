from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create SQLite database in memory for this example
SQLALCHEMY_DATABASE_URL = "sqlite:///./bi_chatbot.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database models
class Customer(Base):
    __tablename__ = "customer"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    city = Column(String, index=True)
    created_at = Column(Date)

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Add sample data
    db = SessionLocal()
    
    # Check if data already exists
    if not db.query(Customer).first():
        from datetime import datetime
        
        sample_customers = [
            {"name": "שרה כהן", "city": "מודיעין עילית", "created_at": "2024-05-01"},
            {"name": "דוד לוי", "city": "ירושלים", "created_at": "2024-06-10"},
            {"name": "רבקה פרידמן", "city": "מודיעין עילית", "created_at": "2024-07-15"},
            {"name": "אברהם יצחק", "city": "בני ברק", "created_at": "2024-07-20"},
            {"name": "משה כץ", "city": "מודיעין עילית", "created_at": "2024-08-01"}
        ]
        
        for customer in sample_customers:
            db.add(Customer(
                name=customer["name"],
                city=customer["city"],
                created_at=datetime.strptime(customer["created_at"], "%Y-%m-%d").date()
            ))
        
        db.commit()
    
    return db

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

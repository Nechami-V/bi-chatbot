from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./bi_chatbot.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Create tables and seed sample data if needed"""
    # Import models so that they are registered with Base
    from app.models.customer import Customer  # noqa: F401
    from app.models.client import Client  # noqa: F401
    from app.models.item import Item  # noqa: F401
    from app.models.order import Order  # noqa: F401
    from app.models.sale import Sale  # noqa: F401
    from app.models.translation_dictionary import TranslationDictionaryModel  # noqa: F401
    
    Base.metadata.create_all(bind=engine)

    # Seed sample data if empty
    db = SessionLocal()
    try:
        # Seed translation dictionary with basic mappings
        if not db.query(TranslationDictionaryModel).first():
            seed_translation_dictionary(db)
            
        # Seed sample customer data if empty  
        if not db.query(Customer).first():
            seed_sample_customers(db)
            
        db.commit()
    finally:
        db.close()


def seed_translation_dictionary(db):
    """Seed the translation dictionary with basic mappings"""
    from app.models.translation_dictionary import TranslationDictionaryModel
    
    mappings = [
        # Customers
        {"client_id": 1, "user_term": "לקוחות", "db_table": "ClientsBot2025", "db_field": "ID_לקוח", "default_agg": "COUNT"},
        {"client_id": 1, "user_term": "לקוחות חדשים", "db_table": "ClientsBot2025", "db_field": "ID_לקוח", "default_agg": "COUNT"},
        {"client_id": 1, "user_term": "מספר לקוחות", "db_table": "ClientsBot2025", "db_field": "ID_לקוח", "default_agg": "COUNT"},
        
        # City
        {"client_id": 1, "user_term": "עיר", "db_table": "ClientsBot2025", "db_field": "city", "default_agg": None},
        {"client_id": 1, "user_term": "ערים", "db_table": "ClientsBot2025", "db_field": "city", "default_agg": None},
        {"client_id": 1, "user_term": "יישוב", "db_table": "ClientsBot2025", "db_field": "city", "default_agg": None},
        
        # Names
        {"client_id": 1, "user_term": "שם פרטי", "db_table": "ClientsBot2025", "db_field": "fname", "default_agg": None},
        {"client_id": 1, "user_term": "שם משפחה", "db_table": "ClientsBot2025", "db_field": "lname", "default_agg": None},
        
        # Items
        {"client_id": 1, "user_term": "פריטים", "db_table": "ItemsBot2025", "db_field": "ID_פריט", "default_agg": "COUNT"},
        {"client_id": 1, "user_term": "מוצרים", "db_table": "ItemsBot2025", "db_field": "ID_פריט", "default_agg": "COUNT"},
        {"client_id": 1, "user_term": "שם פריט", "db_table": "ItemsBot2025", "db_field": "name", "default_agg": None},
        
        # Orders/Sales
        {"client_id": 1, "user_term": "הזמנות", "db_table": "OrdersBot2025", "db_field": "ID_מכירה", "default_agg": "COUNT"},
        {"client_id": 1, "user_term": "מכירות", "db_table": "OrdersBot2025", "db_field": "ID_מכירה", "default_agg": "COUNT"},
        {"client_id": 1, "user_term": "סכום", "db_table": "OrdersBot2025", "db_field": "סכום", "default_agg": "SUM"},
        {"client_id": 1, "user_term": "תאריך", "db_table": "OrdersBot2025", "db_field": "תאריך", "default_agg": None},
    ]
    
    for mapping in mappings:
        db.add(TranslationDictionaryModel(**mapping))


def seed_sample_customers(db):
    from datetime import datetime
    from app.models.customer import Customer

    sample_customers = [
        {"name": "שרה ובר", "city": "מודיעין עילית", "created_at": "2024-05-01"},
        {"name": "נחמי לוי", "city": "ירושלים", "created_at": "2024-06-10"},
        {"name": "רבקה פרידמן", "city": "מודיעין עילית", "created_at": "2024-07-15"},
        {"name": "אברהם יצחק", "city": "בני ברק", "created_at": "2024-07-20"},
        {"name": "משה כץ", "city": "מודיעין עילית", "created_at": "2024-08-01"},
    ]
    for customer in sample_customers:
        db.add(Customer(
            name=customer["name"],
            city=customer["city"],
            created_at=datetime.strptime(customer["created_at"], "%Y-%m-%d").date(),
        ))
    db.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

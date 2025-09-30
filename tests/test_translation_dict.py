#!/usr/bin/env python
"""Direct test without package imports"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import SQLAlchemy directly
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./bi_chatbot.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define TranslationDictionary model
class TranslationDictionaryModel(Base):
    __tablename__ = "translation_dictionary"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, nullable=False, index=True)
    user_term = Column(String, nullable=False, index=True)
    db_table = Column(String, nullable=False)
    db_field = Column(String, nullable=False)
    default_agg = Column(String)
    date_field = Column(String)

# Create tables
print("🔄 Creating tables...")
Base.metadata.create_all(bind=engine)

# Seed data
db = SessionLocal()
try:
    # Check if data exists
    count = db.query(TranslationDictionaryModel).count()
    if count == 0:
        print("📝 Seeding translation dictionary...")
        mappings = [
            {"client_id": 1, "user_term": "לקוחות", "db_table": "ClientsBot2025", "db_field": "ID_לקוח", "default_agg": "COUNT"},
            {"client_id": 1, "user_term": "עיר", "db_table": "ClientsBot2025", "db_field": "city", "default_agg": None},
            {"client_id": 1, "user_term": "פריטים", "db_table": "ItemsBot2025", "db_field": "ID_פריט", "default_agg": "COUNT"},
            {"client_id": 1, "user_term": "סכום", "db_table": "OrdersBot2025", "db_field": "סכום", "default_agg": "SUM"},
        ]
        
        for mapping in mappings:
            db.add(TranslationDictionaryModel(**mapping))
        db.commit()
        
    count = db.query(TranslationDictionaryModel).count()
    print(f"📊 Translation dictionary has {count} entries")
    
    # Show entries
    entries = db.query(TranslationDictionaryModel).all()
    print("📋 All entries:")
    for entry in entries:
        print(f"  - {entry.user_term} → {entry.db_table}.{entry.db_field} ({entry.default_agg})")
    
finally:
    db.close()

print("✅ Translation dictionary is working!")

# Test querying existing tables
print("\n🔍 Testing existing data tables...")
try:
    from sqlalchemy import text
    with engine.connect() as connection:
        # Check ClientsBot2025
        result = connection.execute(text("SELECT COUNT(*) as count FROM ClientsBot2025")).fetchone()
        print(f"📊 ClientsBot2025 has {result[0]} records")
        
        # Check ItemsBot2025  
        result = connection.execute(text("SELECT COUNT(*) as count FROM ItemsBot2025")).fetchone()
        print(f"📊 ItemsBot2025 has {result[0]} records")
        
        # Check OrdersBot2025
        result = connection.execute(text("SELECT COUNT(*) as count FROM OrdersBot2025")).fetchone()
        print(f"📊 OrdersBot2025 has {result[0]} records")
    
    print("🎉 All tests completed successfully!")
    
except Exception as e:
    print(f"❌ Error testing data tables: {e}")
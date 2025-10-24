"""
Database Configuration and Initialization

This module handles database connection, table creation, and seeding
with initial data for the BI Chatbot application.

Key Functions:
- Database engine and session configuration
- Table creation and model registration
- Translation dictionary seeding
- Database dependency injection for FastAPI

Author: BI Chatbot Team
Version: 2.0.0
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.simple_config import config

# Configure logger
logger = logging.getLogger(__name__)

# Database configuration
SQLALCHEMY_DATABASE_URL = config.DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Create tables and seed sample data if needed"""
    try:
        logger.info("Initializing database...")
        
        # Only User model for authentication is required
        pass
        
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Seed sample data if empty
        db = SessionLocal()
        try:
            # Seed translation dictionary with basic mappings
            existing_count = db.query(TranslationDictionaryModel).count()
            if existing_count == 0:
                logger.info("Seeding translation dictionary...")
                seed_translation_dictionary(db)
                db.commit()
                logger.info("Translation dictionary seeded successfully")
            else:
                logger.info(f"Translation dictionary already contains {existing_count} mappings")
                
        finally:
            db.close()
            
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


def seed_translation_dictionary(db):
    """
    Seed the translation dictionary with basic Hebrew-to-database mappings
    
    Args:
        db: SQLAlchemy database session
    """
    from app.models.translation_dictionary import TranslationDictionaryModel
    
    logger.debug("Loading translation dictionary seed data...")
    
    try:
        # Check if already seeded
        existing_count = db.query(TranslationDictionaryModel).count()
        if existing_count > 0:
            logger.debug(f"Translation dictionary already seeded with {existing_count} entries")
            return
        
        logger.info("Seeding translation dictionary with Hebrew term mappings")
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
        
        # orders/sales
        {"client_id": 1, "user_term": "הזמנות", "db_table": "OrdersBot2025", "db_field": "ID_מכירה", "default_agg": "COUNT"},
        {"client_id": 1, "user_term": "מכירות", "db_table": "OrdersBot2025", "db_field": "ID_מכירה", "default_agg": "COUNT"},
        {"client_id": 1, "user_term": "סכום", "db_table": "OrdersBot2025", "db_field": "סכום", "default_agg": "SUM"},
        {"client_id": 1, "user_term": "תאריך", "db_table": "OrdersBot2025", "db_field": "תאריך", "default_agg": None},
    ]
    
        for mapping in mappings:
            db.add(TranslationDictionaryModel(**mapping))
        
        db.commit()
        logger.info(f"Successfully seeded {len(mappings)} translation dictionary entries")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed translation dictionary: {str(e)}")
        raise


def get_db():
    """
    Database dependency injection for FastAPI endpoints
    
    Yields:
        SQLAlchemy database session with automatic cleanup
    """
    logger.debug("Creating database session")
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        logger.debug("Closing database session")
        db.close()
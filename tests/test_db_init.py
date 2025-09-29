#!/usr/bin/env python
"""Test script to initialize database and check translation dictionary"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import init_db, SessionLocal
from app.models.translation_dictionary import TranslationDictionaryModel

print("🔄 Initializing database...")
init_db()

print("✅ Database initialized successfully!")

# Check translation dictionary
db = SessionLocal()
try:
    count = db.query(TranslationDictionaryModel).count()
    print(f"📊 Translation dictionary has {count} entries")
    
    # Show first few entries
    entries = db.query(TranslationDictionaryModel).limit(5).all()
    print("📋 Sample entries:")
    for entry in entries:
        print(f"  - {entry.user_term} → {entry.db_table}.{entry.db_field} ({entry.default_agg})")
        
finally:
    db.close()

print("🎉 Test completed successfully!")
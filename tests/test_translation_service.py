#!/usr/bin/env python
"""Test the new database-backed translation service"""

import sys
import os
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Direct imports to avoid API issues
from app.services.translation_service import TranslationDictionary
from app.db.database import SessionLocal

print("🔄 Testing new database-backed translation service...")

# Test basic functionality
translator = TranslationDictionary(client_id=1)

print("\n📋 Testing term resolution:")
test_terms = ["לקוחות", "עיר", "פריטים", "סכום"]

for term in test_terms:
    try:
        mapping = translator.resolve(term)
        print(f"✅ {term} → {mapping.table}.{mapping.field} ({mapping.default_agg})")
    except Exception as e:
        print(f"❌ {term}: {e}")

print(f"\n📊 Total mappings loaded: {len(translator.get_all_mappings())}")

# Test fuzzy matching
print("\n🔍 Testing fuzzy matching:")
fuzzy_terms = ["לקוח", "לקוחו", "עיירה", "פריט"]

for term in fuzzy_terms:
    try:
        mapping = translator.resolve(term)
        print(f"✅ {term} → {mapping.table}.{mapping.field}")
    except Exception as e:
        print(f"❌ {term}: {e}")

# Test adding new mapping
print("\n➕ Testing adding new mapping:")
success = translator.add_mapping(
    user_term="בעלי עסק",
    db_table="ClientsBot2025", 
    db_field="lname",
    default_agg=None
)
print(f"Add mapping result: {success}")

if success:
    try:
        mapping = translator.resolve("בעלי עסק")
        print(f"✅ New mapping works: בעלי עסק → {mapping.table}.{mapping.field}")
    except Exception as e:
        print(f"❌ New mapping failed: {e}")

print("\n🎉 Translation service test completed!")
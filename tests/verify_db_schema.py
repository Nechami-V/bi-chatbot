"""
Verify database tables were created correctly after migration
"""
import sqlite3
import json

db_path = "bi_chatbot.db"

def check_tables():
    """Check that all expected tables exist"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        'tenants', 'tenant_users', 'sessions', 'usage_daily',
        'saved_reports', 'report_runs', 'quotas', 'external_identities',
        'alembic_version'
    ]
    
    print("=" * 60)
    print("בדיקת טבלאות קיימות")
    print("=" * 60)
    
    all_present = True
    for table in expected_tables:
        exists = table in tables
        status = "✓" if exists else "✗"
        print(f"{status} {table}")
        if not exists:
            all_present = False
    
    print(f"\nטבלאות שנמצאו: {len(tables)}")
    print(f"טבלאות נוספות: {[t for t in tables if t not in expected_tables]}")
    
    conn.close()
    return all_present


def check_table_schema(table_name):
    """Check the schema of a specific table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print(f"\n📊 {table_name}")
    print("-" * 60)
    for col in columns:
        col_id, name, type_, notnull, default, pk = col
        nullable = "NOT NULL" if notnull else "NULL"
        pk_marker = " 🔑" if pk else ""
        print(f"  • {name}: {type_} ({nullable}){pk_marker}")
    
    # Check foreign keys
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    fks = cursor.fetchall()
    if fks:
        print("  Foreign Keys:")
        for fk in fks:
            fk_id, seq, table, from_col, to_col, on_update, on_delete, match = fk
            print(f"    → {from_col} → {table}.{to_col} (ON DELETE {on_delete})")
    
    # Check indexes
    cursor.execute(f"PRAGMA index_list({table_name})")
    indexes = cursor.fetchall()
    if indexes:
        print("  Indexes:")
        for idx in indexes:
            seq, name, unique, origin, partial = idx
            unique_marker = " (UNIQUE)" if unique else ""
            print(f"    📇 {name}{unique_marker}")
    
    conn.close()


def check_alembic_version():
    """Check current Alembic version"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT version_num FROM alembic_version")
        version = cursor.fetchone()
        print("\n" + "=" * 60)
        print(f"Alembic Version: {version[0] if version else 'No version'}")
        print("=" * 60)
    except sqlite3.OperationalError:
        print("\n⚠️  alembic_version table not found")
    
    conn.close()


if __name__ == "__main__":
    print("\n🔍 בדיקת תקינות הדאטהבייס לאחר Migration\n")
    
    # Check tables exist
    tables_ok = check_tables()
    
    if not tables_ok:
        print("\n❌ חסרות טבלאות!")
        exit(1)
    
    # Check each multi-tenant table schema
    print("\n" + "=" * 60)
    print("סכימת הטבלאות")
    print("=" * 60)
    
    for table in ['tenants', 'tenant_users', 'sessions', 'usage_daily', 
                  'saved_reports', 'report_runs', 'quotas', 'external_identities']:
        check_table_schema(table)
    
    # Check Alembic version
    check_alembic_version()
    
    print("\n✅ כל הטבלאות נוצרו בהצלחה!\n")

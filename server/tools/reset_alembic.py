"""
Reset alembic_version table to start fresh with new migrations
"""
import sqlite3
import os

db_path = "bi_chatbot.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop alembic_version table if exists
    cursor.execute("DROP TABLE IF EXISTS alembic_version")
    
    # Also drop old multi-tenant tables if they exist (from old migrations)
    old_tables = [
        'tenants', 'internal_users', 'tenant_users', 'sessions', 
        'usage_daily', 'saved_reports', 'report_runs', 
        'quotas', 'external_identities'
    ]
    
    for table in old_tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"Dropped table: {table}")
        except Exception as e:
            print(f"Could not drop {table}: {e}")
    
    conn.commit()
    conn.close()
    print("\n✅ Database reset successfully - ready for new migrations")
else:
    print(f"Database {db_path} not found")

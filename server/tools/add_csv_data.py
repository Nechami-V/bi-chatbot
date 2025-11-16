# -*- coding: utf-8 -*-
"""
Add CSV data tables to existing database (without dropping DB)
Useful when DB already has other tables (like multi-tenant tables)
"""

import os, csv, sqlite3
from pathlib import Path

# ========= CONFIG =========
DB_PATH = Path(r"C:\bi_chatbot\bi_chatbot.db")
CSV_DIR = Path(r"C:\bi_chatbot\data")

CSV_FILES = {
    "ClientsBot2025": CSV_DIR / "ClientsBot2025.csv",
    "ItemsBot2025":   CSV_DIR / "ItemsBot2025.csv",
    "SalesBot2025":   CSV_DIR / "SalesBot2025.csv",
    "OrdersBot2025":  CSV_DIR / "OrdersBot2025.csv",
}

CSV_HEADERS = {
    "ClientsBot2025": ["ID_לקוח","lname","fname","wname","city"],
    "ItemsBot2025":   ["ID_פריט","name","pgrp"],
    "SalesBot2025":   ["ID_מכירה","week","name"],
    "OrdersBot2025":  ["ID_מכירה","ID_לקוח","ID_פריט","תאריך","סכום"],
}

DDL_TABLES = {
    "ClientsBot2025": """
        CREATE TABLE IF NOT EXISTS "ClientsBot2025" (
          "ID_לקוח" INTEGER PRIMARY KEY,
          "lname"   TEXT,
          "fname"   TEXT,
          "wname"   TEXT,
          "city"    TEXT
        );
    """,
    "ItemsBot2025": """
        CREATE TABLE IF NOT EXISTS "ItemsBot2025" (
          "ID_פריט" INTEGER PRIMARY KEY,
          "name" TEXT,
          "pgrp" INTEGER
        );
    """,
    "SalesBot2025": """
        CREATE TABLE IF NOT EXISTS "SalesBot2025" (
          "ID_מכירה" INTEGER PRIMARY KEY,
          "week" TEXT,
          "name" TEXT
        );
    """,
    "OrdersBot2025": """
        CREATE TABLE IF NOT EXISTS "OrdersBot2025" (
          "row_id"    INTEGER PRIMARY KEY AUTOINCREMENT,
          "ID_מכירה"  INTEGER NOT NULL,
          "ID_לקוח"   INTEGER NOT NULL,
          "ID_פריט"   INTEGER NOT NULL,
          "תאריך"     TEXT,
          "סכום"      REAL,
          FOREIGN KEY("ID_מכירה") REFERENCES "SalesBot2025"("ID_מכירה"),
          FOREIGN KEY("ID_לקוח")  REFERENCES "ClientsBot2025"("ID_לקוח") ON DELETE CASCADE,
          FOREIGN KEY("ID_פריט")  REFERENCES "ItemsBot2025"("ID_פריט")
        );
    """,
}

DDL_INDEXES = {
    "ClientsBot2025": [
        'CREATE INDEX IF NOT EXISTS "ix_ClientsBot2025_ID_לקוח" ON "ClientsBot2025"("ID_לקוח");'
    ],
    "ItemsBot2025": [
        'CREATE INDEX IF NOT EXISTS "ix_ItemsBot2025_ID_פריט" ON "ItemsBot2025"("ID_פריט");'
    ],
    "SalesBot2025": [
        'CREATE INDEX IF NOT EXISTS "ix_SalesBot2025_ID_מכירה" ON "SalesBot2025"("ID_מכירה");'
    ],
    "OrdersBot2025": [
        'CREATE INDEX IF NOT EXISTS "ix_OrdersBot2025_ID_מכירה" ON "OrdersBot2025"("ID_מכירה");',
        'CREATE INDEX IF NOT EXISTS "ix_OrdersBot2025_ID_לקוח" ON "OrdersBot2025"("ID_לקוח");',
        'CREATE INDEX IF NOT EXISTS "ix_OrdersBot2025_ID_פריט" ON "OrdersBot2025"("ID_פריט");',
        'CREATE INDEX IF NOT EXISTS "ix_OrdersBot2025_תאריך" ON "OrdersBot2025"("תאריך");',
    ],
}

# Logical views
DDL_VIEWS = """
DROP VIEW IF EXISTS clients;
CREATE VIEW clients AS 
  SELECT "ID_לקוח" AS id, fname AS first_name, lname AS last_name, 
         wname AS spouse_name, city 
  FROM "ClientsBot2025";

DROP VIEW IF EXISTS customers;
CREATE VIEW customers AS SELECT * FROM clients;

DROP VIEW IF EXISTS items;
CREATE VIEW items AS 
  SELECT "ID_פריט" AS id, name, pgrp AS group_id 
  FROM "ItemsBot2025";

DROP VIEW IF EXISTS sales;
CREATE VIEW sales AS 
  SELECT "ID_מכירה" AS id, week, name 
  FROM "SalesBot2025";

DROP VIEW IF EXISTS orders;
CREATE VIEW orders AS 
  SELECT row_id AS id, "ID_מכירה" AS sale_id, "ID_לקוח" AS customer_id,
         "ID_פריט" AS item_id, "תאריך" AS order_date, "סכום" AS amount
  FROM "OrdersBot2025";
"""


def load_csv_to_table(conn, table_name, csv_path, headers):
    """Load CSV data into table, skipping existing rows"""
    cursor = conn.cursor()
    
    # First, drop the table to reload fresh data
    print(f"  מוחק טבלה קיימת {table_name}...")
    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    
    # Create table
    print(f"  יוצר טבלה {table_name}...")
    cursor.execute(DDL_TABLES[table_name])
    
    # Load data
    print(f"  טוען נתונים מ-{csv_path.name}...")
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            vals = [row.get(h, '').strip() for h in headers]
            rows.append(vals)
        
        placeholders = ','.join(['?'] * len(headers))
        cols_str = ','.join([f'"{h}"' for h in headers])
        
        if table_name == "OrdersBot2025":
            cursor.executemany(
                f'INSERT INTO "{table_name}" ({cols_str}) VALUES ({placeholders})',
                rows
            )
        else:
            cursor.executemany(
                f'INSERT OR IGNORE INTO "{table_name}" ({cols_str}) VALUES ({placeholders})',
                rows
            )
    
    count = cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
    print(f"  ✓ {count} שורות ב-{table_name}")
    
    # Create indexes
    if table_name in DDL_INDEXES:
        print(f"  יוצר אינדקסים עבור {table_name}...")
        for idx_sql in DDL_INDEXES[table_name]:
            cursor.execute(idx_sql)


def main():
    if not DB_PATH.exists():
        print(f"❌ קובץ דאטהבייס לא קיים: {DB_PATH}")
        return
    
    print(f"📂 טוען נתונים מ-CSV אל {DB_PATH}\n")
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Load tables in order (respecting FKs)
    load_order = ["ClientsBot2025", "ItemsBot2025", "SalesBot2025", "OrdersBot2025"]
    
    for tbl in load_order:
        if tbl not in CSV_FILES:
            continue
        csv_path = CSV_FILES[tbl]
        if not csv_path.exists():
            print(f"⚠️  קובץ CSV לא נמצא: {csv_path}")
            continue
        
        print(f"\n🔄 מעבד {tbl}:")
        load_csv_to_table(conn, tbl, csv_path, CSV_HEADERS[tbl])
    
    # Create views
    print(f"\n🔄 יוצר views לוגיים...")
    conn.executescript(DDL_VIEWS)
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ הושלם בהצלחה! הנתונים נטענו אל {DB_PATH}")


if __name__ == "__main__":
    main()

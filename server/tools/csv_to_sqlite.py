# -*- coding: utf-8 -*-
"""
Build SQLite from CSVs + create logical views (idempotent).
Physical tables (per YAML 'physical_table'):
  - ClientsBot2025(ID_לקוח,lname,fname,wname,city)
  - ItemsBot2025(ID_פריט,name,pgrp)
  - SalesBot2025(ID_מכירה,week,name)
  - OrdersBot2025(row_id,ID_מכירה,ID_לקוח,ID_פריט,תאריך,סכום)  -- row_id PK + FKs

Logical views (for queries/templates):
  - clients(id, first_name, last_name, spouse_name, city)
  - items(id, name, group_id)
  - sales(id, week, name)
  - orders(id, sale_id, customer_id, item_id, order_date, amount)
  - customers (compat) -> clients
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
# ========= END CONFIG =====


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
          "name"    TEXT,
          "pgrp"    INTEGER
        );
    """,
    "SalesBot2025": """
        CREATE TABLE IF NOT EXISTS "SalesBot2025" (
          "ID_מכירה" INTEGER PRIMARY KEY,
          "week"     TEXT,
          "name"     TEXT
        );
    """,
    # שימי לב: row_id כ-PK כדי לאפשר כפילויות טבעיות ב-(מכירה/לקוח/פריט)
    "OrdersBot2025": """
        CREATE TABLE IF NOT EXISTS "OrdersBot2025" (
          "row_id"   INTEGER PRIMARY KEY,     -- surrogate key
          "ID_מכירה" INTEGER NOT NULL,
          "ID_לקוח"  INTEGER NOT NULL,
          "ID_פריט"  INTEGER NOT NULL,
          "תאריך"    TEXT,
          "סכום"     REAL,
          FOREIGN KEY ("ID_מכירה") REFERENCES "SalesBot2025"("ID_מכירה") ON DELETE NO ACTION,
          FOREIGN KEY ("ID_לקוח")  REFERENCES "ClientsBot2025"("ID_לקוח") ON DELETE CASCADE,
          FOREIGN KEY ("ID_פריט")  REFERENCES "ItemsBot2025"("ID_פריט") ON DELETE NO ACTION
        );
    """,
}

DDL_INDEXES = """
    CREATE INDEX IF NOT EXISTS "ix_ClientsBot2025_ID_לקוח" ON "ClientsBot2025"("ID_לקוח");
    CREATE INDEX IF NOT EXISTS "ix_ItemsBot2025_ID_פריט"   ON "ItemsBot2025"("ID_פריט");
    CREATE INDEX IF NOT EXISTS "ix_SalesBot2025_ID_מכירה"  ON "SalesBot2025"("ID_מכירה");

    CREATE INDEX IF NOT EXISTS "ix_OrdersBot2025_ID_לקוח"  ON "OrdersBot2025"("ID_לקוח");
    CREATE INDEX IF NOT EXISTS "ix_OrdersBot2025_ID_פריט"  ON "OrdersBot2025"("ID_פריט");
    CREATE INDEX IF NOT EXISTS "ix_OrdersBot2025_ID_מכירה" ON "OrdersBot2025"("ID_מכירה");
    CREATE INDEX IF NOT EXISTS "ix_OrdersBot2025_תאריך"    ON "OrdersBot2025"("תאריך");
"""

DDL_VIEWS = """
    DROP VIEW IF EXISTS customers;
    DROP VIEW IF EXISTS orders;
    DROP VIEW IF EXISTS clients;
    DROP VIEW IF EXISTS items;
    DROP VIEW IF EXISTS sales;

    CREATE VIEW clients AS
    SELECT
      "ID_לקוח" AS id,
      "fname"   AS first_name,
      "lname"   AS last_name,
      "wname"   AS spouse_name,
      "city"    AS city
    FROM "ClientsBot2025";

    CREATE VIEW items AS
    SELECT
      "ID_פריט" AS id,
      "name"    AS name,
      "pgrp"    AS group_id
    FROM "ItemsBot2025";

    CREATE VIEW sales AS
    SELECT
      "ID_מכירה" AS id,
      "week"     AS week,
      "name"     AS name
    FROM "SalesBot2025";

    -- מוסיף id לוגי כדי לתמוך בשאילתות COUNT(o.id)
    CREATE VIEW orders AS
    SELECT
      rowid      AS id,         -- מזהה שורה לוגי של SQLite
      "ID_מכירה" AS sale_id,
      "ID_לקוח"  AS customer_id,
      "ID_פריט"  AS item_id,
      "תאריך"    AS order_date,
      "סכום"     AS amount
    FROM "OrdersBot2025";

    -- תאימות לאחור: יש קוד שקורא customers במקום clients
    CREATE VIEW customers AS
    SELECT * FROM clients;
"""

INSERT_SQL = {
    "ClientsBot2025": 'INSERT INTO "ClientsBot2025" ("ID_לקוח","lname","fname","wname","city") VALUES (?,?,?,?,?)',
    "ItemsBot2025":   'INSERT INTO "ItemsBot2025" ("ID_פריט","name","pgrp") VALUES (?,?,?)',
    "SalesBot2025":   'INSERT INTO "SalesBot2025" ("ID_מכירה","week","name") VALUES (?,?,?)',
    # אין row_id ב-INSERT; SQLite ייצור אותו אוטומטית
    "OrdersBot2025":  'INSERT INTO "OrdersBot2025" ("ID_מכירה","ID_לקוח","ID_פריט","תאריך","סכום") VALUES (?,?,?,?,?)',
}


def safe_delete_db(path: Path):
    if not path.exists():
        return
    try:
        path.unlink()
        print(f"[OK] Deleted old DB: {path}")
    except PermissionError as e:
        raise SystemExit(
            f"לא הצלחתי למחוק את קובץ ה-DB (ייתכן שתהליך מחזיק בו). סגרי VSCode/DB Browser/שרתים ונסי שוב. פירוט: {e}"
        )


def create_schema(conn: sqlite3.Connection):
    cur = conn.cursor()
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    for tbl, sql in DDL_TABLES.items():
        cur.executescript(sql)
    cur.executescript(DDL_INDEXES)
    conn.commit()
    print("[OK] Schema (tables + indexes) created.")


def load_csv_table(conn: sqlite3.Connection, table: str, csv_path: Path):
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    headers = CSV_HEADERS[table]
    insert_sql = INSERT_SQL[table]

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        # אזהרה אם חסרות כותרות
        missing = [h for h in headers if h not in (reader.fieldnames or [])]
        if missing:
            print(f"[WARN] {csv_path.name} missing headers: {missing} (אכניס None עבורן).")

        rows, batch = [], 1000
        cur = conn.cursor()
        for row in reader:
            vals = [row.get(h) if row.get(h) not in ("", None) else None for h in headers]
            # המרת סכום למספר (אם יש פסיקים)
            if table == "OrdersBot2025" and vals[-1] is not None:
                try:
                    vals[-1] = float(str(vals[-1]).replace(",", ""))
                except ValueError:
                    pass
            rows.append(vals)
            if len(rows) >= batch:
                cur.executemany(insert_sql, rows)
                rows.clear()
        if rows:
            cur.executemany(insert_sql, rows)
        conn.commit()
    print(f"[OK] Loaded {table} from {csv_path.name}")


def create_views(conn: sqlite3.Connection):
    conn.executescript(DDL_VIEWS)
    conn.commit()
    print("[OK] Views created (clients/items/sales/orders + customers).")


def verify(conn: sqlite3.Connection):
    cur = conn.cursor()
    objs = cur.execute("""
        SELECT type, name FROM sqlite_master
        WHERE type IN ('table','view') ORDER BY type, name
    """).fetchall()
    print("[INFO] Objects in DB:")
    for t, n in objs:
        print(f"  {t:5}  {n}")
    # ספירה בסיסית
    for name in ["ClientsBot2025","ItemsBot2025","SalesBot2025","OrdersBot2025","clients","items","sales","orders"]:
        try:
            c = cur.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            print(f"  rows({name}): {c}")
        except sqlite3.OperationalError as e:
            print(f"  rows({name}): ERROR ({e})")


def main():
    # 1) מחיקת DB קיים (אם פתוח ע"י תהליך אחר – תופס בשגיאה עם הסבר)
    safe_delete_db(DB_PATH)

    # 2) חיבור ויצירת סכימה
    conn = sqlite3.connect(str(DB_PATH))
    create_schema(conn)

    # 3) טעינת כל ה-CSV לטבלאות הפיזיות
    for tbl, csv_path in CSV_FILES.items():
        load_csv_table(conn, tbl, csv_path)

    # 4) יצירת ה-Views הלוגיים
    create_views(conn)

    # 5) וידוא
    verify(conn)
    conn.close()
    print(f"[DONE] DB ready at: {DB_PATH}")


if __name__ == "__main__":
    main()

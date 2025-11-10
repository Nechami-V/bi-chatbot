# -*- coding: utf-8 -*-
"""
Rebuild SQLite DB from CSVs with logical table/column names (clients/items/sales/orders)
Deletes existing DB, creates tables with PK/FK + indexes, loads data from CSVs.
"""

import os, csv, sqlite3, datetime as dt
from pathlib import Path
from typing import List, Tuple, Dict, Optional

# ========= CONFIG =========
DB_PATH   = Path(r"C:\bi_chatbot\bi_chatbot.db")
CSV_DIR   = Path(r"C:\bi_chatbot\data")

FILES = {
    "clients": CSV_DIR / "ClientsBot2025.csv",
    "items":   CSV_DIR / "ItemsBot2025.csv",
    "sales":   CSV_DIR / "SalesBot2025.csv",
    "orders":  CSV_DIR / "OrdersBot2025.csv",
}

# מיפוי עמודות מקור (CSV) -> עמודות יעד (DB) לכל טבלה
COLUMN_MAP: Dict[str, Dict[str, str]] = {
    "clients": {
        "ID_לקוח": "id",
        "fname": "first_name",
        "lname": "last_name",
        "wname": "spouse_name",
        "city": "city",
    },
    "items": {
        "ID_פריט": "id",
        "name": "name",
        "pgrp": "group_id",
    },
    "sales": {
        "ID_מכירה": "id",
        "week": "week",
        "name": "name",
    },
    "orders": {
        "ID_מכירה": "sale_id",
        "ID_לקוח": "customer_id",
        "ID_פריט": "item_id",
        "תאריך": "order_date",
        "סכום": "amount",
    },
}

# הגדרת סכימה (טיפוסים, PK, FK, אינדקסים)
SCHEMA = {
    "clients": {
        "columns": [
            ("id", "INTEGER"),
            ("first_name", "TEXT"),
            ("last_name", "TEXT"),
            ("spouse_name", "TEXT"),
            ("city", "TEXT"),
        ],
        "pk": ["id"],
        "fks": [],
        "indexes": [("ix_clients_id", ["id"]),
                    ("ix_clients_city", ["city"])],
    },
    "items": {
        "columns": [
            ("id", "INTEGER"),
            ("name", "TEXT"),
            ("group_id", "INTEGER"),
        ],
        "pk": ["id"],
        "fks": [],
        "indexes": [("ix_items_id", ["id"]),
                    ("ix_items_group_id", ["group_id"])],
    },
    "sales": {
        "columns": [
            ("id", "INTEGER"),
            ("week", "TEXT"),
            ("name", "TEXT"),
        ],
        "pk": ["id"],
        "fks": [],
        "indexes": [("ix_sales_id", ["id"]),
                    ("ix_sales_week", ["week"])],
    },
    "orders": {
        "columns": [
            ("sale_id", "INTEGER"),
            ("customer_id", "INTEGER"),
            ("item_id", "INTEGER"),
            ("order_date", "TEXT"),   # נשמר כ-ISO TEXT YYYY-MM-DD או YYYY-MM-DD HH:MM:SS
            ("amount", "REAL"),
        ],
        "pk": [],  # אם יש לך PK מרוכב, הוסיפי כאן, למשל ["sale_id","customer_id","item_id"]
        "fks": [
            ("sale_id",    "sales(id)",    "NO ACTION"),
            ("customer_id","clients(id)",  "CASCADE"),
            ("item_id",    "items(id)",    "NO ACTION"),
        ],
        "indexes": [
            ("ix_orders_sale_id", ["sale_id"]),
            ("ix_orders_customer_id", ["customer_id"]),
            ("ix_orders_item_id", ["item_id"]),
            ("ix_orders_date", ["order_date"]),
        ],
    },
}

# תבניות תאריך נפוצות ב-CSV (אפשר להרחיב אם צריך)
DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
)

# אם True, המרה אוטומטית של עמודת תאריך (orders.order_date) ל-ISO
NORMALIZE_DATES = True

# ========= END CONFIG =========


def parse_date_to_iso(s: Optional[str]) -> Optional[str]:
    if not s or str(s).strip() == "":
        return None
    raw = str(s).strip()
    # כבר בפורמט ISO נכון?
    try:
        # אם זה ISO מלא או YYYY-MM-DD, נסה לפרסר ישירות
        # ננסה קודם ל-ISO מלא:
        dt.datetime.fromisoformat(raw)
        return raw
    except Exception:
        pass
    # נסי תבניות ידועות
    for fmt in DATE_FORMATS:
        try:
            d = dt.datetime.strptime(raw, fmt)
            # אם בפורמט בלי זמן:
            if fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"):
                return d.strftime("%Y-%m-%d")
            else:
                return d.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
    # לא זוהה — שמרי כמו שהוא
    return raw


def drop_db(path: Path):
    try:
        if path.exists():
            path.unlink()
            print(f"[OK] Deleted old DB: {path}")
    except Exception as e:
        raise SystemExit(f"Failed to delete DB: {e}")


def build_table_sql(name: str, meta: dict) -> str:
    cols = []
    for col, typ in meta["columns"]:
        cols.append(f'"{col}" {typ}')
    if meta.get("pk"):
        cols.append('PRIMARY KEY (' + ", ".join(f'"{c}"' for c in meta["pk"]) + ')')
    for (col, ref, ondelete) in meta.get("fks", []):
        cols.append(f'FOREIGN KEY("{col}") REFERENCES {ref} ON DELETE {ondelete}')
    return f'CREATE TABLE "{name}" (\n  ' + ",\n  ".join(cols) + "\n);"


def create_tables(conn: sqlite3.Connection):
    cur = conn.cursor()
    for tname, meta in SCHEMA.items():
        sql = build_table_sql(tname, meta)
        cur.execute(sql)
    conn.commit()
    print("[OK] Created tables.")


def create_indexes(conn: sqlite3.Connection):
    cur = conn.cursor()
    for tname, meta in SCHEMA.items():
        for ix_name, cols in meta.get("indexes", []):
            cols_sql = ", ".join(f'"{c}"' for c in cols)
            cur.execute(f'CREATE INDEX IF NOT EXISTS "{ix_name}" ON "{tname}" ({cols_sql});')
    conn.commit()
    print("[OK] Created indexes.")


def load_csv(conn: sqlite3.Connection, table: str, csv_path: Path, column_map: Dict[str, str]):
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    # עמודות יעד לפי הסכימה שהגדרנו ל-DB
    target_cols = [c for c, _ in SCHEMA[table]["columns"]]

    # בדיקת מיפוי: כל עמודת יעד חייבת להיות ממופה או לבחור להשאיר None
    # כאן נשתמש במיפוי הנתון בלבד—עמודות יעד שלא במיפוי יקבלו None.
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        src_cols = reader.fieldnames or []
        missing_src = [src for src in column_map.keys() if src not in src_cols]
        if missing_src:
            print(f"[WARN] Missing CSV headers for table '{table}': {missing_src}")

        rows = []
        for row in reader:
            # בונים רשימת ערכים ליעד לפי סדר target_cols
            values = []
            for dst_col in target_cols:
                # מוצאים את מקור ה-CSV שממופה לעמודת היעד
                src_for_dst = None
                for src_col, mapped_dst in column_map.items():
                    if mapped_dst == dst_col:
                        src_for_dst = src_col
                        break
                v = row.get(src_for_dst) if src_for_dst else None

                # המרות קלות:
                if table == "orders" and dst_col == "order_date" and NORMALIZE_DATES:
                    v = parse_date_to_iso(v)
                elif table == "orders" and dst_col == "amount":
                    v = (None if v in (None, "") else float(str(v).replace(",", "")))
                else:
                    # המרת ריק ל-None
                    v = None if (v is None or str(v).strip() == "") else v

                values.append(v)
            rows.append(values)

    ph = ", ".join(["?"] * len(target_cols))
    columns_sql = ", ".join([f'"{c}"' for c in target_cols])
    sql = f'INSERT INTO "{table}" ({columns_sql}) VALUES ({ph})'
    # טעינה בבאצ'ים
    cur = conn.cursor()
    BATCH = 1000
    for i in range(0, len(rows), BATCH):
        cur.executemany(sql, rows[i:i+BATCH])
    conn.commit()
    print(f"[OK] Loaded {len(rows):,} rows into {table} from {csv_path.name}")


def verify_counts(conn: sqlite3.Connection):
    cur = conn.cursor()
    for t in SCHEMA.keys():
        c = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f"  {t}: {c:,} rows")


def main():
    # מחיקה ובנייה מחדש
    drop_db(DB_PATH)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    # יצירת טבלאות
    create_tables(conn)

    # טעינת נתונים לכל טבלה
    for tname, csv_path in FILES.items():
        load_csv(conn, tname, csv_path, COLUMN_MAP[tname])

    # אינדקסים
    create_indexes(conn)

    print("[OK] Rebuild complete. Row counts:")
    verify_counts(conn)
    conn.close()
    print(f"[DONE] DB at: {DB_PATH}")


if __name__ == "__main__":
    main()

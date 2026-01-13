from sqlalchemy import text
from .db import get_engine
from shared.contracts import ExecuteResponse
from datetime import date, datetime
from decimal import Decimal

def _json_safe(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v

def execute_sql(sql: str, preview_rows: int = 20) -> ExecuteResponse:
    print("  [EXECUTOR] Executing SQL...")
    engine = get_engine()

    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            columns = list(result.keys())

            rows_raw = result.fetchmany(preview_rows + 1)
            has_more = len(rows_raw) > preview_rows
            rows_raw = rows_raw[:preview_rows]

            rows = []
            for row in rows_raw:
                d = dict(zip(columns, row))
                rows.append({k: _json_safe(v) for k, v in d.items()})

        print(f"  [EXECUTOR] Success. Rows fetched: {len(rows)}")
        return ExecuteResponse(
            columns=columns,
            rows=rows,
            preview_count=len(rows),
            has_more=has_more,
            row_count=None, 
            error=None,
        )

    except Exception as e:
        print(f"  [EXECUTOR] Error: {str(e)}")
        return ExecuteResponse(
            columns=[],
            rows=[],
            preview_count=0,
            has_more=False,
            row_count=None, 
            error=str(e),
        )

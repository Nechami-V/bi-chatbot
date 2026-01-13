# services/nl2sql/guardrails.py
from __future__ import annotations

import re

def validate_sql_against_semantic_rules(sql: str, semantic: dict) -> None:
    if not sql or not sql.strip():
        raise ValueError("Empty SQL")

    s = sql.strip()
    lowered = s.lower().lstrip()

    # 1) Allow only SELECT/WITH
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise ValueError("Only SELECT/WITH queries are allowed")

    # 2) Block T-SQL variables / parameters (your executor doesn't bind them)
    if re.search(r"@\w+", s):
        raise ValueError("SQL contains T-SQL variables (@...). Inline dates using GETDATE/DATEADD instead.")

    # 3) Catch broken CTE pattern: ') SELECT' but query doesn't start with WITH
    # Example you got:  ... GROUP BY ... ) SELECT TOP 10 ...
    if re.search(r"\)\s*select", lowered, flags=re.IGNORECASE) and not lowered.startswith("with"):
        raise ValueError("CTE syntax error: found ') SELECT' but query does not start with WITH <cte> AS (...).")

    # 4) Optional: if it references a CTE name, ensure WITH exists for that name (common failure)
    # This catches: FROM ClientExpenses ... but no WITH ClientExpenses AS (
    m = re.search(r"\bfrom\s+([a-z_][a-z0-9_]*)\b", lowered)
    if m:
        cte_name = m.group(1)
        # only enforce for names that "look like" a CTE (you can keep it simple for your common ones)
        if cte_name in {"clientexpenses", "aggregatedorders", "weeksagg", "weeksordered"}:
            if not re.search(rf"\bwith\s+{re.escape(cte_name)}\s+as\s*\(", lowered):
                raise ValueError(f"CTE '{cte_name}' referenced but missing 'WITH {cte_name} AS (...)'.")

    # 5) Enforce your items join rule (based on your findings)
    if re.search(r"\bitem_salesid\s*=\s*w_items\.itemid\b", lowered):
        raise ValueError("Forbidden join: item_salesID must join to W_items.id (not W_items.itemid).")

    # If you want it stricter: block any use of W_items.itemid in joins
    if re.search(r"\bjoin\s+w_items\b", lowered) and re.search(r"\bw_items\.itemid\b", lowered):
        raise ValueError("W_items.itemid should not be used for joins. Use W_items.id.")

    # 6) Existing forbidden patterns from semantic map (keep this last)
    for pat in semantic.get("forbidden_patterns", []):
        if re.search(pat, s, flags=re.IGNORECASE | re.DOTALL):
            raise ValueError(f"Forbidden SQL pattern matched: {pat}")

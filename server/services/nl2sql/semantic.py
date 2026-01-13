from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

SEMANTIC_MAP_PATH = Path("config/semantic_map.json")

@lru_cache(maxsize=1)
def load_semantic_map() -> dict:
    path = SEMANTIC_MAP_PATH
    if not path.exists():
        raise FileNotFoundError(f"Semantic map file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle) 

def apply_semantic_mapping(question: str, semantic: dict) -> tuple[str, str]:
    q2 = question
    for item in semantic.get("term writes", []):
        src = item.get("from")
        dst = item.get("to")
        if src and dst:
            q2 = q2.replace(src, dst)
    rules_lines = []
    rules_lines.append("CRITICAL SQL RULES (MUST FOLLOW):")
    rules_lines.append("4) Context hints for this question:")
    added = 0
    for h in semantic.get("sql_hints", []):
        term = h.get("term")
        hint = h.get("hint")
        if term and hint and term in q2:
            rules_lines.append(f"   - {hint}")
            added += 1
    if added == 0:
        rules_lines.append("   - (no extra hints)")

    return q2, "\n".join(rules_lines)
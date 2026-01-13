from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from shared.settings import META_SCHEMA_PATH

@dataclass(frozen=True)
class MetaSchema:
    raw: Dict[str, Any]
    warnings: List[str]
    cols_by_table: Dict[str, Set[str]]

_SCHEMA_CACHE: MetaSchema | None = None

def load_meta_schema(force_reload: bool = False) -> MetaSchema:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is not None and not force_reload:
        return _SCHEMA_CACHE

    path = Path(META_SCHEMA_PATH)
    raw = json.loads(path.read_text(encoding="utf-8"))

    tables = raw.get("MetaTables", [])
    cols = raw.get("MetaColumns", [])
    rels = raw.get("MetaRelations", [])

    # map TableID -> TableName
    tableid_to_name = {t["TableID"]: t["TableName"] for t in tables if "TableID" in t and "TableName" in t}

    # columns lookup: TableName -> set(ColumnName)
    cols_by_table: Dict[str, Set[str]] = {}
    for c in cols:
        tname = tableid_to_name.get(c.get("TableID"))
        cname = c.get("ColumnName")
        if tname and cname:
            cols_by_table.setdefault(tname, set()).add(cname)

    # sanity checks על Relations מול Columns
    warnings: List[str] = []
    for r in rels:
        ft, fc = r.get("FromTable"), r.get("FromColumn")
        tt, tc = r.get("ToTable"), r.get("ToColumn")

        if ft and ft not in cols_by_table:
            warnings.append(f"[REL] FromTable missing in MetaColumns: {ft}")
        if tt and tt not in cols_by_table:
            warnings.append(f"[REL] ToTable missing in MetaColumns: {tt}")
        if ft and fc and fc not in cols_by_table.get(ft, set()):
            warnings.append(f"[REL] Missing column: {ft}.{fc}")
        if tt and tc and tc not in cols_by_table.get(tt, set()):
            warnings.append(f"[REL] Missing column: {tt}.{tc}")

    _SCHEMA_CACHE = MetaSchema(raw=raw, warnings=warnings, cols_by_table=cols_by_table)
    return _SCHEMA_CACHE
def build_prompt_schema_text(schema: MetaSchema, max_tables: int = 30) -> str:
    raw = schema.raw
    tables = raw.get("MetaTables", [])
    cols = raw.get("MetaColumns", [])
    rels = raw.get("MetaRelations", [])
    defaults = raw.get("MetaDefaults", [])

    # TableID -> TableName
    tableid_to_name = {t["TableID"]: t["TableName"] for t in tables}

    # group columns by table name
    cols_grouped: Dict[str, List[Dict[str, Any]]] = {}
    for c in cols:
        tname = tableid_to_name.get(c.get("TableID"))
        if tname:
            cols_grouped.setdefault(tname, []).append(c)

    lines: List[str] = []
    lines.append("SQL Server schema (from MetaTables/MetaColumns):")

    for t in tables[:max_tables]:
        tname = t["TableName"]
        lines.append(f"TABLE {tname} - {t.get('Description','')}:")
        for c in cols_grouped.get(tname, [])[:60]:
            aliases = c.get("Aliases")
            alias_txt = f" (aliases: {aliases})" if aliases else ""
            lines.append(f"  - {c['ColumnName']} ({c.get('DataType','')}) - {c.get('Description','')}{alias_txt}")

    lines.append("RELATIONSHIPS:")
    for r in rels[:80]:
        ft, fc = r.get("FromTable"), r.get("FromColumn")
        tt, tc = r.get("ToTable"), r.get("ToColumn")
        if not (ft and fc and tt and tc):
            continue
        if fc in schema.cols_by_table.get(ft, set()) and tc in schema.cols_by_table.get(tt, set()):
            lines.append(f"  - {ft}.{fc} -> {tt}.{tc} ({r.get('Description','')})")

    if defaults:
        lines.append("DEFAULTS:")
        for d in defaults[:30]:
            lines.append(f"  - {d.get('DefaultName')}={d.get('DefaultValue')} ({d.get('Description','')})")

    return "\n".join(lines)

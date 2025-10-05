"""
AI Service - Natural Language Processing for Business Intelligence

This service provides AI-powered natural language understanding for converting
Hebrew business questions into SQL queries and generating intelligent responses.

Key Features:
- OpenAI GPT integration for natural language processing
- Database schema analysis and understanding
- Hebrew language support for business terms
- SQL query generation and validation
- Natural language response generation
- Measures execution time for each operation

Author: BI Chatbot Team
Version: 2.1.0
"""

import logging
import time
from openai import OpenAI
from typing import Dict, List, Optional, Any
import json
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from app.simple_config import config

# Configure logger
logger = logging.getLogger(__name__)


class AIService:
    """
    AI Service for Natural Language to SQL Processing
    
    This service handles all AI-related operations for the BI Chatbot system,
    enabling users to ask business questions in Hebrew and receive intelligent
    answers based on database analysis.
    """

    def __init__(self, db: Session, system_prompt: Optional[str] = None):
        self.db = db
        self.system_prompt = system_prompt or (
            "You are a helpful BI assistant that converts Hebrew business questions into SQL and answers clearly."
        )
        self.schema_info = self._analyze_database_schema()

        if not config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured. Please set OPENAI_API_KEY.")

        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        logger.info("AI Service initialized successfully")

    def _analyze_database_schema(self) -> Dict[str, Any]:
        logger.info("Analyzing database schema...")
        inspector = inspect(self.db.get_bind())
        schema = {"tables": {}, "relationships": []}
        relevant_tables = config.BUSINESS_TABLES

        for table_name in relevant_tables:
            if table_name not in inspector.get_table_names():
                logger.warning(f"Table {table_name} not found in database")
                continue

            columns = [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": col.get("default"),
                    "primary_key": col.get("primary_key", False),
                }
                for col in inspector.get_columns(table_name)
            ]

            primary_keys = [c["name"] for c in columns if c.get("primary_key", False)]
            foreign_keys = [
                {
                    "constrained_columns": fk["constrained_columns"],
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"],
                }
                for fk in inspector.get_foreign_keys(table_name)
            ]

            schema["tables"][table_name] = {
                "columns": columns,
                "primary_key": primary_keys,
                "foreign_keys": foreign_keys,
            }

            for fk in foreign_keys:
                schema["relationships"].append(
                    {
                        "from_table": table_name,
                        "from_columns": fk["constrained_columns"],
                        "to_table": fk["referred_table"],
                        "to_columns": fk["referred_columns"],
                    }
                )

        return schema

    def generate_sql(self, question: str) -> Dict[str, Any]:
        start_time = time.perf_counter()
        # Rule-based fast path for very common intents to avoid LLM latency
        shortcut = self._rule_sql_shortcut(question)
        if shortcut:
            total = time.perf_counter() - start_time
            shortcut['duration_sec'] = total
            return shortcut
        attempts = max(1, getattr(config, "OPENAI_MAX_RETRIES", 3))
        last_raw = None
        last_error = None
        # Try fastest/shortest first: select-only -> soft -> strict JSON
        modes = ["select", "soft", "strict"]

        for i in range(min(attempts, len(modes))):
            mode = modes[i]
            try:
                t0 = time.perf_counter()
                if mode == "select":
                    prompt = self._build_select_prompt(question)
                else:
                    prompt = self._build_sql_prompt(question)
                    if mode == "strict":
                        prompt += "\nReturn only valid JSON in a single line, no explanations, no code fences, no extra text."

                logger.info(f"Generating SQL (mode={mode}, attempt {i+1}/{attempts})")
                response = self._call_openai_for_sql(prompt, mode=mode)
                elapsed = time.perf_counter() - t0
                logger.info(f"SQL generation via OpenAI took {elapsed:.2f} seconds")

                last_raw = response

                if mode == "select":
                    select_sql = self._extract_select_sql(response)
                    if select_sql:
                        total = time.perf_counter() - start_time
                        return {
                            "success": True,
                            "sql": select_sql,
                            "tables": [],
                            "description": "SELECT extracted from model response",
                            "raw_response": response,
                            "error": None,
                            "duration_sec": total,
                        }
                    last_error = "No valid SELECT found in select-mode response"
                    continue

                parsed = self._parse_sql_response(response)
                if parsed.get("success") and (parsed.get("sql") or "").strip():
                    total = time.perf_counter() - start_time
                    parsed["duration_sec"] = total
                    logger.info(f"✅ Full SQL generation succeeded in {total:.2f} seconds")
                    return parsed

                last_error = parsed.get("error") or "Empty SQL after parse"

            except Exception as e:
                last_error = str(e)
                logger.warning(f"SQL generation attempt (mode={mode}) failed: {last_error}")
                continue

        total = time.perf_counter() - start_time
        logger.error(f"❌ SQL generation failed after {total:.2f} seconds. Error: {last_error}")
        return {
            "success": False,
            "error": last_error or "SQL generation returned empty result",
            "sql": "",
            "tables": [],
            "description": "",
            "raw_response": last_raw,
            "duration_sec": total,
        }

    def _build_sql_prompt(self, question: str) -> str:
        tables_summary = self._select_relevant_tables(question)
        schema_brief = json.dumps(tables_summary, ensure_ascii=False)
        return (
            f"{self.system_prompt}\n"
            "Convert Hebrew question to valid SQL for SQLite. Use column names as-is. Join only if necessary. Avoid unsupported functions. Return JSON in a single line.\n"
            f"SCHEMA: {schema_brief}\n"
            f"QUESTION: {question}\n"
            'JSON: {"sql":"...","tables":["..."],"description":"..."}'
        )

    def _build_select_prompt(self, question: str) -> str:
        tables_summary = self._select_relevant_tables(question)
        schema_brief = json.dumps(tables_summary, ensure_ascii=False)
        return (
            f"{self.system_prompt}\n"
            "Convert Hebrew question to a single valid SELECT SQL for SQLite. Use column names as-is. Join only if necessary. Return only SQL, no extra text.\n"
            f"SCHEMA: {schema_brief}\n"
            f"QUESTION: {question}\n"
            "SELECT ONLY"
        )
    
    def _select_relevant_tables(self, question: str) -> Dict[str, List[str]]:
        """Heuristically filter schema tables/columns based on Hebrew keywords in the question."""
        q = (question or "").lower()
        want_clients = any(k in q for k in ["לקוח", "לקוחות", "עיר"])  # customers/city
        want_orders  = any(k in q for k in ["מכירה", "מכירות", "הזמנה", "סכום", "סה""כ", "sum"]) 
        want_items   = any(k in q for k in ["פריט", "מוצר"]) 
        want_sales   = any(k in q for k in ["week", "שבוע", "שם", "name"]) 

        tables = {}
        def add_table(tname: str):
            meta = self.schema_info.get("tables", {}).get(tname)
            if not meta:
                return
            tables[tname] = [c["name"] for c in meta.get("columns", [])]

        if want_clients:
            add_table("ClientsBot2025")
        if want_orders:
            add_table("OrdersBot2025")
        if want_items:
            add_table("ItemsBot2025")
        if want_sales:
            add_table("SalesBot2025")

        # Fallback: include all if nothing matched
        if not tables:
            for tname, meta in self.schema_info.get("tables", {}).items():
                tables[tname] = [c["name"] for c in meta.get("columns", [])]
        return tables

    def _call_openai_for_sql(self, prompt: str, mode: str = "strict") -> str:
        sql_tokens = min(256, getattr(config, "MAX_TOKENS", 1000))
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        response = self.client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            max_completion_tokens=sql_tokens,
        )
        return response.choices[0].message.content

    def _rule_sql_shortcut(self, question: str) -> Optional[Dict[str, Any]]:
        """Heuristic shortcuts: handle 'כמה לקוחות' with/without city without calling LLM.
        Returns a parsed-like dict or None if not applicable.
        """
        if not question:
            return None
        q = question.strip()
        q_low = q.lower()
        # Detect intent: count customers
        if ('כמה' in q_low) and ('לקוח' in q_low or 'לקוחות' in q_low):
            # Try extract city after a 'ב' preposition near the end
            import re
            # Examples: "כמה לקוחות יש בחיפה", "כמה לקוחות יש בעיר חיפה"
            # Prefer last ' ב' occurrence to catch city phrase
            city = None
            m = re.search(r"\sב([^?.!,]+)$", q)
            if m:
                city = m.group(1).strip()
                # Clean wrapping words like 'עיר', 'בעיר'
                city = re.sub(r"^(עיר|בעיר)\s+", "", city).strip()
                # Remove trailing words like 'יש' if miscaptured
                city = city.replace('יש', '').strip()
                # Remove quotes
                city = city.strip("'\"")

            if city:
                safe_city = city.replace("'", "''").strip()
                sql = (
                    "SELECT COUNT(*) AS customer_count FROM ClientsBot2025 "
                    f"WHERE TRIM(city) = '{safe_city}' OR TRIM(city) LIKE '{safe_city}%'"
                )
                return {
                    'success': True,
                    'sql': sql,
                    'tables': ['ClientsBot2025'],
                    'description': f"ספירת לקוחות בעיר {city}",
                    'raw_response': None,
                    'error': None,
                }
            else:
                sql = "SELECT COUNT(*) AS customer_count FROM ClientsBot2025;"
                return {
                    'success': True,
                    'sql': sql,
                    'tables': ['ClientsBot2025'],
                    'description': "סך כל הלקוחות",
                    'raw_response': None,
                    'error': None,
                }
        return None

    def _extract_json_block(self, text: str) -> Optional[str]:
        if not text:
            return None
        import re
        fence = re.search(r"```\s*json\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
        if fence:
            return fence.group(1)
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1].strip()
        return None

    def _extract_select_sql(self, text: str) -> Optional[str]:
        if not text:
            return None
        import re
        m = re.search(r"(?is)\bselect\b[\s\S]+?\bfrom\b[\s\S]+?(?:;|$)", text)
        if not m:
            return None
        candidate = m.group(0).strip()
        if len(candidate) < 20:
            return None
        return candidate

    def _parse_sql_response(self, content: str) -> Dict[str, Any]:
        try:
            result = json.loads(content)
            sql_text = (result.get("sql") or "").strip()
            success = bool(sql_text)
            return {
                "success": success,
                "sql": sql_text,
                "tables": result.get("tables", []),
                "description": result.get("description", ""),
                "raw_response": content,
                "error": None if success else "Empty SQL in JSON response",
            }
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response, trying JSON block or SELECT")
            json_block = self._extract_json_block(content)
            if json_block:
                try:
                    result = json.loads(json_block)
                    sql_text = (result.get("sql") or "").strip()
                    success = bool(sql_text)
                    return {
                        "success": success,
                        "sql": sql_text,
                        "tables": result.get("tables", []),
                        "description": result.get("description", ""),
                        "raw_response": content,
                        "error": None if success else "Empty SQL in extracted JSON",
                    }
                except Exception as inner:
                    logger.warning(f"Extracted JSON block failed: {inner}")
            select_sql = self._extract_select_sql(content)
            if select_sql:
                return {
                    "success": True,
                    "sql": select_sql,
                    "tables": [],
                    "description": "Extracted SQL from text",
                    "raw_response": content,
                    "error": None,
                }
            return {
                "success": False,
                "sql": "",
                "tables": [],
                "description": "",
                "raw_response": content,
                "error": "Unable to parse or extract SQL from model response",
            }

    def execute_query(self, sql: str) -> Dict[str, Any]:
        start_time = time.perf_counter()
        try:
            logger.debug(f"Executing SQL: {sql}")
            result = self.db.execute(text(sql))
            if sql.strip().lower().startswith("select"):
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                elapsed = time.perf_counter() - start_time
                logger.info(f"✅ Query executed in {elapsed:.2f} sec, {len(rows)} rows returned")
                return {"success": True, "results": rows, "row_count": len(rows), "duration_sec": elapsed}
            else:
                self.db.commit()
                elapsed = time.perf_counter() - start_time
                logger.info(f"✅ Non-SELECT query executed in {elapsed:.2f} sec")
                return {"success": True, "row_count": result.rowcount, "message": f"Query executed in {elapsed:.2f} sec", "duration_sec": elapsed}
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"❌ Query failed after {elapsed:.2f} sec: {str(e)}")
            self.db.rollback()
            return {"success": False, "error": str(e), "duration_sec": elapsed}

    def generate_response(self, question: str, query_results: Dict[str, Any]) -> str:
        start_time = time.perf_counter()
        try:
            sample = query_results.get("results", [])[:1]
            columns = list(sample[0].keys()) if sample else []
            prompt = (
                "כתוב משפט קצר אחד בעברית תקנית העונה ישירות על השאלה. אין טבלאות ואין קוד. "
                "שלב בשם היישות (למשל עיר/שבוע/שם) ובמספרים מן הנתונים. החזר משפט אחד בלבד.\n"
                f"השאלה: {question}\n"
                f"עמודות: {json.dumps(columns, ensure_ascii=False)}\n"
                f"דוגמה נתונים: {json.dumps(sample, ensure_ascii=False, default=str)}\n"
            )
            ans_tokens = min(160, getattr(config, "MAX_TOKENS", 1000))
            try:
                response = self.client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "אתה מסביר תוצאות במשפט אחד בעברית. החזר טקסט בלבד."},
                        {"role": "user", "content": prompt},
                    ],
                    max_completion_tokens=ans_tokens,
                )
                ai_response = (response.choices[0].message.content or "").strip()
            except Exception as e:
                # Any OpenAI error (including network filters/HTML blocks) → deterministic fallback
                msg = (str(e) or "").lower()
                if "netfree" in msg or "<html" in msg:
                    logger.warning("OpenAI call appears blocked by network filter; using deterministic fallback.")
                # Deterministic fallback based on query results
                rows = query_results.get("results", [])
                rc = query_results.get("row_count", 0)
                if rc == 0:
                    return "לא נמצאו תוצאות לשאלה שלך."
                if rc == 1 and rows:
                    row = rows[0]
                    if len(row) == 1:
                        val = list(row.values())[0]
                        return f"התוצאה היא {val}."
                    parts = [f"{k}: {v}" for k, v in row.items()]
                    return "התוצאה: " + ", ".join(parts)
                return f"התקבלו {rc} תוצאות עבור השאלה."
            elapsed = time.perf_counter() - start_time
            logger.info(f"🗣️ Response generation took {elapsed:.2f} sec")
            # If the first attempt is empty or too generic, try a stricter second pass
            def _too_generic(txt: str) -> bool:
                return (not txt) or txt.startswith("נמצאו ")

            if _too_generic(ai_response):
                prompt2 = (
                    "חבר משפט אחד ברור בעברית שמכיל את הערכים מן הנתונים ועונה ישירות לשאלה. "
                    "אל תכתוב את התבנית 'נמצאו X תוצאות'. אל תכתוב קוד או רשימות. כתוב משפט ספציפי בלבד.\n"
                    f"השאלה: {question}\n"
                    f"עמודות: {json.dumps(columns, ensure_ascii=False)}\n"
                    f"דוגמה נתונים: {json.dumps(sample, ensure_ascii=False, default=str)}\n"
                )
                response2 = self.client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "אתה כותב תשובה במשפט אחד בעברית. אין טבלאות ואין קוד."},
                        {"role": "user", "content": prompt2},
                    ],
                    max_completion_tokens=ans_tokens,
                )
                ai_response2 = (response2.choices[0].message.content or "").strip()
                if not _too_generic(ai_response2):
                    return ai_response2

            # Deterministic minimal fallback if model still failed
            rows = query_results.get("results", [])
            rc = query_results.get("row_count", 0)
            if rc == 0:
                return "לא נמצאו תוצאות לשאלה שלך."
            if rc == 1 and rows:
                row = rows[0]
                if len(row) == 1:
                    val = list(row.values())[0]
                    return f"התוצאה היא {val}."
                # Multi-column single row: join key facts
                parts = []
                for k, v in row.items():
                    parts.append(f"{k}: {v}")
                return "התוצאה: " + ", ".join(parts)
            return f"התקבלו {rc} תוצאות עבור השאלה."
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"❌ Error generating response after {elapsed:.2f} sec: {str(e)}")
            return f"אירעה שגיאה ביצירת התשובה: {str(e)}"

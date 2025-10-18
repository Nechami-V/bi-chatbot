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

    def generate_sql(self, question: str, context_block: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate SQL query from natural language question.
        
        Args:
            question: User's question in Hebrew
            context_block: Optional compact context for follow-up questions
            
        Returns:
            Dict with success, sql, and optional error
        """
        start_time = time.perf_counter()

        prompt = self._build_sql_prompt(question, context_block)
        last_raw = None
        try:
            t0 = time.perf_counter()
            response = self._call_openai_for_sql(prompt)
            elapsed = time.perf_counter() - t0
            logger.info(f"SQL generation via OpenAI took {elapsed:.2f} seconds")
            last_raw = response

            parsed = self._parse_sql_response(response)
            if parsed.get("success") and (parsed.get("sql") or "").strip():
                total = time.perf_counter() - start_time
                parsed["duration_sec"] = total
                logger.info(f"✅ Full SQL generation succeeded in {total:.2f} seconds")
                return parsed

            error = parsed.get("error") or "Empty SQL after parse"
        except Exception as e:
            error = str(e)

        total = time.perf_counter() - start_time
        logger.error(f"❌ SQL generation failed after {total:.2f} seconds. Error: {error}")
        return {
            "success": False,
            "error": error or "SQL generation returned empty result",
            "sql": "",
            "tables": [],
            "description": "",
            "raw_response": last_raw,
            "duration_sec": total,
        }
    def _build_sql_prompt(self, question: str, context_block: Optional[str] = None) -> str:
        """
        Build SQL generation prompt with optional follow-up context.
        
        Args:
            question: User's question in Hebrew
            context_block: Optional compact context for follow-up questions
            
        Returns:
            Formatted prompt string
        """
        db = "SQLite"
        tables_summary = self._select_relevant_tables(question)
        schema_brief = json.dumps({"tables": tables_summary}, ensure_ascii=False)
        
        base_prompt = (
            f"Translate the following Hebrew business question into one valid and optimized SQL SELECT query for {db}. "
            "Use only the table and column names exactly as they appear in the provided SCHEMA. "
            "Use JOINs only when they are truly necessary. "
            "Do not invent tables or columns that do not exist in the SCHEMA. "
            "Return only the SQL query itself — no explanations, no comments, no markdown, and no extra text.\n\n"
            f"SCHEMA: {schema_brief}\n"
        )
        
        # Inject context block if this is a follow-up
        if context_block:
            base_prompt += f"\n{context_block}\n\n"
        
        base_prompt += (
            f"QUESTION (Hebrew): {question}\n\n"
            "Output: SQL query only."
        )
        
        return base_prompt

    def _select_relevant_tables(self, question: str) -> Dict[str, List[str]]:
        """Send full schema every time (table → column names)"""
        return {
            tname: [c["name"] for c in meta.get("columns", [])]
            for tname, meta in self.schema_info.get("tables", {}).items()
        }

    def _call_openai_for_sql(self, prompt: str, mode: str = "strict") -> str:
        sql_tokens = min(256, getattr(config, "MAX_TOKENS", 1000))
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        logger.info(f"Sending to OpenAI - Prompt: {prompt[:200]}...")
        response = self.client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            max_completion_tokens=sql_tokens,
        )
        ai_content = response.choices[0].message.content
        logger.info(f"OpenAI returned: {ai_content}")
        
        if not ai_content or not ai_content.strip():
            logger.error("OpenAI returned empty response!")
            return '{"sql":"","tables":[],"description":"","error":"Empty response from OpenAI"}'
        
        return ai_content

    def _rule_sql_shortcut(self, question: str) -> Optional[Dict[str, Any]]:
        """Heuristic shortcuts: handle 'כמה לקוחות' with/without city without calling LLM.
        Returns a parsed-like dict or None if not applicable.
        """
        if not question:
            return None
        # Handle city-only short queries like "בחיפה?" → assume intent is customer count by city
        city_only = self._extract_city_from_question(question)
        if city_only:
            safe_city = city_only.replace("'", "''").strip()
            sql = (
                "SELECT COUNT(*) AS customer_count FROM ClientsBot2025 "
                f"WHERE TRIM(city) = '{safe_city}' OR TRIM(city) LIKE '{safe_city}%'"
            )
            return {
                'success': True,
                'sql': sql,
                'tables': ['ClientsBot2025'],
                'description': f"ספירת לקוחות בעיר {city_only}",
                'raw_response': None,
                'error': None,
            }
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
        logger.info(f"Parsing AI response: {content}")
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
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}. Raw response: {content[:200]}...")
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
                    logger.warning(f"Extracted JSON block failed: {inner}. JSON block: {json_block[:100]}...")
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
            logger.error(f"Unable to parse response. Content length: {len(content) if content else 0}. First 100 chars: {content[:100] if content else 'None'}")
            return {
                "success": False,
                "sql": "",
                "tables": [],
                "description": "",
                "raw_response": content,
                "error": f"Unable to parse or extract SQL from model response. Content: {content[:200] if content else 'Empty'}",
            }

    def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()
        try:
            logger.debug(f"Executing SQL: {sql} | params={params or {}}")
            result = self.db.execute(text(sql), params or {})
            if sql.strip().lower().startswith("select"):
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                elapsed = time.perf_counter() - start_time
                return {"success": True, "results": rows, "row_count": len(rows), "duration_sec": elapsed}
            else:
                self.db.commit()
                elapsed = time.perf_counter() - start_time
                return {"success": True, "row_count": result.rowcount, "message": f"Query executed in {elapsed:.2f} sec", "duration_sec": elapsed}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e), "duration_sec": time.perf_counter() - start_time}

    def generate_response(self, question: str, query_results: Dict[str, Any], context_block: Optional[str] = None) -> str:
        """
        Generate natural language response in Hebrew.
        
        Args:
            question: User's question in Hebrew
            query_results: Query execution results
            context_block: Optional compact context for follow-up questions
            
        Returns:
            Natural language answer in Hebrew
        """
        start_time = time.perf_counter()
        try:
            sample = query_results.get("results", [])[:1]
            columns = list(sample[0].keys()) if sample else []
            
            base_prompt = (
                "Write exactly one short, clear, self-contained sentence in Hebrew that summarizes the main result. "
                "Respond in Hebrew only. Do not include code, lists, quotes, or multiple sentences. "
                "Explicitly mention the main business entity (e.g., customers, total sales, order count, product, week) "
                "and include the concrete values from the data (use numerals; apply thousands separators if appropriate). "
                "Do not write generic phrases like 'נמצאו X תוצאות' or 'הנתונים מצביעים על'; be specific and data-grounded.\n"
            )
            
            # Inject context block if this is a follow-up
            if context_block:
                base_prompt += f"\n{context_block}\n\n"
            
            base_prompt += (
                f"Question (Hebrew): {question}\n"
                f"Columns: {json.dumps(columns, ensure_ascii=False)}\n"
                f"Sample data (first row only): {json.dumps(sample, ensure_ascii=False, default=str)}\n"
                "Examples of phrasing style (do not copy verbatim):\n"
                "- For a total customer count: מספר הלקוחות הכולל הוא 1,234.\n"
                "- For a specific city: בעיר חיפה יש 1,137 לקוחות.\n"
                "- For weekly sales: בשבוע 12 נמכרו 980 יחידות.\n"
                "- For total orders: בוצעו 245 הזמנות חדשות.\n"
                "- For product performance: המוצר הנמכר ביותר הוא חולצת כותנה עם 512 יחידות.\n"
                "If there are zero rows, return a single Hebrew sentence stating that no results were found for the question."
            )
            
            ans_tokens = min(160, getattr(config, "MAX_TOKENS", 1000))
            try:
                response = self.client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You produce exactly one concise sentence in Hebrew that is fully self-contained and understandable without seeing the question. Return only the sentence, no lists, no code."},
                        {"role": "user", "content": base_prompt},
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
                    "Write one short, clear sentence in Hebrew that is self-contained and includes the relevant values from the data. "
                    "Do not write 'נמצאו X תוצאות', do not write lists or code. Return exactly one specific sentence.\n"
                    f"השאלה: {question}\n"
                    f"עמודות: {json.dumps(columns, ensure_ascii=False)}\n"
                    f"דוגמה נתונים: {json.dumps(sample, ensure_ascii=False, default=str)}\n"
                )
                response2 = self.client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You produce exactly one concise, self-contained Hebrew sentence. No tables, no code."},
                        {"role": "user", "content": prompt2},
                    ],
                    max_completion_tokens=ans_tokens,
                )
                ai_response2 = (response2.choices[0].message.content or "").strip()
                if not _too_generic(ai_response2):
                    return ai_response2

            # Last-resort deterministic fallback if model still failed
            explicit = self._format_explicit_answer(question, query_results)
            if explicit:
                return explicit
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

    def _extract_city_from_question(self, question: str) -> Optional[str]:
        if not question:
            return None
        import re
        q = (question or "").strip()
        # Pattern A: space-then-"ב" until end
        m = re.search(r"\sב([^?.!,]+)$", q)
        city = None
        if m:
            city = m.group(1)
        else:
            # Pattern B: standalone token starting with 'ב' even without a leading space, e.g., "בחיפה?"
            m2 = re.search(r"\bב([\u0590-\u05FFA-Za-z\-\s]+)[?!. ,]*$", q)
            if m2:
                city = m2.group(1)
        if not city:
            return None
        city = city.strip()
        city = re.sub(r"^(עיר|בעיר)\s+", "", city).strip()
        city = city.replace('יש', '').strip()
        city = city.strip("'\"")
        return city or None

    def _format_explicit_answer(self, question: str, query_results: Dict[str, Any]) -> Optional[str]:
        """
        Generate a natural-language answer in English using OpenAI:
        - If no results: return "No results found."
        - Otherwise: send the question and summarized query results (JSON) to OpenAI
        to generate a clear, short, human-readable answer.
        Notes:
        - Requires environment variable OPENAI_API_KEY
        - Uses self.nlg_model or OPENAI_NLG_MODEL (default: gpt-4o-mini)
        """
        import json

        rows = query_results.get("results") or []
        rc = query_results.get("row_count", len(rows) if isinstance(rows, list) else 0)

        if rc == 0:
            return "No results found."

        # Safely convert each row to a dictionary (works for SQLAlchemy Row objects as well)
        def row_to_dict(r):
            if isinstance(r, dict):
                return r
            try:
                return dict(r)
            except Exception:
                try:
                    return {k: r[k] for k in r.keys()}
                except Exception:
                    return {"value": str(r)}

        # Limit number of preview rows to keep the prompt short
        max_rows = 5
        preview_rows = [row_to_dict(r) for r in rows[:max_rows]]

        compact_context = {
            "row_count": rc,
            "preview": preview_rows,
        }

        # Build the OpenAI prompt
        user_prompt = (
            "You are a professional BI assistant. Based only on the SQL query results provided below "
            "in JSON format, generate a short and accurate Hebrew sentence that clearly answers the user’s question. "
            "Avoid technical terms, do not add data that doesn’t exist in the results, and be concise. "
            "If results are ambiguous or incomplete, phrase the response carefully (e.g., 'at least X'). "
            "After the main answer, add one short and natural follow-up question in Hebrew that encourages the user "
            "to continue exploring the data — for example, suggesting a forecast, breakdown, or trend analysis. "
            "The follow-up must be relevant to the topic of the question.\n\n"
            f"Question: \"{question}\"\n"
            f"Query Results (JSON): {json.dumps(compact_context, ensure_ascii=False)}"
            "Return only the Hebrew text (answer + follow-up question)."
        )

        try:
            # Send request to OpenAI
            import os
            from openai import OpenAI

            client = getattr(self, "openai_client", None) or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            model = getattr(self, "nlg_model", os.getenv("OPENAI_NLG_MODEL", "gpt-4o-mini"))

            completion = client.chat.completions.create(
                model=model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": "You are a clear, concise, and professional BI report summarizer."},
                    {"role": "user", "content": user_prompt},
                ],
            )

            text = completion.choices[0].message.content.strip()
            return text or None

        except Exception:
            # Graceful fallback: basic text representation of results
            try:
                if len(preview_rows) == 1 and len(preview_rows[0]) == 1:
                    val = next(iter(preview_rows[0].values()))
                    return f"The result is {val}."
                return f"Example results: {json.dumps(preview_rows, ensure_ascii=False)}"
            except Exception:
                return "Unable to generate a natural-language answer from the results."

"""
Chatbot Service - BI Natural Language Processing Layer

Handles:
- Question processing and validation
- Smart context-aware follow-up handling (server-side only)
- SQL generation and execution
- Timed performance metrics
- Error resilience and clean logging
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import logging
import time

from app.services.ai_service import AIService
from app.models.user import User
from app.schemas.chat import QueryRequest, QueryResponse
from app.simple_config import config
from app.simple_memory import session_memory

logger = logging.getLogger(__name__)


class ChatbotService:
    """Main chatbot logic with performance tracking."""

    def __init__(self, db: Session, client_id: str = "KT"):
        self.db = db
        self.client_id = client_id
        self.ai_service = AIService(db, system_prompt=config.SYSTEM_PROMPT, client_id=client_id)
        

    async def process_question(self, request: QueryRequest, user: Optional[User] = None) -> QueryResponse:
        """
        Process user question with smart follow-up context injection.

        Server-side only follow-up handling:
        1. Detects if question is a follow-up using heuristics
        2. Injects minimal context if follow-up detected
        3. Updates context after successful response
        """
        question = request.question.strip()
        user_id = str(getattr(user, 'id', None) or 0)
        
        t0 = time.perf_counter()
        timings = {}

        # SIMPLE SYSTEM: Get session context as text for prompt injection
        context_text = session_memory.get_context_text(user_id)
        logger.debug(f"Retrieved context text for user {user_id}: {bool(context_text)}")

        # If PACK is configured, use prompt packs path to produce answer+SQL without changing frontend
        if config.PACK:
            try:
                t_pack = time.perf_counter()
                pack_out = self.ai_service.generate_pack_output(question, variables={"context_text": context_text})
                timings['prompt_pack'] = (time.perf_counter() - t_pack) * 1000
                sql_query = (pack_out or {}).get('sql_export')
                ai_answer = (pack_out or {}).get('short_answer', '')
                if sql_query:
                    # Execute SQL from pack
                    t2 = time.perf_counter()
                    query_results = await self._execute_query(sql_query)
                    timings['db_exec'] = (time.perf_counter() - t2) * 1000
                    if not query_results.get('success'):
                        return self._error_response(question, query_results.get('error', 'Query execution failed'), "DB", sql_query)
                    data = query_results['results']
                    # If pack did not provide an answer, generate one now
                    if not ai_answer or not ai_answer.strip():
                        t3 = time.perf_counter()
                        ai_answer = await self._generate_response(question, query_results, context_text=context_text)
                        timings['answer_gen'] = (time.perf_counter() - t3) * 1000
                    # Save context and return in legacy QueryResponse shape
                    session_memory.add_exchange(user_id, question, ai_answer, sql_query)
                    total_ms = (time.perf_counter() - t0) * 1000
                    timings['total'] = total_ms
                    return QueryResponse(
                        question=question,
                        answer=ai_answer,
                        sql=sql_query,
                        data=data,
                        error=None,
                        total_time_ms=total_ms,
                        timings_ms=timings
                    )
                else:
                    logger.warning("PACK set but no sql_export returned; falling back to legacy flow")
            except Exception as e:
                logger.warning(f"PACK path failed ({e}); falling back to legacy flow")

        try:
            # Generate SQL with simple context text
            t1 = time.perf_counter()
            sql_result = await self._generate_sql(question, context_text=context_text)
            timings['sql_gen'] = (time.perf_counter() - t1) * 1000

            if not sql_result.get('success'):
                return self._error_response(question, sql_result.get('error', 'SQL generation failed'), "SQL")

            sql_query = sql_result['sql']
            logger.info(f"Generated SQL: {sql_query}")

            # Execute SQL
            t2 = time.perf_counter()
            query_results = await self._execute_query(sql_query)
            timings['db_exec'] = (time.perf_counter() - t2) * 1000

            if not query_results.get('success'):
                return self._error_response(question, query_results.get('error', 'Query execution failed'), "DB", sql_query)

            data = query_results['results']
            row_count = query_results.get('row_count', 0)

            # Generate answer
            if row_count == 0:
                ai_answer = "לא נמצאו תוצאות לשאלה שלך."
            else:
                # Always craft a natural-language sentence via AI
                t3 = time.perf_counter()
                ai_answer = await self._generate_response(question, query_results, context_text=context_text)
                timings['answer_gen'] = (time.perf_counter() - t3) * 1000

            # Update session memory for natural OpenAI context
            session_memory.add_exchange(user_id, question, ai_answer, sql_query)
            logger.debug(f"Updated session memory for user {user_id}")

            total_ms = (time.perf_counter() - t0) * 1000
            timings['total'] = total_ms
            # Build visualization hint for frontend (best-effort)
            try:
                logger.info(f"Building visualization hint from data: {data}")
                viz = self._build_visualization_hint(data)
                logger.info(f"Visualization hint result: {viz}")
            except Exception:
                logger.exception("Visualization hint generation failed")
                viz = None

            return QueryResponse(
                question=question,
                answer=ai_answer,
                sql=sql_query,
                data=data,
                error=None,
                total_time_ms=total_ms,
                timings_ms=timings,
                visualization=viz,
            )

        except Exception as e:
            logger.exception("Unexpected error during question processing")
            return self._error_response(question, str(e), "Unexpected")

    async def _generate_sql(self, question: str, context_text: str = "") -> Dict[str, Any]:
        """Generate SQL strictly via OpenAI API (no server-side AST fallback)."""

        try:
            logger.info(f"Generating SQL via OpenAI only: {question}")
            result = self.ai_service.generate_sql(question, context_text=context_text)
            if result.get('success'):
                result['method'] = 'openai'
            else:
                logger.error(f"OpenAI failed to generate SQL: {result.get('error')}")
            return result

        except Exception as openai_error:
            logger.exception("OpenAI SQL generation raised an exception")
            return {
                'success': False,
                'error': f"OpenAI SQL generation failed: {openai_error}",
                'method': 'openai_error'
            }

    async def _execute_query(self, sql: str) -> Dict[str, Any]:
        try:
            return self.ai_service.execute_query(sql)
        except Exception as e:
            logger.error(f"DB execution error: {e}")
            return {'success': False, 'error': str(e)}

    async def _generate_response(self, question: str, results: Dict[str, Any], context_text: str = "") -> str:
        """Generate response with optional context for follow-up questions"""
        try:
            return self.ai_service.generate_response(question, results, context_text=context_text)
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return f"נמצאו {results.get('row_count', 0)} תוצאות אך אירעה שגיאה ביצירת תשובה."

    def _guess_number(self, value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return value
        try:
            s = str(value).replace(",", "").replace(" ", "")
            return float(s)
        except:
            return None
    def _is_date_string(self, s: Any) -> bool:
        if not s:
            return False
        try:
            st = str(s)
            # Simple ISO date detection YYYY-MM-DD or YYYY/MM/DD
            import re
            if re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}", st):
                return True
            # Year-only
            if re.match(r"^\d{4}$", st):
                return True
        except Exception:
            return False
        return False

    def _build_visualization_hint(self, rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a best-effort visualization hint from query result rows.

        Returns a dict like:
        {chart_type: 'bar'|'line'|'pie'|'metric', title, label_field, value_field, labels, values}
        or None if not enough structure.
        """
        if not rows or len(rows) == 0:
            return None

        # Use first row to inspect columns
        first = rows[0]
        cols = list(first.keys())
        # If single numeric value -> metric
        if len(cols) == 1:
            only = cols[0]
            num = self._guess_number(first.get(only))
            if num is not None:
                return {
                    "chart_type": "metric",
                    "title": f"{only}",
                    "label_field": only,
                    "value_field": only,
                    "labels": [only],
                    "values": [num],
                }
            return None

        # If two columns: one categorical and one numeric -> bar/pie
        if len(cols) == 2:
            a, b = cols[0], cols[1]
            # Check types across rows
            a_num = [self._guess_number(r.get(a)) for r in rows]
            b_num = [self._guess_number(r.get(b)) for r in rows]

            a_all_num = all(v is not None for v in a_num)
            b_all_num = all(v is not None for v in b_num)

            # date detection for timeseries
            if any(self._is_date_string(r.get(a)) for r in rows) and b_all_num:
                labels = [str(r.get(a)) for r in rows]
                values = [float(self._guess_number(r.get(b)) or 0) for r in rows]
                return {
                    "chart_type": "line",
                    "title": f"{b} over {a}",
                    "label_field": a,
                    "value_field": b,
                    "labels": labels,
                    "values": values,
                }

            if a_all_num and not b_all_num:
                # swap so label is b, value is a
                labels = [str(r.get(b)) for r in rows]
                values = [float(v or 0) for v in a_num]
                return {
                    "chart_type": "bar",
                    "title": f"{a} by {b}",
                    "label_field": b,
                    "value_field": a,
                    "labels": labels,
                    "values": values,
                }
            if b_all_num and not a_all_num:
                labels = [str(r.get(a)) for r in rows]
                values = [float(v or 0) for v in b_num]
                return {
                    "chart_type": "bar",
                    "title": f"{b} by {a}",
                    "label_field": a,
                    "value_field": b,
                    "labels": labels,
                    "values": values,
                }

            # If both numeric: scatter-like -> return as two-series
            if a_all_num and b_all_num:
                labels = [str(i) for i in range(len(rows))]
                values = [{"x": float(a_num[i]), "y": float(b_num[i])} for i in range(len(rows))]
                return {
                    "chart_type": "scatter",
                    "title": f"{a} vs {b}",
                    "label_field": a,
                    "value_field": b,
                    "labels": labels,
                    "values": values,
                }

        # For >2 columns, try to find one categorical and one numeric column
        numeric_cols = []
        categorical_cols = []
        for c in cols:
            nums = [self._guess_number(r.get(c)) for r in rows]
            if all(v is not None for v in nums):
                numeric_cols.append(c)
            else:
                categorical_cols.append(c)

        if numeric_cols and categorical_cols:
            num_col = numeric_cols[0]
            cat_col = categorical_cols[0]
            # aggregate by categorical (sum)
            agg = {}
            for r in rows:
                key = str(r.get(cat_col))
                val = self._guess_number(r.get(num_col)) or 0
                agg[key] = agg.get(key, 0) + val
            labels = list(agg.keys())[:20]
            values = [agg[k] for k in labels]
            return {
                "chart_type": "bar",
                "title": f"{num_col} by {cat_col}",
                "label_field": cat_col,
                "value_field": num_col,
                "labels": labels,
                "values": values,
            }

        return None

    def _error_response(self, question: str, msg: str, context: str, sql: Optional[str] = None) -> QueryResponse:
        logger.warning(f"Error [{context}]: {msg}")
        return QueryResponse(
            question=question,
            answer=f"שגיאה בעיבוד השאלה ({context}): {msg}",
            sql=sql,
            error=msg
        )

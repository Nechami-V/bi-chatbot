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
from app.query_ast import HebrewQueryParser, create_sql_generator

logger = logging.getLogger(__name__)


class ChatbotService:
    """Main chatbot logic with performance tracking."""

    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService(db, system_prompt=config.SYSTEM_PROMPT)
        
        # Add Hebrew Query AST system for better SQL generation
        self.query_parser = HebrewQueryParser("sample-client")
        self.sql_generator = create_sql_generator("sample-client")

    async def process_question(self, request: QueryRequest, user: Optional[User] = None) -> QueryResponse:
        """
        Process user question with smart follow-up context injection.
        
        Server-side only follow-up handling:
        1. Detects if question is a follow-up using heuristics
        2. Injects minimal context if follow-up detected
        3. Updates context after successful response
        """
        question = request.question.strip()
        user_id = getattr(user, 'id', None) or 0
        
        t0 = time.perf_counter()
        timings = {}

        # SIMPLE SYSTEM: Get session context as text for prompt injection
        context_text = session_memory.get_context_text(user_id)
        logger.debug(f"Retrieved context text for user {user_id}: {bool(context_text)}")

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
            session_memory.add_exchange(user_id, question, ai_answer)
            logger.debug(f"Updated session memory for user {user_id}")

            total_ms = (time.perf_counter() - t0) * 1000
            timings['total'] = total_ms
            # Build visualization hint for frontend (best-effort)
            try:
                viz = self._build_visualization_hint(data)
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
        """Generate SQL using OpenAI as primary method (user preference)"""
        
        # Use OpenAI as primary method per user request
        try:
            logger.info(f"Using OpenAI for SQL generation (user preference): {question}")
            result = self.ai_service.generate_sql(question, context_text=context_text)
            if result.get('success'):
                result['method'] = 'openai'
                return result
            else:
                logger.warning("OpenAI SQL generation failed, trying AST as fallback")
                
        except Exception as openai_error:
            logger.warning(f"OpenAI failed: {openai_error}, trying AST as fallback")
        
        # Only fallback to AST if OpenAI completely fails
        try:
            logger.info("Using AST as fallback after OpenAI failure")
            parsed_query = self.query_parser.parse(question)
            
            if parsed_query.confidence >= 0.4:  # Lower threshold for fallback
                sql_query = self.sql_generator.generate_sql(parsed_query)
                logger.info(f"AST fallback generated SQL (confidence: {parsed_query.confidence:.2f}): {sql_query}")
                
                return {
                    'success': True,
                    'sql': sql_query,
                    'method': 'ast_fallback',
                    'confidence': parsed_query.confidence,
                    'intent': parsed_query.intent
                }
            else:
                return {
                    'success': False,
                    'error': f"OpenAI failed and AST confidence too low ({parsed_query.confidence:.2f})",
                    'method': 'both_failed'
                }
                
        except Exception as ast_error:
            logger.error(f"Both OpenAI and AST failed: AST={ast_error}")
            return {'success': False, 'error': f"Both methods failed: {ast_error}"}

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

    def _guess_number(self, val: Any) -> Optional[float]:
        """Try to coerce a value into a float for charting purposes."""
        if val is None:
            return None
        try:
            if isinstance(val, (int, float)):
                return float(val)
            # Some DB drivers return Decimal
            from decimal import Decimal
            if isinstance(val, Decimal):
                return float(val)
            # Strings that look like numbers
            s = str(val).replace(',', '')
            return float(s)
        except Exception:
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

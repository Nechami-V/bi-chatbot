"""
Chatbot Service - BI Natural Language Processing Layer

Handles:
- Question processing and validation
- Context-aware follow-up handling
- SQL generation and execution
- Timed performance metrics
- Error resilience and clean logging
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import logging
import time

from app.services.ai_service import AIService
from app.models.user import User
from app.schemas.chat import QueryRequest, QueryResponse
from app.simple_config import config

logger = logging.getLogger(__name__)

USER_CONTEXT: dict = {}  # for conversation continuity


def _resolve_followup(prev_q: str, new_q: str) -> str:
    """Reconstruct a full question from a short follow-up."""
    if not prev_q:
        return new_q.strip()
    q = new_q.strip()
    if q.startswith('ו'):
        q = q[1:].strip()
    if 'לקוח' in prev_q and 'לקוח' not in q:
        if q.startswith('ב'):
            return f"כמה לקוחות יש {q}"
        return f"כמה לקוחות יש {q}"
    return f"{prev_q} {q}"


class ChatbotService:
    """Main chatbot logic with performance tracking."""

    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService(db, system_prompt=config.SYSTEM_PROMPT)

    async def process_question(self, request: QueryRequest, user: Optional[User] = None) -> QueryResponse:
        question = request.question.strip()
        user_key = str(getattr(user, 'id', None) or getattr(user, 'email', None) or 'anonymous')

        # handle context
        prev_q = USER_CONTEXT.get(user_key, {}).get('last_question')
        if prev_q and (question.startswith('ו') or ('לקוח' in prev_q and 'לקוח' not in question)):
            effective_q = _resolve_followup(prev_q, question)
        else:
            effective_q = question

        t0 = time.perf_counter()
        timings = {}

        try:
            # Generate SQL
            t1 = time.perf_counter()
            sql_result = await self._generate_sql(effective_q)
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
                # Always craft a natural-language sentence via AI, even for single-number results
                t3 = time.perf_counter()
                ai_answer = await self._generate_response(question, query_results)
                timings['answer_gen'] = (time.perf_counter() - t3) * 1000

            USER_CONTEXT[user_key] = {'last_question': effective_q}

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

        except Exception as e:
            logger.exception("Unexpected error during question processing")
            return self._error_response(question, str(e), "Unexpected")

    async def _generate_sql(self, question: str) -> Dict[str, Any]:
        try:
            return self.ai_service.generate_sql(question)
        except Exception as e:
            logger.error(f"SQL generation error: {e}")
            return {'success': False, 'error': str(e)}

    async def _execute_query(self, sql: str) -> Dict[str, Any]:
        try:
            return self.ai_service.execute_query(sql)
        except Exception as e:
            logger.error(f"DB execution error: {e}")
            return {'success': False, 'error': str(e)}

    async def _generate_response(self, question: str, results: Dict[str, Any]) -> str:
        try:
            return self.ai_service.generate_response(question, results)
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return f"נמצאו {results.get('row_count', 0)} תוצאות אך אירעה שגיאה ביצירת תשובה."

    def _error_response(self, question: str, msg: str, context: str, sql: Optional[str] = None) -> QueryResponse:
        logger.warning(f"Error [{context}]: {msg}")
        return QueryResponse(
            question=question,
            answer=f"שגיאה בעיבוד השאלה ({context}): {msg}",
            sql=sql,
            error=msg
        )

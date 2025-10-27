"""
Chatbot Service - BI Natural Language Processing Layer

Handles:
- Question processing and validation
- Smart context-aware follow-up handling (server-side only)
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
from app.context_memory import context_store
from app.conversation_history import conversation_history
from app.followup import is_follow_up, summarize_answer, build_context_block
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

        # OLD SYSTEM: Retrieve previous context for follow-up detection
        prev_context = context_store.get(user_id)
        prev_question = prev_context.prev_question if prev_context else None
        
        # OLD SYSTEM: Detect if this is a follow-up question
        is_followup = is_follow_up(question, prev_question)
        
        # NEW SYSTEM: Get conversation history for OpenAI context (testing phase)
        conversation_context = conversation_history.build_context_for_openai(user_id)
        logger.debug(f"NEW: Built conversation context with {len(conversation_context)} messages")
        
        if is_followup and prev_context:
            logger.info(f"Follow-up detected for user {user_id}")
            # Build compact context block for prompt
            context_block = build_context_block(
                prev_question=prev_context.prev_question,
                prev_answer_summary=prev_context.prev_answer_summary,
                prev_sql_snippet=prev_context.prev_sql_snippet
            )
        else:
            context_block = None
            logger.debug(f"Standalone question (is_followup={is_followup}, has_context={prev_context is not None})")

        try:
            # Generate SQL
            t1 = time.perf_counter()
            sql_result = await self._generate_sql(question, context_block)
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
                ai_answer = await self._generate_response(question, query_results, context_block)
                timings['answer_gen'] = (time.perf_counter() - t3) * 1000

            # Update context for next question
            answer_summary = summarize_answer(ai_answer, max_length=100)
            context_store.set(
                user_id=user_id,
                question=question,
                answer_summary=answer_summary,
                sql_snippet=sql_query
            )
            logger.debug(f"Updated context for user {user_id}")

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

    async def _generate_sql(self, question: str, context_block: Optional[str] = None) -> Dict[str, Any]:
        """Generate SQL using OpenAI as primary method (user preference)"""
        
        # Use OpenAI as primary method per user request
        try:
            logger.info(f"Using OpenAI for SQL generation (user preference): {question}")
            result = self.ai_service.generate_sql(question, context_block)
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

    async def _generate_response(self, question: str, results: Dict[str, Any], context_block: Optional[str] = None) -> str:
        """Generate response with optional context for follow-up questions"""
        try:
            return self.ai_service.generate_response(question, results, context_block)
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

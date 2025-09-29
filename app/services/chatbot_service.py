"""
Chatbot Service - Business Logic for Question Processing

This service handles the main business logic for processing natural language
questions and generating responses. It orchestrates the AI service and provides
a clean interface for the API endpoints.

Key Responsibilities:
- Question validation and preprocessing
- AI service orchestration (SQL generation, execution, response)
- Error handling and logging
- Response formatting

Author: BI Chatbot Team
Version: 2.0.0
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
import logging

from app.services.ai_service import AIService
from app.schemas.chat import QueryRequest, QueryResponse

# Configure logging
logger = logging.getLogger(__name__)


class ChatbotService:
    """
    Main chatbot service for processing natural language questions
    
    This service provides a clean interface for processing user questions
    and generating appropriate responses using AI capabilities.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the chatbot service with database session
        
        Args:
            db (Session): SQLAlchemy database session
        """
        self.db = db
        self.ai_service = AIService(db)
    
    async def process_question(self, request: QueryRequest) -> QueryResponse:
        """
        Process a natural language question and generate a complete response
        
        Args:
            request (QueryRequest): The user's question request
            
        Returns:
            QueryResponse: Complete response with answer, SQL, and metadata
        """
        question = request.question
        
        try:
            logger.info(f"Processing question: {question}")
            
            # Step 1: Generate SQL from natural language question
            logger.info("Generating SQL from question using AI...")
            sql_result = await self._generate_sql(question)
            
            if not sql_result.get('success'):
                return self._create_error_response(
                    question=question,
                    error_msg=sql_result.get('error', 'Unknown SQL generation error'),
                    context="SQL generation failed"
                )
            
            sql_query = sql_result.get('sql', '')
            logger.info(f"Generated SQL: {sql_query}")
            
            # Step 2: Execute the generated SQL query
            logger.info("Executing SQL query...")
            query_results = await self._execute_query(sql_query)
            
            if not query_results.get('success'):
                return self._create_error_response(
                    question=question,
                    error_msg=query_results.get('error', 'Unknown query execution error'),
                    context="Query execution failed",
                    sql=sql_query
                )
            
            # Step 3: Generate natural language response
            logger.info("Generating natural language response...")
            ai_answer = await self._generate_response(question, query_results)
            
            logger.info("Question processed successfully")
            return QueryResponse(
                question=question,
                answer=ai_answer,
                sql=sql_query,
                error=None
            )
            
        except Exception as exc:
            logger.error(f"Unexpected error processing question: {str(exc)}", exc_info=True)
            return self._create_error_response(
                question=question,
                error_msg=f"אירעה שגיאה בלתי צפויה בעיבוד השאלה: {str(exc)}",
                context="Unexpected system error"
            )
    
    async def _generate_sql(self, question: str) -> Dict[str, Any]:
        """
        Generate SQL query from natural language question
        
        Args:
            question (str): The user's question in Hebrew
            
        Returns:
            Dict[str, Any]: Result with success status and SQL or error
        """
        try:
            return self.ai_service.generate_sql(question)
        except Exception as exc:
            logger.error(f"Error in SQL generation: {str(exc)}")
            return {
                'success': False,
                'error': f"שגיאה ביצירת שאילתת SQL: {str(exc)}"
            }
    
    async def _execute_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute SQL query against the database
        
        Args:
            sql_query (str): The SQL query to execute
            
        Returns:
            Dict[str, Any]: Result with success status and data or error
        """
        try:
            return self.ai_service.execute_query(sql_query)
        except Exception as exc:
            logger.error(f"Error in query execution: {str(exc)}")
            return {
                'success': False,
                'error': f"שגיאה בביצוע השאילתה: {str(exc)}"
            }
    
    async def _generate_response(self, question: str, query_results: Dict[str, Any]) -> str:
        """
        Generate natural language response from query results
        
        Args:
            question (str): The original user question
            query_results (Dict[str, Any]): Results from query execution
            
        Returns:
            str: Natural language response in Hebrew
        """
        try:
            return self.ai_service.generate_response(question, query_results)
        except Exception as exc:
            logger.error(f"Error in response generation: {str(exc)}")
            # Fallback to basic response if AI fails
            row_count = query_results.get('row_count', 0)
            return f"מצאתי {row_count} תוצאות עבור השאלה שלך, אך אירעה שגיאה ביצירת התשובה המפורטת."
    
    def _create_error_response(
        self, 
        question: str, 
        error_msg: str, 
        context: str, 
        sql: str = None
    ) -> QueryResponse:
        """
        Create a standardized error response
        
        Args:
            question (str): The original user question
            error_msg (str): The error message to display
            context (str): Context where the error occurred
            sql (str, optional): The SQL query if available
            
        Returns:
            QueryResponse: Formatted error response
        """
        logger.warning(f"Creating error response - Context: {context}, Error: {error_msg}")
        
        return QueryResponse(
            question=question,
            answer=error_msg,
            sql=sql,
            error=error_msg
        )
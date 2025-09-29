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

Author: BI Chatbot Team
Version: 2.0.0
"""

import logging
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
    
    Attributes:
        db (Session): SQLAlchemy database session
        client (OpenAI): OpenAI API client for language processing
        schema_info (Dict): Analyzed database schema information
    """
    
    def __init__(self, db: Session):
        """
        Initialize the AI service with database connection
        
        Args:
            db (Session): SQLAlchemy database session for query execution
            
        Raises:
            ValueError: If OpenAI API key is not configured
        """
        self.db = db
        self.schema_info = self._analyze_database_schema()
        
        # Validate and configure OpenAI client
        if not config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured. Please set the OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        logger.info("AI Service initialized successfully")
    
    def _analyze_database_schema(self) -> Dict[str, Any]:
        """
        Analyze database schema to understand structure and relationships
        
        This method examines the database to understand table structures,
        column types, relationships, and constraints. This information
        helps the AI generate more accurate SQL queries.
        
        Returns:
            Dict[str, Any]: Structured schema information containing:
                - tables: Dict of table names with column info
                - relationships: List of foreign key relationships
        """
        logger.info("Analyzing database schema...")
        
        inspector = inspect(self.db.get_bind())
        schema = {
            'tables': {},
            'relationships': []
        }
        
        # Focus on business data tables (exclude system/temp tables)
        relevant_tables = config.BUSINESS_TABLES
        
        for table_name in relevant_tables:
            # Verify table exists in database
            if table_name not in inspector.get_table_names():
                logger.warning(f"Table {table_name} not found in database")
                continue
                
            # Extract column information for AI understanding
            columns = []
            for column in inspector.get_columns(table_name):
                columns.append({
                    'name': column['name'],
                    'type': str(column['type']),
                    'nullable': column['nullable'],
                    'default': column.get('default'),
                    'primary_key': column.get('primary_key', False)
                })
            
            # Identify primary key columns
            primary_keys = [col['name'] for col in columns if col.get('primary_key', False)]
            
            # Extract foreign key relationships for JOIN operations
            foreign_keys = []
            for fk in inspector.get_foreign_keys(table_name):
                foreign_keys.append({
                    'constrained_columns': fk['constrained_columns'],
                    'referred_table': fk['referred_table'],
                    'referred_columns': fk['referred_columns']
                })
            
            # Store table metadata
            schema['tables'][table_name] = {
                'columns': columns,
                'primary_key': primary_keys,
                'foreign_keys': foreign_keys
            }
            
            # Build relationship graph for AI query generation
            for fk in foreign_keys:
                schema['relationships'].append({
                    'from_table': table_name,
                    'from_columns': fk['constrained_columns'],
                    'to_table': fk['referred_table'],
                    'to_columns': fk['referred_columns']
                })
        
        return schema
    
    def generate_sql(self, question: str) -> Dict[str, Any]:
        """Generate SQL from a natural language question using OpenAI."""
        try:
            prompt = self._build_sql_prompt(question)
            response = self._call_openai_for_sql(prompt)
            return self._parse_sql_response(response)
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'sql': '',
                'tables': [],
                'description': ''
            }
    
    def _build_sql_prompt(self, question: str) -> str:
        """Build the prompt for OpenAI SQL generation."""
        schema_info = json.dumps(self.schema_info, indent=2, ensure_ascii=False)
        
        return f"""
Based on this database schema:
{schema_info}

Hebrew Question: "{question}"

Generate a precise SQL query following these rules:
1. Use Hebrew column names as they exist in the database
2. Hebrew text should appear in WHERE conditions for data matching
3. Use proper JOINs when querying multiple tables
4. Return meaningful English aliases for calculated results
5. Ensure SQLite compatibility

Key tables:
- ClientsBot2025: customers data (ID_לקוח, fname, lname, wname, city)
- OrdersBot2025: sales/orders data (ID_מכירה, ID_לקוח, ID_פריט, תאריך, סכום)
- ItemsBot2025: items data (ID_פריט, name, pgrp)
- SalesBot2025: sales metadata (ID_מכירה, week, name)

Examples:
- "כמה לקוחות יש?" → SELECT COUNT(*) AS customer_count FROM ClientsBot2025
- "כמה לקוחות בתל אביב?" → SELECT COUNT(*) AS customer_count FROM ClientsBot2025 WHERE city = 'תל אביב'

Respond with valid JSON only:
{{
  "sql": "your_sql_query_here",
  "tables": ["table1", "table2"],
  "description": "תיאור בעברית"
}}
        """.strip()
    
    def _call_openai_for_sql(self, prompt: str) -> str:
        """Call OpenAI API for SQL generation."""
        response = self.client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": config.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=config.MAX_TOKENS
        )
        return response.choices[0].message.content
    
    def _parse_sql_response(self, content: str) -> Dict[str, Any]:
        """Parse OpenAI response for SQL generation."""
        try:
            result = json.loads(content)
            return {
                'success': True,
                'sql': result.get('sql', ''),
                'tables': result.get('tables', []),
                'description': result.get('description', ''),
                'raw_response': content
            }
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response, extracting SQL as text")
            return {
                'success': True,
                'sql': content.strip(),
                'tables': [],
                'description': 'Generated SQL from text',
                'raw_response': content
            }
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute a SQL query and return the results."""
        try:
            logger.debug(f"Executing SQL: {sql}")
            result = self.db.execute(text(sql))
            
            # If it's a SELECT query, fetch the results
            if sql.strip().lower().startswith('select'):
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                logger.info(f"Query returned {len(rows)} rows")
                if rows:
                    logger.debug(f"Sample result: {rows[0]}")
                return {
                    'success': True,
                    'results': rows,
                    'row_count': len(rows)
                }
            else:
                # For non-SELECT queries, return the rowcount
                self.db.commit()
                return {
                    'success': True,
                    'row_count': result.rowcount,
                    'message': f"Query executed successfully. {result.rowcount} rows affected."
                }
                
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_response(self, question: str, query_results: Dict[str, Any]) -> str:
        """Generate a natural language response based on query results."""
        try:
            logger.debug(f"Query results for response: {query_results}")
            
            # Prepare the context for the AI
            context = {
                'question': question,
                'row_count': query_results.get('row_count', 0),
                'sample_data': query_results.get('results', [])[:3]  # First 3 rows as sample
            }
            
            logger.debug(f"Context prepared: {context}")
            
            # Create the prompt for the AI
            prompt = f"""
            המשתמש שאל: {question}
            
            הנה תוצאות השאילתה:
            - מספר שורות: {context['row_count']}
            - דוגמא לנתונים (3 שורות ראשונות): {json.dumps(context['sample_data'], ensure_ascii=False, default=str)}
            
            אנא ענה על השאלה בעברית בצורה ברורה ותמציתית.
            """.strip()
            
            logger.debug(f"Prompt for response generation: {prompt}")
            
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=config.MAX_TOKENS
            )
            
            ai_response = response.choices[0].message.content.strip()
            logger.debug(f"AI Response: {ai_response}")
            
            return ai_response
            
        except Exception as e:
            error_msg = f"אירעה שגיאה ביצירת התשובה: {str(e)}"
            logger.error(f"Error in generate_response: {error_msg}")
            return error_msg

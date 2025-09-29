from openai import OpenAI
from typing import Dict, List, Optional, Any
import json
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from ..simple_config import config

class AIService:
    """Service for handling AI-related operations including natural language understanding and SQL generation."""
    
    def __init__(self, db: Session):
        """Initialize the AI service with a database session."""
        self.db = db
        self.schema_info = self._analyze_database_schema()
        
        # Configure OpenAI client
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        if not config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured. Please set the OPENAI_API_KEY environment variable.")
    
    def _analyze_database_schema(self) -> Dict[str, Any]:
        """Analyze the database schema and return a structured representation."""
        inspector = inspect(self.db.get_bind())
        schema = {
            'tables': {},
            'relationships': []
        }
        
        # Only analyze the real data tables, not the mock tables
        relevant_tables = ['ClientsBot2025', 'OrdersBot2025', 'ItemsBot2025', 'SalesBot2025']
        
        for table_name in relevant_tables:
            # Check if table exists
            if table_name not in inspector.get_table_names():
                continue
                
            # Get columns for each table
            columns = []
            for column in inspector.get_columns(table_name):
                columns.append({
                    'name': column['name'],
                    'type': str(column['type']),
                    'nullable': column['nullable'],
                    'default': column.get('default'),
                    'primary_key': column.get('primary_key', False)
                })
            
            # Get primary keys
            primary_keys = [col['name'] for col in columns if col.get('primary_key', False)]
            
            # Get foreign keys
            foreign_keys = []
            for fk in inspector.get_foreign_keys(table_name):
                foreign_keys.append({
                    'constrained_columns': fk['constrained_columns'],
                    'referred_table': fk['referred_table'],
                    'referred_columns': fk['referred_columns']
                })
            
            schema['tables'][table_name] = {
                'columns': columns,
                'primary_key': primary_keys,
                'foreign_keys': foreign_keys
            }
            
            # Add relationship information
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
        # Prepare the schema information for the prompt
        schema_info = json.dumps(self.schema_info, indent=2, ensure_ascii=False)
        
        # Create the prompt for the AI
        prompt = f"""
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
        
        try:
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=config.MAX_TOKENS
            )
            
            # Extract the generated SQL from the response
            content = response.choices[0].message.content
            
            # Try to parse the JSON response
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
                # If JSON parsing fails, try to extract SQL from the text
                return {
                    'success': True,
                    'sql': content.strip(),
                    'tables': [],
                    'description': 'Generated SQL from text',
                    'raw_response': content
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'sql': '',
                'tables': [],
                'description': ''
            }
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute a SQL query and return the results."""
        try:
            print(f"   Executing SQL: {sql}")
            result = self.db.execute(text(sql))
            
            # If it's a SELECT query, fetch the results
            if sql.strip().lower().startswith('select'):
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                print(f"   Query returned {len(rows)} rows")
                if rows:
                    print(f"   Sample result: {rows[0]}")
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
            print(f"   Query results for response: {query_results}")
            
            # Prepare the context for the AI
            context = {
                'question': question,
                'row_count': query_results.get('row_count', 0),
                'sample_data': query_results.get('results', [])[:3]  # First 3 rows as sample
            }
            
            print(f"   Context prepared: {context}")
            
            # Create the prompt for the AI
            prompt = f"""
            המשתמש שאל: {question}
            
            הנה תוצאות השאילתה:
            - מספר שורות: {context['row_count']}
            - דוגמא לנתונים (3 שורות ראשונות): {json.dumps(context['sample_data'], ensure_ascii=False, default=str)}
            
            אנא ענה על השאלה בעברית בצורה ברורה ותמציתית.
            """.strip()
            
            print(f"   Prompt for response generation: {prompt}")
            
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
            print(f"   AI Response: {ai_response}")
            
            return ai_response
            
        except Exception as e:
            error_msg = f"אירעה שגיאה ביצירת התשובה: {str(e)}"
            print(f"   Error in generate_response: {error_msg}")
            return error_msg

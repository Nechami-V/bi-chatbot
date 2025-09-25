import openai
from typing import Dict, List, Optional, Any
import json
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from ..config import config

class AIService:
    """Service for handling AI-related operations including natural language understanding and SQL generation."""
    
    def __init__(self, db: Session):
        """Initialize the AI service with a database session."""
        self.db = db
        self.schema_info = self._analyze_database_schema()
        
        # Configure OpenAI
        openai.api_key = config.OPENAI_API_KEY
        if not openai.api_key:
            raise ValueError("OpenAI API key is not configured. Please set the OPENAI_API_KEY environment variable.")
    
    def _analyze_database_schema(self) -> Dict[str, Any]:
        """Analyze the database schema and return a structured representation."""
        inspector = inspect(self.db.get_bind())
        schema = {
            'tables': {},
            'relationships': []
        }
        
        # Get all table names
        table_names = inspector.get_table_names()
        
        for table_name in table_names:
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
        נתון סכמת מסד הנתונים הבאה:
        {schema_info}
        
        על סמך הסכמה הנ"ל, צור שאילתת SQL שמענה על השאלה: "{question}"
        
        החזר את השאילתה בפורמט JSON עם השדות הבאים:
        - sql: השאילתה ב-SQL
        - tables: רשימת הטבלאות המעורבות
        - description: הסבר קצר על השאילתה
        """.strip()
        
        try:
            # Call the OpenAI API
            response = openai.ChatCompletion.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS
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
            result = self.db.execute(sql)
            
            # If it's a SELECT query, fetch the results
            if sql.strip().lower().startswith('select'):
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
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
            # Prepare the context for the AI
            context = {
                'question': question,
                'row_count': query_results.get('row_count', 0),
                'sample_data': query_results.get('results', [])[:3]  # First 3 rows as sample
            }
            
            # Create the prompt for the AI
            prompt = f"""
            המשתמש שאל: {question}
            
            הנה תוצאות השאילתה:
            - מספר שורות: {context['row_count']}
            - דוגמא לנתונים (3 שורות ראשונות): {json.dumps(context['sample_data'], ensure_ascii=False, default=str)}
            
            אנא ענה על השאלה בעברית בצורה ברורה ותמציתית.
            """.strip()
            
            # Call the OpenAI API
            response = openai.ChatCompletion.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"אירעה שגיאה ביצירת התשובה: {str(e)}"

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import inspect
import json

class AIQuestionProcessor:
    """
    A class to process natural language questions using AI capabilities.
    Handles question analysis, database interaction, and response generation.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the AI Question Processor with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.schema_info = self._analyze_database_schema()
    
    def _analyze_database_schema(self) -> Dict[str, Any]:
        """
        Analyze the database schema to understand tables, columns, and relationships.
        
        Returns:
            Dictionary containing schema information
        """
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
        
        return schema
    
    def process_question(self, question: str) -> Dict[str, Any]:
        """
        Process a natural language question and generate a response.
        
        Args:
            question: The natural language question from the user
            
        Returns:
            Dictionary containing the response and metadata
        """
        try:
            # Step 1: Analyze the question
            analysis = self._analyze_question(question)
            
            # Step 2: Generate SQL query based on analysis
            query_info = self._generate_query(analysis)
            
            # Step 3: Execute the query
            results = self._execute_query(query_info['sql'])
            
            # Step 4: Generate natural language response
            response = self._generate_response(question, results, query_info)
            
            return {
                'success': True,
                'question': question,
                'response': response,
                'sql': query_info.get('sql'),
                'analysis': analysis,
                'data': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'question': question
            }
    
    def _analyze_question(self, question: str) -> Dict[str, Any]:
        """
        Analyze the question to understand user intent and extract entities.
        
        Args:
            question: The natural language question
            
        Returns:
            Dictionary containing analysis results
        """
        # TODO: Implement more sophisticated NLP analysis
        # This is a placeholder implementation
        return {
            'intent': 'query',  # Could be 'query', 'filter', 'aggregate', etc.
            'entities': [],     # Extracted entities (tables, columns, values)
            'filters': [],      # Filter conditions
            'aggregations': [], # Aggregation functions (count, sum, avg, etc.)
            'group_by': [],     # Grouping criteria
            'order_by': [],     # Sorting criteria
            'limit': None       # Result limit
        }
    
    def _generate_query(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate SQL query based on question analysis.
        
        Args:
            analysis: The analysis dictionary from _analyze_question
            
        Returns:
            Dictionary containing SQL query and metadata
        """
        # TODO: Implement query generation based on analysis
        # This is a placeholder implementation
        return {
            'sql': 'SELECT * FROM your_table LIMIT 10',
            'tables': [],
            'columns': []
        }
    
    def _execute_query(self, query: str) -> List[Dict]:
        """
        Execute a SQL query and return the results.
        
        Args:
            query: SQL query to execute
            
        Returns:
            List of dictionaries representing the query results
        """
        try:
            result = self.db.execute(query)
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception as e:
            raise Exception(f"שגיאה בביצוע השאילתה: {str(e)}")
    
    def _generate_response(self, question: str, data: List[Dict], query_info: Dict) -> str:
        """
        Generate a natural language response based on query results.
        
        Args:
            question: The original question
            data: The query results
            query_info: Information about the executed query
            
        Returns:
            Natural language response
        """
        # TODO: Implement more sophisticated response generation
        if not data:
            return "לא נמצאו תוצאות התואמות את השאילתך."
        
        # Simple response for now
        result_count = len(data)
        return f"נמצאו {result_count} תוצאות התואמות את שאלתך. " \
               f"התשובה מבוססת על ניתוח של {len(query_info.get('tables', []))} טבלאות."

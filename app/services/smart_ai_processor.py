from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import json
import logging
from .ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartAIProcessor:
    """
    Smart AI processor that uses OpenAI to understand natural language questions,
    generate SQL queries, and provide meaningful responses.
    """
    
    def __init__(self, db: Session):
        """Initialize with a database session."""
        self.db = db
        self.ai_service = AIService(db)
    
    def process_question(self, question: str) -> Dict[str, Any]:
        """
        Process a natural language question and return a response.
        
        Args:
            question: The natural language question
            
        Returns:
            Dictionary containing the response and metadata
        """
        try:
            logger.info(f"Processing question: {question}")
            
            # Step 1: Generate SQL using AI
            sql_result = self.ai_service.generate_sql(question)
            
            if not sql_result['success']:
                return {
                    'success': False,
                    'question': question,
                    'error': f"שגיאה ביצירת שאילתה: {sql_result.get('error')}",
                    'response': "לא הצלחתי להבין את השאלה או ליצור שאילתה מתאימה."
                }
            
            # Step 2: Execute the generated SQL
            query_result = self.ai_service.execute_query(sql_result['sql'])
            
            if not query_result['success']:
                return {
                    'success': False,
                    'question': question,
                    'sql': sql_result['sql'],
                    'error': f"שגיאה בביצוע השאילתה: {query_result.get('error')}",
                    'response': "אירעה שגיאה בעת ניסיון לקבל את הנתונים מבסיס הנתונים."
                }
            
            # Step 3: Generate a natural language response
            response = self.ai_service.generate_response(question, query_result)
            
            # Prepare the result
            result = {
                'success': True,
                'question': question,
                'response': response,
                'sql': sql_result['sql'],
                'tables': sql_result.get('tables', []),
                'row_count': query_result.get('row_count', 0),
                'data': query_result.get('results', [])
            }
            
            # Add visualization if there's data to show
            if query_result.get('results'):
                result['visualization'] = self._generate_visualization(
                    query_result['results'], 
                    question
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}", exc_info=True)
            return {
                'success': False,
                'question': question,
                'error': str(e),
                'response': "אירעה שגיאה בלתי צפויה בעיבוד השאלה."
            }
    
    def _generate_visualization(self, data: List[Dict], question: str) -> Optional[Dict]:
        """
        Generate a visualization suggestion based on the data and question.
        
        Args:
            data: The query results
            question: The original question
            
        Returns:
            Dictionary with visualization details or None if not applicable
        """
        if not data or len(data) == 0:
            return None
            
        try:
            # Simple heuristic to determine visualization type
            numeric_cols = []
            date_cols = []
            category_cols = []
            
            # Analyze the first row to determine column types
            first_row = data[0]
            for col, value in first_row.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    numeric_cols.append(col)
                elif isinstance(value, str) and len(str(value)) < 50:  # Avoid long text
                    category_cols.append(col)
                elif isinstance(value, (datetime.date, datetime.datetime)):
                    date_cols.append(col)
            
            # Determine visualization type based on available columns
            if date_cols and numeric_cols:
                # Time series data
                return {
                    'type': 'line',
                    'x_axis': date_cols[0],
                    'y_axis': numeric_cols[0],
                    'title': f"{numeric_cols[0]} לאורך זמן"
                }
            elif numeric_cols and category_cols:
                # Categorical data
                return {
                    'type': 'bar',
                    'x_axis': category_cols[0],
                    'y_axis': numeric_cols[0],
                    'title': f"{numeric_cols[0]} לפי {category_cols[0]}"
                }
            elif len(numeric_cols) >= 2:
                # Scatter plot for multiple numeric columns
                return {
                    'type': 'scatter',
                    'x_axis': numeric_cols[0],
                    'y_axis': numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0],
                    'title': f"התפלגות {numeric_cols[1]} מול {numeric_cols[0]}"
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not generate visualization: {str(e)}")
            return None

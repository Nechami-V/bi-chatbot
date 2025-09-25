import spacy
import numpy as np
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import json
import os

class AdvancedAIProcessor:
    """
    Advanced AI processor for natural language to SQL conversion with enhanced NLP capabilities.
    Supports complex queries, Hebrew language processing, and intelligent response generation.
    """
    
    def __init__(self, db: Session):
        """Initialize the AI processor with database session and load NLP models."""
        self.db = db
        self.nlp = self._load_nlp_model()
        self.schema_info = self._analyze_database_schema()
        self.knowledge_graph = self._build_knowledge_graph()
    
    def _load_nlp_model(self):
        """Load the appropriate NLP model, with fallback to small model if needed."""
        try:
            # Try to load Hebrew model
            return spacy.load("he_core_news_lg")
        except OSError:
            # If model not found, download it
            os.system("python -m spacy download he_core_news_lg")
            return spacy.load("he_core_news_lg")
    
    def _analyze_database_schema(self) -> Dict[str, Any]:
        """Analyze database schema to understand table structures and relationships."""
        inspector = inspect(self.db.get_bind())
        schema = {'tables': {}, 'relationships': []}
        
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
                    'referred_columns': fk['referred_columns'],
                    'name': fk.get('name', '')
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
                    'to_columns': fk['referred_columns'],
                    'name': fk.get('name', '')
                })
        
        return schema
    
    def _build_knowledge_graph(self) -> Dict[str, Any]:
        """Build a knowledge graph from database schema and sample data."""
        knowledge_graph = {
            'entities': {},
            'relationships': []
        }
        
        # Add tables as entities
        for table_name, table_info in self.schema_info['tables'].items():
            knowledge_graph['entities'][table_name] = {
                'type': 'table',
                'attributes': [col['name'] for col in table_info['columns']],
                'sample_data': self._get_sample_data(table_name, limit=5)
            }
        
        # Add relationships
        knowledge_graph['relationships'] = self.schema_info['relationships']
        
        return knowledge_graph
    
    def _get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict]:
        """Get sample data from a table."""
        try:
            result = self.db.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception:
            return []
    
    def process_question(self, question: str) -> Dict[str, Any]:
        """Process a natural language question and return a response."""
        try:
            # Step 1: Analyze the question
            analysis = self._analyze_question(question)
            
            # Step 2: Generate SQL query
            query_info = self._generate_sql(analysis)
            
            # Step 3: Execute the query
            results = self._execute_query(query_info['sql'])
            
            # Step 4: Generate response
            response = self._generate_response(question, results, query_info)
            
            return {
                'success': True,
                'question': question,
                'response': response,
                'sql': query_info.get('sql'),
                'analysis': analysis,
                'data': results,
                'visualization': self._generate_visualization(results, analysis)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'question': question
            }
    
    def _analyze_question(self, question: str) -> Dict[str, Any]:
        """Analyze the natural language question."""
        doc = self.nlp(question)
        
        # Extract entities and intents
        entities = [{
            'text': ent.text,
            'label': ent.label_,
            'start': ent.start_char,
            'end': ent.end_char
        } for ent in doc.ents]
        
        # Check for question type
        question_type = self._determine_question_type(doc)
        
        # Extract tables and columns mentioned
        mentioned_tables = []
        mentioned_columns = []
        
        for token in doc:
            # Simple heuristic to identify potential table/column names
            if token.is_alpha and not token.is_stop:
                # Check if token matches any table or column name
                for table_name in self.schema_info['tables'].keys():
                    if token.text.lower() in table_name.lower():
                        mentioned_tables.append(table_name)
                        break
                
                for table_name, table_info in self.schema_info['tables'].items():
                    for col in table_info['columns']:
                        if token.text.lower() == col['name'].lower():
                            mentioned_columns.append({
                                'table': table_name,
                                'column': col['name']
                            })
                            break
        
        # Remove duplicates
        mentioned_tables = list(set(mentioned_tables))
        
        return {
            'question': question,
            'tokens': [token.text for token in doc],
            'entities': entities,
            'question_type': question_type,
            'mentioned_tables': mentioned_tables,
            'mentioned_columns': mentioned_columns,
            'intent': self._determine_intent(doc)
        }
    
    def _determine_question_type(self, doc) -> str:
        """Determine the type of question being asked."""
        question_words = {
            'who': 'PERSON',
            'what': 'THING',
            'when': 'TIME',
            'where': 'PLACE',
            'why': 'REASON',
            'how': 'MANNER',
            'how many': 'QUANTITY',
            'how much': 'QUANTITY'
        }
        
        first_token = doc[0].text.lower()
        for word, q_type in question_words.items():
            if first_token.startswith(word):
                return q_type
        
        return 'GENERAL'
    
    def _determine_intent(self, doc) -> str:
        """Determine the intent of the question."""
        # This is a simplified version - in a real system, you'd use more sophisticated NLP
        text = doc.text.lower()
        
        if any(word in text for word in ['סכום', 'סה"כ', 'סכום כולל']):
            return 'SUM'
        elif any(word in text for word in ['ממוצע', 'ממוצע של']):
            return 'AVERAGE'
        elif any(word in text for word in ['ספור', 'כמה', 'מספר']):
            return 'COUNT'
        elif any(word in text for word in ['הצג', 'הראה', 'תראה']):
            return 'SHOW'
        elif any(word in text for word in ['השווה', 'השוואה']):
            return 'COMPARE'
        
        return 'QUERY'
    
    def _generate_sql(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL query based on question analysis."""
        # This is a simplified version - in a real system, this would be more sophisticated
        tables = analysis.get('mentioned_tables', [])
        
        if not tables:
            # If no tables mentioned, try to infer from columns or use all tables
            columns = [col['column'] for col in analysis.get('mentioned_columns', [])]
            if columns:
                # Find tables that contain the mentioned columns
                for table_name, table_info in self.schema_info['tables'].items():
                    table_columns = [col['name'] for col in table_info['columns']]
                    if any(col in columns for col in table_columns):
                        tables.append(table_name)
            else:
                # If no tables or columns mentioned, use all tables
                tables = list(self.schema_info['tables'].keys())
        
        # Build SELECT clause
        select_columns = []
        if analysis['mentioned_columns']:
            for col_info in analysis['mentioned_columns']:
                select_columns.append(f"{col_info['table']}.{col_info['column']}")
        else:
            # If no specific columns mentioned, select all from the first table
            if tables:
                select_columns.append(f"{tables[0]}.*")
        
        if not select_columns:
            select_columns = ["*"]
        
        # Build FROM clause
        from_clause = ", ".join(tables)
        
        # Build WHERE clause (simplified)
        where_conditions = []
        
        # Add conditions based on entities
        for entity in analysis.get('entities', []):
            if entity['label'] in ['DATE', 'TIME', 'CARDINAL', 'PERCENT']:
                # This is a very simplified approach
                for table in tables:
                    for col in self.schema_info['tables'][table]['columns']:
                        if col['type'].lower() in ['date', 'timestamp', 'integer', 'numeric']:
                            where_conditions.append(f"{table}.{col['name']} = '{entity['text']}'")
                            break
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Build GROUP BY clause
        group_by = ""
        if analysis['intent'] in ['SUM', 'AVERAGE', 'COUNT'] and analysis['mentioned_columns']:
            group_by = f"GROUP BY {', '.join([col['column'] for col in analysis['mentioned_columns']])}"
        
        # Build ORDER BY clause
        order_by = ""
        if analysis['intent'] in ['SHOW', 'COMPARE'] and analysis['mentioned_columns']:
            order_by = f"ORDER BY {analysis['mentioned_columns'][0]['column']} DESC"
        
        # Construct the final query
        sql = f"""
        SELECT {', '.join(select_columns)}
        FROM {from_clause}
        WHERE {where_clause}
        {group_by}
        {order_by}
        LIMIT 100
        """.strip()
        
        return {
            'sql': sql,
            'tables': tables,
            'columns': select_columns,
            'conditions': where_conditions
        }
    
    def _execute_query(self, sql: str) -> List[Dict]:
        """Execute a SQL query and return the results."""
        try:
            result = self.db.execute(text(sql))
            columns = result.keys()
            
            # Convert to list of dicts
            rows = []
            for row in result.fetchall():
                row_dict = {}
                for i, value in enumerate(row):
                    # Convert date/datetime objects to ISO format for JSON serialization
                    if isinstance(value, (date, datetime)):
                        row_dict[columns[i]] = value.isoformat()
                    else:
                        row_dict[columns[i]] = value
                rows.append(row_dict)
            
            return rows
            
        except Exception as e:
            raise Exception(f"שגיאה בביצוע השאילתה: {str(e)}")
    
    def _generate_response(self, question: str, results: List[Dict], query_info: Dict) -> str:
        """Generate a natural language response based on query results."""
        if not results:
            return "לא נמצאו תוצאות התואמות את השאילתך."
        
        # Get analysis from query info
        analysis = query_info.get('analysis', {})
        intent = analysis.get('intent', 'QUERY')
        
        # Generate response based on intent
        if intent == 'COUNT':
            count = len(results)
            return f"נמצאו {count} תוצאות התואמות את השאילתך."
            
        elif intent == 'SUM':
            # Find the first numeric column to sum
            numeric_columns = []
            if results:
                first_row = results[0]
                for col, value in first_row.items():
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        numeric_columns.append(col)
            
            if numeric_columns:
                total = sum(row.get(numeric_columns[0], 0) for row in results)
                return f"הסכום הכולל של {numeric_columns[0]} הוא {total:,.2f}."
            
        elif intent == 'AVERAGE':
            # Find the first numeric column to average
            numeric_columns = []
            if results:
                first_row = results[0]
                for col, value in first_row.items():
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        numeric_columns.append(col)
            
            if numeric_columns:
                values = [row.get(numeric_columns[0], 0) for row in results]
                avg = sum(values) / len(values) if values else 0
                return f"הממוצע של {numeric_columns[0]} הוא {avg:,.2f}."
        
        # Default response for other intents
        result_count = len(results)
        if result_count == 1:
            return f"הנה התוצאה שמצאתי: {json.dumps(results[0], ensure_ascii=False, default=str)}"
        else:
            return f"נמצאו {result_count} תוצאות. להלן הדוגמאות הראשונות: {json.dumps(results[:3], ensure_ascii=False, default=str)}"
    
    def _generate_visualization(self, data: List[Dict], analysis: Dict) -> Optional[Dict]:
        """Generate visualization for the query results."""
        if not data:
            return None
        
        try:
            df = pd.DataFrame(data)
            
            # Simple heuristic to determine the best visualization
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            category_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            # If we have both numeric and category columns, create a bar chart
            if numeric_cols and category_cols:
                x_col = category_cols[0]
                y_col = numeric_cols[0]
                
                # Limit to top 10 categories for better visualization
                if len(df) > 10:
                    df = df.nlargest(10, y_col)
                
                fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} לפי {x_col}")
                return {
                    'type': 'bar',
                    'data': fig.to_dict(),
                    'title': f"{y_col} לפי {x_col}"
                }
            
            # If we have dates, create a time series
            date_cols = [col for col in df.columns if any(term in col.lower() for term in ['date', 'time', 'timestamp'])]
            if date_cols and numeric_cols:
                date_col = date_cols[0]
                y_col = numeric_cols[0]
                
                # Convert to datetime if needed
                if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                
                # Sort by date
                df = df.sort_values(date_col).dropna(subset=[date_col])
                
                fig = px.line(df, x=date_col, y=y_col, title=f"{y_col} לאורך זמן")
                return {
                    'type': 'line',
                    'data': fig.to_dict(),
                    'title': f"{y_col} לאורך זמן"
                }
            
            # Default to a simple table if no good visualization found
            return {
                'type': 'table',
                'data': df.head(10).to_dict('records'),
                'title': 'תוצאות השאילתה'
            }
            
        except Exception as e:
            print(f"Error generating visualization: {str(e)}")
            return None

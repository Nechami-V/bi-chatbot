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
        
        # Analyze all available tables in the connected database
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
        
        # Create the prompt for the AI (strict JSON-only response) in English
        prompt = f"""
Given this database schema (JSON):
{schema_info}

User question (can be in Hebrew): "{question}"

Generate a precise SQL query following these rules:
1) Use only columns and tables that exist in the schema. Do NOT invent tables/columns.
2) Join tables only when necessary, using proper JOINs.
3) Avoid SELECT * — specify explicit column names.
4) Ensure SQLite compatibility.
5) For the intent "show customers" (development default): use table customer with columns: id, name, city, created_at.
6) Do NOT add ORDER BY unless the question explicitly asks for sorting (e.g., "by last name" / "by date").
7) For display queries ("show ..."), add LIMIT 100 by default.
8) If the question contains Hebrew filter values (e.g., a city), use them verbatim in WHERE clauses.

 Disambiguation rules (very important):
 9) Hebrew phrase "לפי <field>" means ORDER BY <field> (sorting), NOT aggregation. Do NOT use GROUP BY unless the user asked for a count/summary.
 10) Hebrew words indicating count/aggregation: "כמה", "כמות", "מספר", "ספירה". Only when these appear should you use COUNT/GROUP BY.
 11) Example: "הצג לקוחות לפי עיר" means: list customers with their fields, ORDER BY city; do NOT GROUP BY city and do NOT COUNT.
 12) Example: "כמה לקוחות יש בכל עיר" means: grouped count per city using COUNT and GROUP BY city.

Return output as JSON only, with no explanations/markdown:
{{
  "sql": "valid SQL query",
  "tables": ["Table1", "Table2"],
  "description": "A short Hebrew description of what the query returns"
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
                sql_text = result.get('sql', '')
                # Prefer 'customer' table for 'לקוחות' if both exist
                try:
                    available_tables = set(self.schema_info.get('tables', {}).keys())
                    if 'לקוחות' in question and 'customer' in available_tables and 'ClientsBot2025' in available_tables:
                        sql_text = sql_text.replace('ClientsBot2025', 'customer')
                except Exception:
                    pass
                return {
                    'success': True,
                    'sql': sql_text,
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
    
    def generate_response(self, question: str, query_results: Dict[str, Any], sql: str) -> str:
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
            
            # Extract simple SQL semantics for consistent wording
            sql_l = (sql or "").strip().lower()
            is_aggregation = (" group by " in sql_l) or ("count(" in sql_l) or (" sum(" in sql_l) or (" avg(" in sql_l)
            order_by_field = None
            if " order by " in sql_l:
                try:
                    ob_clause = sql_l.split(" order by ", 1)[1]
                    # take first token (field name) before comma or space
                    order_by_field = ob_clause.split(",")[0].strip().split()[0]
                except Exception:
                    order_by_field = None
            
            # Create the prompt for the AI (natural-language answer only) — prompt in English, answer in Hebrew
            prompt = f"""
User asked (Hebrew possible): {question}

Result summary for you:
- Row count: {context['row_count']}
- Sample (up to 3 rows): {json.dumps(context['sample_data'], ensure_ascii=False, default=str)}

Answer instructions:
- Reply in Hebrew, in 1–2 short sentences.
- Do NOT show SQL, JSON, code or markdown.
- If names/cities appear in the sample, you may mention them briefly.
- If there is no data, say there are no results.

 IMPORTANT semantic constraints — your text must reflect the actual SQL:
 - SQL: {sql}
 - Aggregation present: {is_aggregation}
 - ORDER BY field (if any): {order_by_field}
 - If Aggregation present is False: do NOT describe counts/summaries. Describe a list of rows. If there is an ORDER BY field, say it is sorted by that field in Hebrew.
 - If Aggregation present is True: describe a summary (e.g., counts per city) and do NOT claim a simple list.
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
            print(f"   AI Response (raw): {ai_response}")
            clean = self._clean_answer_text(ai_response, query_results)
            print(f"   AI Response (clean): {clean}")
            return clean
            
        except Exception as e:
            error_msg = f"אירעה שגיאה ביצירת התשובה: {str(e)}"
            print(f"   Error in generate_response: {error_msg}")
            return error_msg

    def _clean_answer_text(self, text: str, query_results: Dict[str, Any]) -> str:
        """Ensure the final answer is a short Hebrew sentence without SQL/JSON/Markdown."""
        try:
            # Strip code fences and markdown artifacts
            txt = text.strip()
            if txt.startswith("```") and txt.endswith("```"):
                txt = txt.strip("`")
            # If JSON slipped through, try to parse and use description
            if (txt.startswith("{") and txt.endswith("}")) or '"sql"' in txt:
                try:
                    data = json.loads(txt)
                    desc = data.get("description")
                    if isinstance(desc, str) and desc.strip():
                        return desc.strip()
                except Exception:
                    pass
            # Collapse to one or two short sentences
            txt = txt.replace("\n", " ").replace("\r", " ")
            txt = txt.replace("  ", " ").strip()
            if len(txt) > 220:
                # fallback to summary using row_count
                rc = query_results.get("row_count", 0)
                return f"נמצאו {rc} רשומות רלוונטיות לשאלה."
            return txt
        except Exception:
            rc = query_results.get("row_count", 0)
            return f"נמצאו {rc} רשומות."

"""
Generic Database Schema Inspector
Reads database schema dynamically from any database - no hardcoded tables or columns
Works with any client database structure
"""

import logging
from typing import Dict, Any, List
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class GenericSchemaInspector:
    """Generic schema inspector that works with any database"""
    
    def __init__(self, db: Session):
        self.db = db
        self.inspector = inspect(db.bind)
        self._schema_cache = None
    
    def get_schema(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get complete database schema dynamically"""
        if self._schema_cache is not None and not force_refresh:
            return self._schema_cache
            
        try:
            logger.info("Inspecting database schema dynamically...")
            
            schema = {
                "tables": {},
                "relationships": []
            }
            
            # Get all table names
            table_names = self.inspector.get_table_names()
            logger.info(f"Found {len(table_names)} tables: {table_names}")
            
            # Inspect each table
            for table_name in table_names:
                table_info = self._inspect_table(table_name)
                if table_info:
                    schema["tables"][table_name] = table_info
            
            # Cache the result
            self._schema_cache = schema
            logger.info(f"Successfully inspected schema with {len(schema['tables'])} tables")
            
            return schema
            
        except Exception as e:
            logger.error(f"Failed to inspect database schema: {e}")
            return {"tables": {}, "relationships": []}
    
    def _inspect_table(self, table_name: str) -> Dict[str, Any]:
        """Inspect a single table structure"""
        try:
            # Get column information
            columns = self.inspector.get_columns(table_name)
            primary_keys = self.inspector.get_pk_constraint(table_name)
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            
            # Convert to our schema format
            table_info = {
                "display_name": self._make_display_name(table_name),
                "description": f"Table: {table_name}",
                "columns": [],
                "is_fact_table": self._is_fact_table(table_name),
                "row_count": self._get_row_count(table_name)
            }
            
            # Process columns
            pk_columns = primary_keys.get('constrained_columns', []) if primary_keys else []
            
            for col in columns:
                column_info = {
                    "name": col['name'],
                    "logical_name": col['name'],
                    "display_name": self._make_display_name(col['name']),
                    "type": str(col['type']),
                    "nullable": col['nullable'],
                    "primary_key": col['name'] in pk_columns,
                    "description": f"Column: {col['name']}"
                }
                table_info["columns"].append(column_info)
            
            return table_info
            
        except Exception as e:
            logger.warning(f"Failed to inspect table {table_name}: {e}")
            return None
    
    def _make_display_name(self, name: str) -> str:
        """Convert technical name to display name"""
        # Simple heuristics for better display names
        if name.startswith('ID_'):
            return f"מזהה {name[3:]}"
        elif name.lower() in ['name', 'fname', 'first_name']:
            return "שם"
        elif name.lower() in ['lname', 'last_name']:
            return "שם משפחה"
        elif name.lower() in ['city', 'עיר']:
            return "עיר"
        elif name.lower() in ['date', 'תאריך']:
            return "תאריך"
        elif name.lower() in ['amount', 'sum', 'סכום']:
            return "סכום"
        else:
            return name  # Keep original name if no pattern matches
    
    def _is_fact_table(self, table_name: str) -> bool:
        """Determine if table is a fact table based on naming patterns"""
        fact_patterns = ['order', 'sale', 'transaction', 'הזמנ', 'מכיר']
        table_lower = table_name.lower()
        return any(pattern in table_lower for pattern in fact_patterns)
    
    def _get_row_count(self, table_name: str) -> int:
        """Get approximate row count for table"""
        try:
            result = self.db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            return count or 0
        except Exception as e:
            logger.warning(f"Could not get row count for {table_name}: {e}")
            return 0
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get specific table information"""
        schema = self.get_schema()
        return schema["tables"].get(table_name, {})
    
    def get_all_tables(self) -> List[str]:
        """Get list of all table names"""
        schema = self.get_schema()
        return list(schema["tables"].keys())
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict]:
        """Get sample data from table"""
        try:
            result = self.db.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
            columns = result.keys()
            rows = result.fetchall()
            
            sample_data = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                sample_data.append(row_dict)
            
            return sample_data
            
        except Exception as e:
            logger.warning(f"Could not get sample data from {table_name}: {e}")
            return []
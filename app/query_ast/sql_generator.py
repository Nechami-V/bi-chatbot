"""
SQL Generator from AST
Converts AST representation to dialect-specific SQL
Supports multiple database backends through visitor pattern
Each database type gets its own generator with specific SQL dialect support
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .ast_nodes import (
    QueryVisitor, SelectQuery, ShortcutQuery, EntityRef, AttributeRef,
    FilterCondition, AggregateFunction, SortClause, ParsedQuery,
    AggregationType, FilterOperator, SortDirection
)
from app.config_loader import config_loader
from app.config_models import Datasource, Mappings, DatabaseType

logger = logging.getLogger(__name__)

class SQLGenerator(QueryVisitor):
    """Base SQL generator using visitor pattern"""
    
    def __init__(self, client_id: str = "sample-client"):
        self.client_id = client_id
        self._datasource: Optional[Datasource] = None
        self._mappings: Optional[Mappings] = None
        
    def _load_config(self):
        """Load datasource configuration"""
        if self._datasource is None:
            self._datasource, self._mappings = config_loader.load_client_config(self.client_id)
    
    def generate_sql(self, parsed_query: ParsedQuery) -> str:
        """
        Generate SQL from parsed query
        
        Args:
            parsed_query: Parsed query with AST
            
        Returns:
            Generated SQL string
        """
        self._load_config()
        return parsed_query.query_node.accept(self)
    
    @abstractmethod
    def visit_select_query(self, query: SelectQuery) -> str:
        """Generate SQL for SELECT query"""
        pass
    
    @abstractmethod
    def visit_shortcut_query(self, query: ShortcutQuery) -> str:
        """Generate SQL for shortcut query"""
        pass
    
    def _get_physical_table(self, entity_name: str) -> str:
        """Get physical table name for entity"""
        if entity_name not in self._datasource.table_mappings:
            raise ValueError(f"No table mapping found for entity: {entity_name}")
        
        return self._datasource.table_mappings[entity_name].physical_table
    
    def _get_physical_column(self, entity_name: str, attribute_name: str) -> str:
        """Get physical column name for attribute"""
        if entity_name not in self._datasource.table_mappings:
            raise ValueError(f"No table mapping found for entity: {entity_name}")
            
        table_mapping = self._datasource.table_mappings[entity_name]
        
        if attribute_name not in table_mapping.columns:
            raise ValueError(f"No column mapping found for {entity_name}.{attribute_name}")
        
        return table_mapping.columns[attribute_name]
    
    def translate_sql_functions(self, sql: str) -> str:
        """Translate generic SQL functions to database-specific ones"""
        # Base implementation - override in subclasses
        return sql
    
    def _translate_column_names_in_condition(self, condition: str, entity_name: str) -> str:
        """Translate logical column names to physical column names in a condition string"""
        if entity_name not in self._datasource.table_mappings:
            return condition
            
        table_mapping = self._datasource.table_mappings[entity_name]
        translated_condition = condition
        
        # Replace each logical column name with its physical equivalent
        for logical_col, physical_col in table_mapping.columns.items():
            # Replace standalone column names (word boundaries)
            import re
            pattern = r'\b' + re.escape(logical_col) + r'\b'
            translated_condition = re.sub(pattern, physical_col, translated_condition)
        
        return translated_condition

class SQLiteGenerator(SQLGenerator):
    """SQLite-specific SQL generator"""
    
    def get_year_function(self, column_name: str) -> str:
        """SQLite YEAR function equivalent"""
        return f"strftime('%Y', {column_name})"
    
    def get_month_function(self, column_name: str) -> str:
        """SQLite MONTH function equivalent"""
        return f"strftime('%m', {column_name})"
    
    def get_current_date(self) -> str:
        """SQLite current date"""
        return "date('now')"
    
    def get_current_year(self) -> str:
        """SQLite current year"""
        return "strftime('%Y', 'now')"
    
    def translate_sql_functions(self, sql: str) -> str:
        """Translate generic SQL functions to SQLite-specific ones"""
        # Replace YEAR() with strftime()
        import re
        
        # Replace YEAR(column) with strftime('%Y', column)
        sql = re.sub(r'YEAR\(([^)]+)\)', r"strftime('%Y', \1)", sql)
        
        # Replace MONTH(column) with strftime('%m', column)  
        sql = re.sub(r'MONTH\(([^)]+)\)', r"strftime('%m', \1)", sql)
        
        # Replace YEAR(CURRENT_DATE) with strftime('%Y', 'now')
        sql = sql.replace("YEAR(CURRENT_DATE)", "strftime('%Y', 'now')")
        sql = sql.replace("MONTH(CURRENT_DATE)", "strftime('%m', 'now')")
        
        # Replace CURRENT_DATE with 'now'
        sql = sql.replace("CURRENT_DATE", "'now'")
        
        return sql
    
    def visit_select_query(self, query: SelectQuery) -> str:
        """Generate SQLite SELECT statement"""
        
        if not query.entities:
            return "-- No entities specified"
        
        # Build SELECT clause
        select_parts = []
        
        if query.aggregates:
            # Handle aggregations
            for agg in query.aggregates:
                if agg.attribute:
                    # Aggregate on specific attribute
                    physical_col = self._get_physical_column(agg.attribute.entity, agg.attribute.attribute)
                    agg_expr = f"{agg.function.value}({physical_col})"
                else:
                    # COUNT(*) or similar
                    agg_expr = f"{agg.function.value}(*)"
                
                if agg.alias:
                    agg_expr += f" AS {agg.alias}"
                
                select_parts.append(agg_expr)
        else:
            # Regular SELECT
            if query.attributes:
                # Select specific attributes
                for attr in query.attributes:
                    physical_col = self._get_physical_column(attr.entity, attr.attribute)
                    if attr.alias:
                        select_parts.append(f"{physical_col} AS {attr.alias}")
                    else:
                        select_parts.append(physical_col)
            else:
                # SELECT *
                select_parts.append("*")
        
        select_clause = "SELECT " + ", ".join(select_parts)
        
        # Build FROM clause
        # For now, handle single table queries
        main_entity = query.entities[0]
        main_table = self._get_physical_table(main_entity.name)
        from_clause = f"FROM {main_table}"
        
        if main_entity.alias:
            from_clause += f" AS {main_entity.alias}"
        
        # Build WHERE clause
        where_parts = []
        
        # Add default filters from business rules
        if (self._mappings.business_rules and 
            self._mappings.business_rules.default_filters and 
            main_entity.name in self._mappings.business_rules.default_filters):
            
            default_filters = self._mappings.business_rules.default_filters[main_entity.name]
            for field, condition in default_filters.items():
                # Translate logical column names to physical column names in condition
                translated_condition = self._translate_column_names_in_condition(condition, main_entity.name)
                where_parts.append(translated_condition)
        
        # Add explicit filters
        for filter_cond in query.filters:
            physical_col = self._get_physical_column(filter_cond.attribute.entity, filter_cond.attribute.attribute)
            
            # Format value based on type
            if isinstance(filter_cond.value, str):
                formatted_value = f"'{filter_cond.value}'"
            else:
                formatted_value = str(filter_cond.value)
            
            condition = f"{physical_col} {filter_cond.operator.value} {formatted_value}"
            
            if filter_cond.negate:
                condition = f"NOT ({condition})"
            
            where_parts.append(condition)
        
        where_clause = ""
        if where_parts:
            where_clause = "WHERE " + " AND ".join(where_parts)
        
        # Build GROUP BY clause
        group_by_clause = ""
        if query.group_by:
            group_by_cols = []
            for attr in query.group_by:
                physical_col = self._get_physical_column(attr.entity, attr.attribute)
                group_by_cols.append(physical_col)
            group_by_clause = "GROUP BY " + ", ".join(group_by_cols)
        
        # Build ORDER BY clause
        order_by_clause = ""
        
        # Add explicit sorts
        order_by_parts = []
        for sort in query.sorts:
            physical_col = self._get_physical_column(sort.attribute.entity, sort.attribute.attribute)
            order_by_parts.append(f"{physical_col} {sort.direction.value}")
        
        # Add default ordering from business rules
        if (not order_by_parts and 
            self._mappings.business_rules and 
            self._mappings.business_rules.default_ordering and 
            main_entity.name in self._mappings.business_rules.default_ordering):
            
            default_order = self._mappings.business_rules.default_ordering[main_entity.name]
            order_by_parts.append(default_order)
        
        if order_by_parts:
            order_by_clause = "ORDER BY " + ", ".join(order_by_parts)
        
        # Build LIMIT clause
        limit_clause = ""
        if query.limit:
            limit_clause = f"LIMIT {query.limit}"
        
        # Combine all parts
        sql_parts = [select_clause, from_clause]
        
        if where_clause:
            sql_parts.append(where_clause)
        if group_by_clause:
            sql_parts.append(group_by_clause)
        if order_by_clause:
            sql_parts.append(order_by_clause)  
        if limit_clause:
            sql_parts.append(limit_clause)
        
        final_sql = " ".join(sql_parts)
        return self.translate_sql_functions(final_sql)
    
    def visit_shortcut_query(self, query: ShortcutQuery) -> str:
        """Return predefined SQL for shortcut with database-specific translation"""
        return self.translate_sql_functions(query.sql)

class SQLServerGenerator(SQLGenerator):
    """SQL Server-specific SQL generator"""
    
    def visit_select_query(self, query: SelectQuery) -> str:
        # Similar to SQLite but with SQL Server syntax differences
        # For now, delegate to SQLite implementation
        sqlite_gen = SQLiteGenerator(self.client_id)
        sqlite_gen._datasource = self._datasource
        sqlite_gen._mappings = self._mappings
        
        sql = sqlite_gen.visit_select_query(query)
        
        # Apply SQL Server specific transformations
        if query.limit and "LIMIT" in sql:
            # Replace LIMIT with TOP clause
            sql = sql.replace(f"LIMIT {query.limit}", "")
            sql = sql.replace("SELECT ", f"SELECT TOP {query.limit} ")
        
        return self.translate_sql_functions(sql)
    
    def visit_shortcut_query(self, query: ShortcutQuery) -> str:
        return self.translate_sql_functions(query.sql)

class MySQLGenerator(SQLGenerator):
    """MySQL-specific SQL generator"""
    
    def visit_select_query(self, query: SelectQuery) -> str:
        # Similar to SQLite for basic queries
        sqlite_gen = SQLiteGenerator(self.client_id)
        sqlite_gen._datasource = self._datasource
        sqlite_gen._mappings = self._mappings
        return sqlite_gen.visit_select_query(query)
    
    def visit_shortcut_query(self, query: ShortcutQuery) -> str:
        return query.sql


class SQLServerGenerator(SQLGenerator):
    """SQL Server specific SQL generator"""
    
    def get_year_function(self, column_name: str) -> str:
        """SQL Server YEAR function"""
        return f"YEAR({column_name})"
    
    def get_month_function(self, column_name: str) -> str:
        """SQL Server MONTH function"""
        return f"MONTH({column_name})"
    
    def get_current_date(self) -> str:
        """SQL Server current date"""
        return "GETDATE()"
    
    def get_current_year(self) -> str:
        """SQL Server current year"""
        return "YEAR(GETDATE())"
    
    def translate_sql_functions(self, sql: str) -> str:
        """Translate generic SQL functions to SQL Server-specific ones"""
        # SQL Server mostly uses standard SQL
        # Just need to replace CURRENT_DATE with GETDATE()
        sql = sql.replace("CURRENT_DATE", "GETDATE()")
        return sql
    
    def visit_select_query(self, query: SelectQuery) -> str:
        """Generate SQL Server SELECT statement with TOP clause"""
        # Similar to SQLite but with TOP instead of LIMIT
        # Implementation would be similar to SQLiteGenerator but with SQL Server syntax
        sqlite_gen = SQLiteGenerator(self.client_id)
        sqlite_gen._datasource = self._datasource
        sqlite_gen._mappings = self._mappings
        sql = sqlite_gen.visit_select_query(query)
        
        # Convert LIMIT to TOP (basic conversion)
        if " LIMIT " in sql:
            parts = sql.split(" LIMIT ")
            if len(parts) == 2:
                select_part, limit_part = parts
                limit_num = limit_part.strip()
                sql = select_part.replace("SELECT", f"SELECT TOP {limit_num}")
        
        return sql
    
    def visit_shortcut_query(self, query: ShortcutQuery) -> str:
        return query.sql


class MySQLGenerator(SQLGenerator):
    """MySQL specific SQL generator"""
    
    def get_year_function(self, column_name: str) -> str:
        """MySQL YEAR function"""
        return f"YEAR({column_name})"
    
    def get_month_function(self, column_name: str) -> str:
        """MySQL MONTH function"""
        return f"MONTH({column_name})"
    
    def get_current_date(self) -> str:
        """MySQL current date"""
        return "CURDATE()"
    
    def get_current_year(self) -> str:
        """MySQL current year"""
        return "YEAR(CURDATE())"
    
    def translate_sql_functions(self, sql: str) -> str:
        """Translate generic SQL functions to MySQL-specific ones"""
        # MySQL uses CURDATE() instead of CURRENT_DATE
        sql = sql.replace("CURRENT_DATE", "CURDATE()")
        return sql
    
    def visit_select_query(self, query: SelectQuery) -> str:
        """Generate MySQL SELECT statement"""
        # MySQL syntax is very similar to SQLite for basic queries
        sqlite_gen = SQLiteGenerator(self.client_id)
        sqlite_gen._datasource = self._datasource
        sqlite_gen._mappings = self._mappings
        sql = sqlite_gen.visit_select_query(query)
        return self.translate_sql_functions(sql)
    
    def visit_shortcut_query(self, query: ShortcutQuery) -> str:
        return self.translate_sql_functions(query.sql)

def create_sql_generator(client_id: str = "sample-client") -> SQLGenerator:
    """
    Factory function to create appropriate SQL generator based on datasource
    
    Args:
        client_id: Client configuration identifier
        
    Returns:
        Appropriate SQL generator instance
    """
    datasource, _ = config_loader.load_client_config(client_id)
    
    if datasource.database_type.value == "sqlite":
        return SQLiteGenerator(client_id)
    elif datasource.database_type.value == "sqlserver":
        return SQLServerGenerator(client_id)
    elif datasource.database_type.value == "mysql":
        return MySQLGenerator(client_id)
    elif datasource.database_type.value == "postgresql":
        return MySQLGenerator(client_id)  # PostgreSQL similar to MySQL for basic queries
    else:
        logger.warning(f"Unknown database type: {datasource.database_type}, using SQLite generator")
        return SQLiteGenerator(client_id)
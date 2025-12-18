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
        
        # Add default ordering from business rules ONLY if:
        # 1. No explicit ordering specified
        # 2. No aggregations (aggregates require columns to be in SELECT or GROUP BY)
        if (not order_by_parts and 
            not query.aggregates and  # Don't apply default ordering with aggregations
            self._mappings.business_rules and 
            self._mappings.business_rules.default_ordering and 
            main_entity.name in self._mappings.business_rules.default_ordering):
            
            default_order = self._mappings.business_rules.default_ordering[main_entity.name]
            order_by_parts.append(default_order)
        
        if order_by_parts:
            order_by_clause = "ORDER BY " + ", ".join(order_by_parts)
        
        # Build TOP clause
        top = ""
        if query.top:
            top = f"TOP {query.top}"
        
        # Combine all parts
        sql_parts = [select_clause, from_clause]
        
        if where_clause:
            sql_parts.append(where_clause)
        if group_by_clause:
            sql_parts.append(group_by_clause)
        if order_by_clause:
            sql_parts.append(order_by_clause)  
        if top:
            sql_parts.append(top)
        
        final_sql = " ".join(sql_parts)
        return self.translate_sql_functions(final_sql)
    
    def visit_shortcut_query(self, query: ShortcutQuery) -> str:
        """Return predefined SQL for shortcut with database-specific translation"""
        return self.translate_sql_functions(query.sql)

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
        """Translate SQLite, PostgreSQL and MySQL functions to SQL Server-specific ones"""
        import re
        
        # MySQL/PostgreSQL DATE(NOW()) or DATE(GETDATE()) -> CAST(GETDATE() AS DATE)
        sql = re.sub(r"\bDATE\(\s*NOW\(\)\s*\)", "CAST(GETDATE() AS DATE)", sql, flags=re.IGNORECASE)
        sql = re.sub(r"\bDATE\(\s*GETDATE\(\)\s*\)", "CAST(GETDATE() AS DATE)", sql, flags=re.IGNORECASE)
        
        # Generic pattern: DATE(...) - INTERVAL N DAY -> DATEADD(day, -N, CAST(... AS DATE))
        # Must run BEFORE we translate NOW() and CURDATE()
        sql = re.sub(
            r"DATE\(\s*NOW\(\)\s*\)\s*-\s*INTERVAL\s+(\d+)\s+DAY",
            r"DATEADD(day, -\1, CAST(GETDATE() AS DATE))",
            sql,
            flags=re.IGNORECASE
        )
        
        sql = re.sub(
            r"DATE\(\s*GETDATE\(\)\s*\)\s*-\s*INTERVAL\s+(\d+)\s+DAY",
            r"DATEADD(day, -\1, CAST(GETDATE() AS DATE))",
            sql,
            flags=re.IGNORECASE
        )
        
        # Pattern: CAST(GETDATE() AS DATE) - INTERVAL N DAY -> DATEADD(day, -N, CAST(GETDATE() AS DATE))
        sql = re.sub(
            r"CAST\(\s*GETDATE\(\)\s*AS\s+DATE\)\s*-\s*INTERVAL\s+(\d+)\s+DAY",
            r"DATEADD(day, -\1, CAST(GETDATE() AS DATE))",
            sql,
            flags=re.IGNORECASE
        )
        
        # MySQL CURDATE() -> CAST(GETDATE() AS DATE)
        sql = re.sub(r"\bCURDATE\(\)", "CAST(GETDATE() AS DATE)", sql, flags=re.IGNORECASE)
        
        # MySQL NOW() -> GETDATE()
        sql = re.sub(r"\bNOW\(\)", "GETDATE()", sql, flags=re.IGNORECASE)
        
        # MySQL DATE_SUB(CURDATE(), INTERVAL N DAY) -> DATEADD(day, -N, GETDATE())
        sql = re.sub(
            r"DATE_SUB\(\s*CURDATE\(\)\s*,\s*INTERVAL\s+(\d+)\s+DAY\s*\)",
            r"DATEADD(day, -\1, CAST(GETDATE() AS DATE))",
            sql,
            flags=re.IGNORECASE
        )
        
        # MySQL DATE_SUB(NOW(), INTERVAL N DAY) -> DATEADD(day, -N, GETDATE())
        sql = re.sub(
            r"DATE_SUB\(\s*NOW\(\)\s*,\s*INTERVAL\s+(\d+)\s+DAY\s*\)",
            r"DATEADD(day, -\1, GETDATE())",
            sql,
            flags=re.IGNORECASE
        )
        
        # Generic DATE_SUB(..., INTERVAL N WEEK) -> DATEADD(week, -N, ...)
        def _replace_date_sub_interval(match):
            expr = match.group(1).strip()
            amount = match.group(2)
            unit = match.group(3).lower()
            unit_map = {
                "day": "day",
                "week": "week",
                "month": "month",
                "year": "year",
                "hour": "hour",
                "minute": "minute",
                "second": "second",
            }
            sql_unit = unit_map.get(unit, unit)
            return f"DATEADD({sql_unit}, -{amount}, {expr})"

        sql = re.sub(
            r"DATE_SUB\(\s*(.+?)\s*,\s*INTERVAL\s+(\d+)\s+(DAY|WEEK|MONTH|YEAR|HOUR|MINUTE|SECOND)\s*\)",
            _replace_date_sub_interval,
            sql,
            flags=re.IGNORECASE | re.DOTALL
        )

        # MySQL DATE_ADD(CURDATE(), INTERVAL N DAY) -> DATEADD(day, N, GETDATE())
        sql = re.sub(
            r"DATE_ADD\(\s*CURDATE\(\)\s*,\s*INTERVAL\s+(\d+)\s+DAY\s*\)",
            r"DATEADD(day, \1, CAST(GETDATE() AS DATE))",
            sql,
            flags=re.IGNORECASE
        )
        
        # Generic DATE_ADD(..., INTERVAL N UNIT) -> DATEADD(UNIT, N, ...)
        def _replace_date_add_interval(match):
            expr = match.group(1).strip()
            amount = match.group(2)
            unit = match.group(3).lower()
            unit_map = {
                "day": "day",
                "week": "week",
                "month": "month",
                "year": "year",
                "hour": "hour",
                "minute": "minute",
                "second": "second",
            }
            sql_unit = unit_map.get(unit, unit)
            return f"DATEADD({sql_unit}, {amount}, {expr})"

        sql = re.sub(
            r"DATE_ADD\(\s*(.+?)\s*,\s*INTERVAL\s+(\d+)\s+(DAY|WEEK|MONTH|YEAR|HOUR|MINUTE|SECOND)\s*\)",
            _replace_date_add_interval,
            sql,
            flags=re.IGNORECASE | re.DOTALL
        )

        # PostgreSQL DATE_TRUNC('month', column) -> DATEADD(month, DATEDIFF(month, 0, column), 0)
        # Simpler alternative: just use YEAR/MONTH grouping
        sql = re.sub(
            r"DATE_TRUNC\(['\"]month['\"]\s*,\s*([a-zA-Z_][a-zA-Z0-9_.]+)\)",
            r"DATEADD(month, DATEDIFF(month, 0, \1), 0)",
            sql,
            flags=re.IGNORECASE
        )
        
        # PostgreSQL DATE_TRUNC('year', column) -> DATEADD(year, DATEDIFF(year, 0, column), 0)
        sql = re.sub(
            r"DATE_TRUNC\(['\"]year['\"]\s*,\s*([a-zA-Z_][a-zA-Z0-9_.]+)\)",
            r"DATEADD(year, DATEDIFF(year, 0, \1), 0)",
            sql,
            flags=re.IGNORECASE
        )
        
        # PostgreSQL DATE_TRUNC('week', column) -> DATEADD(week, DATEDIFF(week, 0, column), 0)
        sql = re.sub(
            r"DATE_TRUNC\(['\"]week['\"]\s*,\s*([a-zA-Z_][a-zA-Z0-9_.]+)\)",
            r"DATEADD(week, DATEDIFF(week, 0, \1), 0)",
            sql,
            flags=re.IGNORECASE
        )

        # Generic WEEK(column) -> DATEPART(week, column)
        sql = re.sub(
            r"\bWEEK\s*\(\s*([a-zA-Z_][a-zA-Z0-9_.]+)\s*\)",
            r"DATEPART(week, \1)",
            sql,
            flags=re.IGNORECASE
        )

        # PostgreSQL DATE_TRUNC('day', column) -> CAST(column AS DATE)
        sql = re.sub(
            r"DATE_TRUNC\(['\"]day['\"]\s*,\s*([a-zA-Z_][a-zA-Z0-9_.]+)\)",
            r"CAST(\1 AS DATE)",
            sql,
            flags=re.IGNORECASE
        )
        
        # PostgreSQL INTERVAL '1 year' -> year, -1 for DATEADD
        # Pattern: DATE_TRUNC(...) - INTERVAL '1 year' -> DATEADD(year, -1, DATE_TRUNC(...))
        sql = re.sub(
            r"(DATEADD\([^)]+\))\s*-\s*INTERVAL\s+['\"](\d+)\s+year['\"]",
            r"DATEADD(year, -\2, \1)",
            sql,
            flags=re.IGNORECASE
        )
        
        # Simpler: column >= CURRENT_DATE - INTERVAL '1 year' -> column >= DATEADD(year, -1, GETDATE())
        sql = re.sub(
            r">=\s*CURRENT_DATE\s*-\s*INTERVAL\s+['\"](\d+)\s+year['\"]",
            r">= DATEADD(year, -\1, GETDATE())",
            sql,
            flags=re.IGNORECASE
        )
        
        # CURRENT_DATE -> CAST(GETDATE() AS DATE)
        sql = re.sub(r"\bCURRENT_DATE\b", "CAST(GETDATE() AS DATE)", sql, flags=re.IGNORECASE)
        
        # Replace SQLite strftime with SQL Server functions
        # strftime('%Y', column) -> YEAR(column)
        sql = re.sub(r"strftime\(['\"]%Y['\"]\s*,\s*([a-zA-Z_][a-zA-Z0-9_.]+)\)", r"YEAR(\1)", sql, flags=re.IGNORECASE)
        
        # strftime('%m', column) -> MONTH(column)  
        sql = re.sub(r"strftime\(['\"]%m['\"]\s*,\s*([a-zA-Z_][a-zA-Z0-9_.]+)\)", r"MONTH(\1)", sql, flags=re.IGNORECASE)
        
        # strftime('%W', column) -> DATEPART(week, column)
        sql = re.sub(r"strftime\(['\"]%W['\"]\s*,\s*([a-zA-Z_][a-zA-Z0-9_.]+)\)", r"DATEPART(week, \1)", sql, flags=re.IGNORECASE)
        
        # date('now') or 'now' -> GETDATE()
        sql = sql.replace("date('now')", "GETDATE()")
        sql = sql.replace("'now'", "GETDATE()")
        
        return sql
    
    def visit_select_query(self, query: SelectQuery) -> str:
        """Generate SQL Server SELECT statement with TOP clause"""
        
        if not query.entities:
            return "-- No entities specified"
        
        # Build SELECT clause
        select_parts = []
        
        # Handle TOP clause if limit is specified
        top_clause = ""
        if query.limit:
            top_clause = f"TOP {query.limit} "
        
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
        
        select_clause = f"SELECT {top_clause}" + ", ".join(select_parts)
        
        # Build FROM clause
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
        
        # Add default ordering from business rules ONLY if:
        # 1. No explicit ordering specified
        # 2. No aggregations (aggregates require columns to be in SELECT or GROUP BY)
        if (not order_by_parts and 
            not query.aggregates and  # Don't apply default ordering with aggregations
            self._mappings.business_rules and 
            self._mappings.business_rules.default_ordering and 
            main_entity.name in self._mappings.business_rules.default_ordering):
            
            default_order = self._mappings.business_rules.default_ordering[main_entity.name]
            order_by_parts.append(default_order)
        
        if order_by_parts:
            order_by_clause = "ORDER BY " + ", ".join(order_by_parts)
        
        # Combine all parts (no LIMIT clause for SQL Server, we use TOP)
        sql_parts = [select_clause, from_clause]
        
        if where_clause:
            sql_parts.append(where_clause)
        if group_by_clause:
            sql_parts.append(group_by_clause)
        if order_by_clause:
            sql_parts.append(order_by_clause)
        
        final_sql = " ".join(sql_parts)
        return self.translate_sql_functions(final_sql)
    
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
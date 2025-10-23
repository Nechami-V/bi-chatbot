"""
Query AST Package
Abstract Syntax Tree representation and processing for Hebrew queries
"""

from .ast_nodes import (
    ParsedQuery, SelectQuery, ShortcutQuery, EntityRef, AttributeRef,
    FilterCondition, AggregateFunction, SortClause, QueryNode, QueryVisitor,
    AggregationType, FilterOperator, SortDirection,
    create_entity_ref, create_attribute_ref, create_filter, create_aggregate, create_sort
)
from .parser import HebrewQueryParser, MatchedTerm
from .sql_generator import SQLGenerator, SQLiteGenerator, SQLServerGenerator, MySQLGenerator, create_sql_generator

__all__ = [
    # AST Nodes
    'ParsedQuery', 'SelectQuery', 'ShortcutQuery', 'EntityRef', 'AttributeRef',
    'FilterCondition', 'AggregateFunction', 'SortClause', 'QueryNode', 'QueryVisitor',
    'AggregationType', 'FilterOperator', 'SortDirection', 'MatchedTerm',
    
    # Helper functions
    'create_entity_ref', 'create_attribute_ref', 'create_filter', 'create_aggregate', 'create_sort',
    
    # Parser
    'HebrewQueryParser',
    
    # SQL Generators
    'SQLGenerator', 'SQLiteGenerator', 'SQLServerGenerator', 'MySQLGenerator', 'create_sql_generator'
]
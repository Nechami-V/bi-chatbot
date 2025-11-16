"""
Abstract Syntax Tree (AST) for Query Representation
Represents parsed queries in a structured format before SQL generation
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from enum import Enum

class AggregationType(Enum):
    """Supported aggregation functions"""
    COUNT = "COUNT"
    SUM = "SUM"
    AVG = "AVG"
    MAX = "MAX" 
    MIN = "MIN"

class FilterOperator(Enum):
    """Filter comparison operators"""
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    LIKE = "LIKE"
    IN = "IN"
    NOT_IN = "NOT IN"

class SortDirection(Enum):
    """Sorting directions"""
    ASC = "ASC"
    DESC = "DESC"

@dataclass
class EntityRef:
    """Reference to an entity in the ontology"""
    name: str                    # Logical entity name (e.g., "customer")
    alias: Optional[str] = None  # Optional alias for joins

@dataclass
class AttributeRef:
    """Reference to an entity attribute"""
    entity: str                  # Entity name
    attribute: str               # Attribute name
    alias: Optional[str] = None  # Optional alias

@dataclass
class FilterCondition:
    """Filter condition in WHERE clause"""
    attribute: AttributeRef
    operator: FilterOperator
    value: Any
    negate: bool = False

@dataclass
class SortClause:
    """Sort specification"""
    attribute: AttributeRef
    direction: SortDirection = SortDirection.ASC

@dataclass
class AggregateFunction:
    """Aggregation function specification"""
    function: AggregationType
    attribute: Optional[AttributeRef] = None  # None for COUNT(*)
    alias: Optional[str] = None

class QueryNode(ABC):
    """Base class for all AST nodes"""
    
    @abstractmethod
    def accept(self, visitor):
        """Accept a visitor for traversal"""
        pass

@dataclass
class SelectQuery(QueryNode):
    """Main SELECT query node"""
    entities: List[EntityRef]                           # FROM clause entities
    attributes: List[AttributeRef] = None               # SELECT attributes (None = SELECT *)
    aggregates: List[AggregateFunction] = None          # Aggregate functions
    filters: List[FilterCondition] = None               # WHERE conditions
    sorts: List[SortClause] = None                      # ORDER BY clauses
    limit: Optional[int] = None                         # LIMIT clause
    group_by: List[AttributeRef] = None                 # GROUP BY attributes
    
    def __post_init__(self):
        """Initialize empty lists"""
        if self.attributes is None:
            self.attributes = []
        if self.aggregates is None:
            self.aggregates = []
        if self.filters is None:
            self.filters = []
        if self.sorts is None:
            self.sorts = []
        if self.group_by is None:
            self.group_by = []
    
    def accept(self, visitor):
        """Accept visitor for traversal"""
        return visitor.visit_select_query(self)

@dataclass
class ShortcutQuery(QueryNode):
    """Predefined shortcut query"""
    shortcut_name: str
    sql: str
    description: str
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
    
    def accept(self, visitor):
        return visitor.visit_shortcut_query(self)

@dataclass
class ParsedQuery:
    """Complete parsed query with metadata"""
    original_text: str                          # Original Hebrew query
    query_node: QueryNode                       # AST representation  
    matched_terms: List[str] = None             # Hebrew terms that matched
    confidence: float = 1.0                     # Confidence score
    intent: Optional[str] = None                # Detected intent
    
    def __post_init__(self):
        if self.matched_terms is None:
            self.matched_terms = []

class QueryVisitor(ABC):
    """Visitor pattern for AST traversal"""
    
    @abstractmethod
    def visit_select_query(self, query: SelectQuery):
        """Visit a SELECT query node"""
        pass
    
    @abstractmethod  
    def visit_shortcut_query(self, query: ShortcutQuery):
        """Visit a shortcut query node"""
        pass

# Helper functions for AST construction
def create_entity_ref(name: str, alias: str = None) -> EntityRef:
    """Create an entity reference"""
    return EntityRef(name=name, alias=alias)

def create_attribute_ref(entity: str, attribute: str, alias: str = None) -> AttributeRef:
    """Create an attribute reference"""
    return AttributeRef(entity=entity, attribute=attribute, alias=alias)

def create_filter(entity: str, attribute: str, operator: FilterOperator, value: Any, negate: bool = False) -> FilterCondition:
    """Create a filter condition"""
    attr_ref = create_attribute_ref(entity, attribute)
    return FilterCondition(attribute=attr_ref, operator=operator, value=value, negate=negate)

def create_aggregate(function: AggregationType, entity: str = None, attribute: str = None, alias: str = None) -> AggregateFunction:
    """Create an aggregate function"""
    attr_ref = create_attribute_ref(entity, attribute) if entity and attribute else None
    return AggregateFunction(function=function, attribute=attr_ref, alias=alias)

def create_sort(entity: str, attribute: str, direction: SortDirection = SortDirection.ASC) -> SortClause:
    """Create a sort clause"""
    attr_ref = create_attribute_ref(entity, attribute)
    return SortClause(attribute=attr_ref, direction=direction)
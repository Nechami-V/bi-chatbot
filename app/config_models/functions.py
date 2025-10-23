"""
Pydantic models for functions and aggregations configuration
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Literal
from enum import Enum

class AggregationType(str, Enum):
    """Supported SQL aggregation functions"""
    COUNT = "COUNT"
    SUM = "SUM" 
    AVG = "AVG"
    MAX = "MAX"
    MIN = "MIN"
    DISTINCT = "DISTINCT"

class ReturnType(str, Enum):
    """Return types for functions"""
    INTEGER = "integer"
    DECIMAL = "decimal"
    STRING = "string"
    DYNAMIC = "dynamic"

class Aggregation(BaseModel):
    """Aggregation function definition"""
    sql_function: AggregationType = Field(..., description="SQL function name")
    hebrew_names: List[str] = Field(..., min_items=1, description="Hebrew names for this aggregation")
    return_type: ReturnType = Field(..., description="Expected return type")
    description: str = Field(..., description="Function description")
    applicable_types: Optional[List[str]] = Field(default=None, description="Data types this function can be applied to")
    
    @validator('hebrew_names')
    def validate_hebrew_names(cls, v):
        if not all(isinstance(name, str) and name.strip() for name in v):
            raise ValueError("All Hebrew names must be non-empty strings")
        return v

class QueryIntent(str, Enum):
    """Supported query intents"""
    COUNT = "count"
    SELECT = "select"
    AGGREGATE = "aggregate"
    FILTER = "filter"
    SORT = "sort"

class QueryPattern(BaseModel):
    """Query pattern for intent recognition"""
    pattern: str = Field(..., description="Pattern template with placeholders")
    intent: QueryIntent = Field(..., description="Query intent")
    sql_template: Optional[str] = Field(default=None, description="SQL template")
    aggregation: Optional[str] = Field(default=None, description="Default aggregation function")
    filter_type: Optional[str] = Field(default=None, description="Filter operation type")

class DateFunction(BaseModel):
    """Date and time function definition"""
    sql_function: str = Field(..., description="SQL function expression")
    hebrew_names: List[str] = Field(..., min_items=1, description="Hebrew names")
    description: Optional[str] = Field(default=None, description="Function description")

class Functions(BaseModel):
    """Complete functions configuration"""
    aggregations: Dict[str, Aggregation] = Field(..., description="Available aggregation functions")
    query_patterns: Dict[str, QueryPattern] = Field(..., description="Query pattern templates")
    date_functions: Optional[Dict[str, DateFunction]] = Field(default={}, description="Date/time functions")
    
    @validator('aggregations')
    def validate_aggregations(cls, v):
        if not v:
            raise ValueError("At least one aggregation must be defined")
        return v
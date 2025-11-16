"""
Pydantic models for client-specific mappings and business rules
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional

class CustomEntityTerms(BaseModel):
    """Additional Hebrew terms for an entity"""
    additional_names: List[str] = Field(..., min_items=1, description="Additional Hebrew names")
    
    @validator('additional_names')
    def validate_names(cls, v):
        if not all(isinstance(name, str) and name.strip() for name in v):
            raise ValueError("All names must be non-empty strings")
        return v

class CustomAttributeTerms(BaseModel):
    """Additional Hebrew terms for an attribute"""
    additional_names: List[str] = Field(..., min_items=1, description="Additional Hebrew names")
    
    @validator('additional_names') 
    def validate_names(cls, v):
        if not all(isinstance(name, str) and name.strip() for name in v):
            raise ValueError("All names must be non-empty strings")
        return v

class CustomTerms(BaseModel):
    """Client-specific Hebrew terminology"""
    entities: Optional[Dict[str, CustomEntityTerms]] = Field(default={}, description="Additional entity names")
    attributes: Optional[Dict[str, CustomAttributeTerms]] = Field(default={}, description="Additional attribute names")

class BusinessRules(BaseModel):
    """Client-specific business rules and defaults"""
    default_filters: Optional[Dict[str, Dict[str, str]]] = Field(default={}, description="Default WHERE clauses per entity")
    default_ordering: Optional[Dict[str, str]] = Field(default={}, description="Default ORDER BY per entity")
    max_results_override: Optional[int] = Field(default=None, ge=1, le=10000, description="Override max results")

class QueryShortcut(BaseModel):
    """Predefined query shortcut"""
    sql: str = Field(..., description="SQL query")
    description: str = Field(..., description="Human-readable description")
    parameters: Optional[Dict[str, str]] = Field(default={}, description="Query parameters")
    
    @validator('sql')
    def validate_sql(cls, v):
        if not v or not v.strip():
            raise ValueError("SQL cannot be empty")
        return v.strip()

class Mappings(BaseModel):
    """Complete client-specific mappings configuration"""
    client_id: str = Field(..., description="Client identifier")
    custom_terms: Optional[CustomTerms] = Field(default_factory=CustomTerms, description="Additional Hebrew terms")
    business_rules: Optional[BusinessRules] = Field(default_factory=BusinessRules, description="Business rules")
    shortcuts: Optional[Dict[str, QueryShortcut]] = Field(default={}, description="Query shortcuts")
    
    @validator('client_id')
    def validate_client_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Client ID cannot be empty")
        return v.strip()
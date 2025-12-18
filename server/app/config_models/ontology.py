"""
Pydantic models for YAML configuration validation
Validates the structure and content of all YAML config files
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional
from enum import Enum

class AttributeType(str, Enum):
    """Valid data types for entity attributes"""
    INTEGER = "integer"
    STRING = "string"  
    DECIMAL = "decimal"
    DATE = "date"
    BOOLEAN = "boolean"

class RelationshipType(str, Enum):
    """Valid relationship types between entities"""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"

class Attribute(BaseModel):
    """Entity attribute definition"""
    type: AttributeType
    hebrew_names: List[str] = Field(..., min_items=1, description="Hebrew names for this attribute")
    primary_key: bool = False
    foreign_key: Optional[str] = None
    nullable: bool = True
    description: Optional[str] = None
    
    @validator('hebrew_names')
    def validate_hebrew_names(cls, v):
        """Ensure all Hebrew names are non-empty strings"""
        if not all(isinstance(name, str) and name.strip() for name in v):
            raise ValueError("All Hebrew names must be non-empty strings")
        return v

class Entity(BaseModel):
    """Business entity definition"""
    display_name: str = Field(..., description="English display name")
    hebrew_names: List[str] = Field(..., min_items=1, description="Hebrew names for this entity")
    description: str = Field(..., description="Entity description")
    attributes: Dict[str, Attribute] = Field(..., description="Entity attributes")
    
    @validator('attributes')
    def validate_attributes_and_primary_key(cls, v):
        """Ensure at least one attribute and exactly one primary key exists"""
        if len(v) < 1:
            raise ValueError("Each entity must have at least one attribute")
        primary_keys = [attr for attr in v.values() if attr.primary_key]
        if len(primary_keys) != 1:
            raise ValueError("Each entity must have exactly one primary key")
        return v

class Relationship(BaseModel):
    """Relationship between entities"""
    from_entity: str = Field(..., alias="from", description="Source entity")
    to_entity: str = Field(..., alias="to", description="Target entity")
    type: RelationshipType = Field(..., description="Relationship type")
    foreign_key: str = Field(..., description="Foreign key attribute name")

class Ontology(BaseModel):
    """Complete business ontology configuration"""
    entities: Dict[str, Entity] = Field(..., description="Business entities")
    relationships: Optional[Dict[str, Relationship]] = Field(default={}, description="Entity relationships")
    
    @validator('entities')
    def validate_entities(cls, v):
        """Ensure at least one entity exists"""
        if len(v) < 1:
            raise ValueError("Ontology must have at least one entity")
        return v
    
    class Config:
        populate_by_name = True
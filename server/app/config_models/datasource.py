"""
Pydantic models for datasource configuration  
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional
from enum import Enum

class DatabaseType(str, Enum):
    """Supported database types"""
    SQLITE = "sqlite"
    MYSQL = "mysql"  
    POSTGRESQL = "postgresql"
    SQLSERVER = "sqlserver"

class ColumnMapping(BaseModel):
    """Mapping between logical attribute and physical column"""
    physical_column: str = Field(..., description="Physical database column name")
    data_type: Optional[str] = Field(default=None, description="Database-specific data type")
    nullable: bool = Field(default=True, description="Whether column can be NULL")
    
class TableMapping(BaseModel):
    """Mapping between logical entity and physical table"""
    physical_table: str = Field(..., description="Physical database table name")
    columns: Dict[str, str] = Field(..., description="Column mappings (logical -> physical)")
    where_clause: Optional[str] = Field(default=None, description="Default WHERE clause for this table")
    
    @validator('columns')
    def validate_columns(cls, v):
        if not v or len(v) < 1:
            raise ValueError("Table must have at least one column mapping")
        return v

class DatabaseSettings(BaseModel):
    """Database connection and query settings"""
    max_results: int = Field(default=1000, ge=1, le=10000, description="Maximum query results")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Query timeout in seconds")  
    enable_explain: bool = Field(default=True, description="Enable SQL EXPLAIN functionality")
    connection_pool_size: Optional[int] = Field(default=5, ge=1, le=20, description="Connection pool size")

class Datasource(BaseModel):
    """Complete datasource configuration"""
    client_id: str = Field(..., description="Client identifier")
    database_type: DatabaseType = Field(..., description="Database type")
    connection_string: str = Field(..., description="Database connection string")
    table_mappings: Dict[str, TableMapping] = Field(..., description="Entity to table mappings")
    database_settings: DatabaseSettings = Field(default_factory=DatabaseSettings, description="Database settings")
    
    @validator('table_mappings')
    def validate_table_mappings(cls, v):
        """Ensure at least one table mapping exists"""
        if len(v) < 1:
            raise ValueError("Datasource must have at least one table mapping")
        return v
    
    @validator('client_id')
    def validate_client_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Client ID cannot be empty")
        return v.strip()
    
    @validator('connection_string')  
    def validate_connection_string(cls, v):
        if not v or not v.strip():
            raise ValueError("Connection string cannot be empty")
        return v.strip()
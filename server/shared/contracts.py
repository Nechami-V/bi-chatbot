from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class VisualizationPayload(BaseModel):
    chart_type: Optional[str] = None
    title: Optional[str] = None
    label_field: Optional[str] = None
    value_field: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    values: List[Any] = Field(default_factory=list)
    value_prefix: Optional[str] = None
    value_suffix: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    question: Optional[str] = None
    sql: Optional[str] = None
    data: List[Dict[str, Any]] = Field(default_factory=list)
    columns: List[str] = Field(default_factory=list)
    row_count: Optional[int] = None
    preview_count: int = 0
    has_more: bool = False
    error: Optional[str] = None
    visualization: Optional[VisualizationPayload] = None
    total_time_ms: Optional[float] = None
    timings_ms: Dict[str, float] = Field(default_factory=dict)

class NL2SQLResponse(BaseModel):
    sql: str
    dialect: str = "mssql"
    warnings: List[str] = Field(default_factory=list)
    error: Optional[str] = None

class ExecuteResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: Optional[int] = None
    preview_count: int = 0
    has_more: bool = False
    error: Optional[str] = None

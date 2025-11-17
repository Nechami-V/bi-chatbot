from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    sql: Optional[str] = None
    error: Optional[str] = None

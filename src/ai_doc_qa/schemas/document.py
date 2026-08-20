from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class DocumentResponse(BaseModel):
    id: int
    name: str
    status: Literal["processing", "completed", "failed"]
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentListResponse(BaseModel):
    total_count: int
    documents: list[DocumentResponse]

class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=2000)
    document_id: int | None = Field(default=None, ge=1)
    limit: int = Field(default=5, ge=1, le=20)

class SearchHit(BaseModel):
    score: float
    text: str | None
    document_id: int | None
    chunk_id: int | str
    
class SearchResponse(BaseModel):
    question: str
    results: list[SearchHit]

class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=2000)

class AskResponse(BaseModel):
    answer: str
    sources: list[SearchHit]
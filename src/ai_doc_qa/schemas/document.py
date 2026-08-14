import enum
from datetime import datetime
from typing import Literal
from pydantic import BaseModel

from ai_doc_qa.db.models import document

class DocumentResponse(BaseModel):
    id: int
    name: str
    status: Literal["processing", "completed", "failed"]
    created_at: datetime
    updated_at: datetime

class DocumentListResponse(BaseModel):
    total_count: int
    documents: list[DocumentResponse]

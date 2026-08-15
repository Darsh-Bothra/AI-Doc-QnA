from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict

class DocumentResponse(BaseModel):
    id: int
    name: str
    status: Literal["processing", "completed", "failed"]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentListResponse(BaseModel):
    total_count: int
    documents: list[DocumentResponse]

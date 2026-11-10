from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateCollectionDto(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class CollectionFileDto(BaseModel):
    id: str
    filename: str
    status: str
    chunk_count: int = 0
    error: Optional[str] = None
    content_type: Optional[str] = None
    size: int = 0
    created_at: Optional[datetime] = None


class CollectionDto(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    file_count: int = 0

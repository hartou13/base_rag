from typing import Optional

from pydantic import BaseModel, Field


class ChatRequestDto(BaseModel):
    session_id: str
    collection_id: str
    question: str = Field(min_length=1)


class ChatSourceDto(BaseModel):
    """Shape of each item in the `sources` SSE event and of a stored message's sources."""
    id: str
    file_id: Optional[str] = None
    filename: Optional[str] = None
    text: str
    distance: Optional[float] = None  # not stored, so absent on reloaded messages

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.chat.dto.chat_dto import ChatSourceDto


class CreateSessionDto(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)


class UpdateSessionDto(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class SessionDto(BaseModel):
    id: str
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MessageDto(BaseModel):
    id: str
    role: str
    content: str
    created_at: Optional[datetime] = None
    sources: Optional[List[ChatSourceDto]] = None


class SessionDetailDto(SessionDto):
    messages: List[MessageDto] = []

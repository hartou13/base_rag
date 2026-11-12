import uuid

from sqlalchemy import JSON, Column, ForeignKey, String, Text, text
from sqlalchemy.dialects.mysql import DATETIME

from src.database.mysql_connector import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    role = Column(String(20), nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    # Chroma chunk ids ("{file_id}:{chunk_index}") the answer was built from, and the collection holding them.
    source_ids = Column(JSON, nullable=True)
    source_collection_id = Column(String(36), nullable=True)
    created_at = Column(DATETIME(fsp=6), index=True, server_default=text("CURRENT_TIMESTAMP(6)"))

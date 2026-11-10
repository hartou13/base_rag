import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, text

from src.database.mysql_connector import Base


class CollectionFile(Base):
    __tablename__ = "collection_files"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="CASCADE"), index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    size = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    status = Column(String(20), default="indexing")  # indexing | ready | failed
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

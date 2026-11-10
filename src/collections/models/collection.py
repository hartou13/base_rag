import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, text

from src.database.mysql_connector import Base


class Collection(Base):
    __tablename__ = "collections"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

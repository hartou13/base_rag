import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from src.database.mysql_connector import Base
from datetime import datetime

class UserActiveToken(Base):
    __tablename__ = "users_active_token"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    token = Column(String(255), index=True)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)    
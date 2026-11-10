from datetime import datetime
import uuid
from sqlalchemy import Boolean, Column, DateTime, Integer, String, text
from src.database.mysql_connector import Base

class User(Base):
    __tablename__ = "users"
    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )    
    first_name = Column(String(255), index=True)
    last_name = Column(String(255), index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)
    language = Column(String(3), default="fr")
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))



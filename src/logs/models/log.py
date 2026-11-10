import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum, Text
from src.database.mysql_connector import Base
from sqlalchemy.orm import relationship
from datetime import datetime

from enum import Enum as PyEnum

class ActionType(PyEnum):
    REGISTER = "register"
    LOGIN = "login"
    LOGOUT = "logout"
    API_KEY_REGENERATION = "api_key_regeneration"
    
class LogTypes(PyEnum):
    INFO = 'INFO'
    WARN = 'WARN'
    ERR = 'ERR'



class Log(Base):
    __tablename__ = "logs"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), index=True)
    type = Column(Enum(LogTypes), index=True)
    action = Column(Enum(ActionType), index=True)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)    
    # user = relationship("User", back_populates="logs")

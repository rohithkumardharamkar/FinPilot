from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from src.core.database import Base

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False)
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

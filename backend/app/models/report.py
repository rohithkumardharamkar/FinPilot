from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from src.core.database import Base

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content_markdown = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

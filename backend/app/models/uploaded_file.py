from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from src.core.database import Base

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from src.core.database import Base

class FraudAlert(Base):
    __tablename__ = "fraud_alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(50), nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
    severity = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow)
    risk_score = Column(Float, nullable=False)

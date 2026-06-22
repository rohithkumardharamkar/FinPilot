from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text
from src.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    transaction_id = Column(String(50), primary_key=True)
    date = Column(String(20), nullable=False)  # YYYY-MM-DD
    merchant = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    account_type = Column(String(50), nullable=False)  # UPI, Credit Card, Bank Account, Wallets
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    is_subscription = Column(Boolean, default=False)


class Income(Base):
    __tablename__ = "income"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    salary = Column(Float, nullable=False, default=0.0)
    other_income = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Budget(Base):
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), unique=True, nullable=False)
    budget_amount = Column(Float, nullable=False)


class SavingsGoal(Base):
    __tablename__ = "savings_goals"
    
    goal_name = Column(String(100), primary_key=True)
    target_amount = Column(Float, nullable=False)
    current_saved = Column(Float, nullable=False, default=0.0)
    target_date = Column(String(20), nullable=False)  # YYYY-MM-DD


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant = Column(String(100), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    frequency = Column(String(50), default="Monthly")
    is_used = Column(Boolean, default=True)


class Account(Base):
    __tablename__ = "accounts"
    
    account_name = Column(String(100), primary_key=True)
    account_type = Column(String(50), nullable=False)  # Bank Account, Credit Card, UPI, Wallets
    balance = Column(Float, nullable=False, default=0.0)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String(100), nullable=False)
    agent = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)  # PASSED, FAILED, BLOCKED, etc.
    details = Column(Text, nullable=True)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    
    chunk_id = Column(Integer, primary_key=True, autoincrement=True)
    document_name = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)  # JSON string
    embedding = Column(Text, nullable=False)     # JSON representation of vector


class SummaryMemory(Base):
    __tablename__ = "summary_memories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default="user_1", nullable=False)
    profile_id = Column(Integer, default=1)
    summary_text = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReflectionMemory(Base):
    __tablename__ = "reflections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default="user_1", nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    issue = Column(Text, nullable=False)
    lesson_learned = Column(Text, nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default="user_1", nullable=False)
    thread_id = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)  # human, ai
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class EntityMemory(Base):
    __tablename__ = "entity_memories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default="user_1", nullable=False)
    entity_name = Column(String(100), nullable=False)
    entity_value = Column(Text, nullable=False)
    confidence_score = Column(Float, default=1.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EpisodicMemory(Base):
    __tablename__ = "episodic_memories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default="user_1", nullable=False)
    memory = Column(Text, nullable=False)
    importance = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Goal(Base):
    __tablename__ = "goals"
    
    goal_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default="user_1", nullable=False)
    goal_description = Column(Text, nullable=False)
    target_value = Column(Float, nullable=False)
    target_date = Column(String(50), nullable=False)
    status = Column(String(50), default="active")  # active, completed, cancelled
    progress = Column(Float, default=0.0)


class Preference(Base):
    __tablename__ = "preferences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default="user_1", nullable=False)
    preference_type = Column(String(100), nullable=False)  # e.g., "report_frequency", "alert_type"
    preference_value = Column(Text, nullable=False)


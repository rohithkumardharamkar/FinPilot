from typing import Dict, Any, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import Transaction, EpisodicMemory

async def get_transaction_timeline(db: AsyncSession, user_id: str = "user_1") -> List[Dict[str, Any]]:
    """
    Get a chronologically sorted list of all transactions from SQLite.
    """
    result = await db.execute(select(Transaction).order_by(Transaction.date))
    txns = result.scalars().all()
    
    events = []
    for t in txns:
        events.append({
            "event_type": "Transaction",
            "timestamp": t.date,
            "description": f"Paid ₹{t.amount} at {t.merchant} using {t.account_type} (Description: {t.description or 'N/A'}, Category: {t.category or 'Unassigned'})",
            "meta": {
                "transaction_id": t.transaction_id,
                "merchant": t.merchant,
                "amount": t.amount,
                "account_type": t.account_type,
                "category": t.category,
                "is_subscription": t.is_subscription
            }
        })
    return events

async def get_recent_transactions(limit: int, db: AsyncSession, user_id: str = "user_1") -> List[Dict[str, Any]]:
    """Retrieve the most recent transactions."""
    result = await db.execute(select(Transaction).order_by(desc(Transaction.date)).limit(limit))
    txns = result.scalars().all()
    
    events = []
    for t in txns:
        events.append({
            "transaction_id": t.transaction_id,
            "date": t.date,
            "merchant": t.merchant,
            "amount": t.amount,
            "account_type": t.account_type,
            "category": t.category
        })
    return events

async def get_episodic_memories(user_id: str, db: AsyncSession) -> List[str]:
    """Retrieve episodic memories for a user."""
    stmt = select(EpisodicMemory).where(EpisodicMemory.user_id == user_id).order_by(desc(EpisodicMemory.created_at))
    result = await db.execute(stmt)
    memories = result.scalars().all()
    return [m.memory for m in memories]

async def save_episodic_memory(user_id: str, memory_text: str, importance: float, db: AsyncSession):
    """Save an episodic memory for a user."""
    memory_obj = EpisodicMemory(user_id=user_id, memory=memory_text, importance=importance)
    db.add(memory_obj)
    await db.flush()


from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.db_models import Account, Budget, SavingsGoal, Subscription, EntityMemory

async def get_financial_profile(db: AsyncSession, user_id: str = "user_1") -> Dict[str, Any]:
    """Retrieve financial account details and current balances from SQLite."""
    result = await db.execute(select(Account))
    accounts = result.scalars().all()
    
    total_balance = 0.0
    account_list = []
    for acc in accounts:
        account_list.append({
            "name": acc.account_name,
            "type": acc.account_type,
            "balance": acc.balance
        })
        total_balance += acc.balance
        
    return {
        "accounts": account_list,
        "total_net_worth": total_balance
    }

async def get_budget_limits(db: AsyncSession, user_id: str = "user_1") -> List[Dict[str, Any]]:
    """Retrieve all budget categories and limits from SQLite."""
    result = await db.execute(select(Budget))
    budgets = result.scalars().all()
    return [{"category": b.category, "limit": b.budget_amount} for b in budgets]

async def get_savings_goals(db: AsyncSession, user_id: str = "user_1") -> List[Dict[str, Any]]:
    """Retrieve savings goals from SQLite."""
    result = await db.execute(select(SavingsGoal))
    goals = result.scalars().all()
    return [{
        "goal_name": g.goal_name,
        "target_amount": g.target_amount,
        "current_saved": g.current_saved,
        "target_date": g.target_date,
        "progress_percentage": round((g.current_saved / g.target_amount) * 100.0, 2) if g.target_amount > 0 else 0.0
    } for g in goals]

async def get_active_subscriptions(db: AsyncSession, user_id: str = "user_1") -> List[Dict[str, Any]]:
    """Retrieve subscriptions list from SQLite."""
    result = await db.execute(select(Subscription))
    subs = result.scalars().all()
    return [{
        "merchant": s.merchant,
        "amount": s.amount,
        "frequency": s.frequency,
        "is_used": s.is_used
    } for s in subs]

async def get_user_entities(user_id: str, db: AsyncSession) -> Dict[str, str]:
    """Retrieve user-specific key-value entities."""
    stmt = select(EntityMemory).where(EntityMemory.user_id == user_id)
    result = await db.execute(stmt)
    entities = result.scalars().all()
    return {e.entity_name: e.entity_value for e in entities}

async def save_user_entity(user_id: str, entity_name: str, entity_value: str, confidence_score: float, db: AsyncSession):
    """Save or update a user-specific entity."""
    stmt = select(EntityMemory).where(EntityMemory.user_id == user_id, EntityMemory.entity_name == entity_name)
    res = await db.execute(stmt)
    entity = res.scalar_one_or_none()
    if entity:
        entity.entity_value = entity_value
        entity.confidence_score = confidence_score
    else:
        entity = EntityMemory(user_id=user_id, entity_name=entity_name, entity_value=entity_value, confidence_score=confidence_score)
        db.add(entity)
    await db.flush()


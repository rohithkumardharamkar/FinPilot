from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.db_models import Goal

async def get_goals(user_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
    """Retrieve all goals for a user."""
    stmt = select(Goal).where(Goal.user_id == user_id)
    res = await db.execute(stmt)
    goals = res.scalars().all()
    return [
        {
            "goal_id": g.goal_id,
            "goal_description": g.goal_description,
            "target_value": g.target_value,
            "target_date": g.target_date,
            "status": g.status,
            "progress": g.progress
        }
        for g in goals
    ]

async def save_goal(
    user_id: str,
    goal_description: str,
    target_value: float,
    target_date: str,
    status: str = "active",
    progress: float = 0.0,
    db: AsyncSession = None
) -> Dict[str, Any]:
    """Add a new goal for a user."""
    goal = Goal(
        user_id=user_id,
        goal_description=goal_description,
        target_value=target_value,
        target_date=target_date,
        status=status,
        progress=progress
    )
    db.add(goal)
    await db.flush()
    return {
        "goal_id": goal.goal_id,
        "goal_description": goal.goal_description,
        "target_value": goal.target_value,
        "target_date": goal.target_date,
        "status": goal.status,
        "progress": goal.progress
    }

async def update_goal(
    user_id: str,
    goal_id: int,
    updates: Dict[str, Any],
    db: AsyncSession
) -> Optional[Dict[str, Any]]:
    """Update goal attributes (e.g. progress, status)."""
    stmt = select(Goal).where(Goal.user_id == user_id, Goal.goal_id == goal_id)
    res = await db.execute(stmt)
    goal = res.scalar_one_or_none()
    if not goal:
        return None
        
    for k, v in updates.items():
        if hasattr(goal, k):
            setattr(goal, k, v)
            
    await db.flush()
    return {
        "goal_id": goal.goal_id,
        "goal_description": goal.goal_description,
        "target_value": goal.target_value,
        "target_date": goal.target_date,
        "status": goal.status,
        "progress": goal.progress
    }

async def delete_goal(user_id: str, goal_id: int, db: AsyncSession) -> bool:
    """Delete a user goal."""
    stmt = select(Goal).where(Goal.user_id == user_id, Goal.goal_id == goal_id)
    res = await db.execute(stmt)
    goal = res.scalar_one_or_none()
    if not goal:
        return False
    await db.delete(goal)
    await db.flush()
    return True

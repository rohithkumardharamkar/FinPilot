from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.core.database import get_db
from api.auth import get_current_user
from src.models.db_models import Subscription

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

@router.get("")
async def list_subscriptions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Subscription)
    res = await db.execute(stmt)
    subs = res.scalars().all()
    
    # We map to frontend expectation
    return [
        {
            "id": s.id,
            "merchant": s.merchant,
            "monthly_cost": s.amount,
            "annual_cost": s.amount * 12,
            "savings_opportunity": s.amount * 12 if not s.is_used else 0.0,
            "confidence_score": 0.95 if s.is_used else 0.70,
            "is_unused": not s.is_used,
            "duplicate_service": False # Can set based on business logic if duplicate
        }
        for s in subs
    ]

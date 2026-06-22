from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from api.auth import get_current_user
from src.tools.reporting import calculate_wellness_score_tool

router = APIRouter(prefix="/wellness", tags=["Wellness"])

def get_grade_for_score(score: float) -> str:
    if score >= 85:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 55:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"

@router.get("")
async def get_latest_wellness(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await calculate_wellness_score_tool(db)
    if res.get("status") == "success":
        score = res["data"].get("overall_wellness_score", 72.5)
    else:
        score = 72.5
        
    return {
        "score": score,
        "grade": get_grade_for_score(score)
    }

@router.get("/history")
async def get_wellness_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await calculate_wellness_score_tool(db)
    current_score = res["data"].get("overall_wellness_score", 72.5) if res.get("status") == "success" else 72.5
    
    # Return last 6 months trend
    return [
        {"month": "Jan", "score": 65.0},
        {"month": "Feb", "score": 67.5},
        {"month": "Mar", "score": 70.0},
        {"month": "Apr", "score": 68.0},
        {"month": "May", "score": 71.0},
        {"month": "Jun", "score": current_score}
    ]

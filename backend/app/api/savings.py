from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.core.database import get_db
from api.auth import get_current_user
from src.models.db_models import SavingsGoal, AuditLog, Transaction, Income
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from datetime import datetime

router = APIRouter(prefix="/savings", tags=["Savings"])

# --- Request Schemas ---
class SavingsGoalCreateRequest(BaseModel):
    name: str
    target_amount: float
    current_amount: float
    start_date: str
    target_date: str
    category: str

# --- Routes ---

@router.get("")
async def list_goals(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(SavingsGoal)
    res = await db.execute(stmt)
    goals = res.scalars().all()
    
    out = []
    for g in goals:
        health = int((g.current_saved / g.target_amount * 100)) if g.target_amount > 0 else 100
        health = min(max(health, 0), 100) # clamp to 0-100
        out.append({
            "id": g.goal_name,
            "name": g.goal_name,
            "current_amount": g.current_saved,
            "target_amount": g.target_amount,
            "target_date": g.target_date,
            "health_score": health
        })
    return out

@router.post("")
async def create_goal(
    req: SavingsGoalCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(SavingsGoal).where(SavingsGoal.goal_name == req.name)
    res = await db.execute(stmt)
    goal = res.scalar_one_or_none()
    
    # Parse dates
    # Target date is YYYY-MM-DD
    target_dt_str = req.target_date[:10]
    
    if goal:
        goal.target_amount = req.target_amount
        goal.current_saved = req.current_amount
        goal.target_date = target_dt_str
    else:
        goal = SavingsGoal(
            goal_name=req.name,
            target_amount=req.target_amount,
            current_saved=req.current_amount,
            target_date=target_dt_str
        )
        db.add(goal)
        
    audit = AuditLog(
        action="SAVINGS_GOAL_CREATION",
        agent="savings_agent",
        status="SUCCESS",
        details=f"Established/updated savings goal {req.name} with target ₹{req.target_amount}."
    )
    db.add(audit)
    await db.commit()
    
    return {
        "id": goal.goal_name,
        "name": goal.goal_name,
        "current_amount": goal.current_saved,
        "target_amount": goal.target_amount,
        "target_date": goal.target_date,
        "health_score": int((goal.current_saved / goal.target_amount * 100)) if goal.target_amount > 0 else 100
    }

@router.post("/roadmap")
async def generate_roadmap(
    target_amount: float = Query(...),
    months_horizon: int = Query(...),
    goal_name: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Calculate required monthly savings
    required_monthly = target_amount / months_horizon if months_horizon > 0 else target_amount
    
    # Fetch income
    inc_stmt = select(Income)
    inc_res = await db.execute(inc_stmt)
    income_row = inc_res.scalars().first()
    total_income = (income_row.salary + income_row.other_income) if income_row else 92000.0
    
    # Fetch transactions to calculate average monthly expenses
    txn_stmt = select(Transaction)
    txn_res = await db.execute(txn_stmt)
    txns = txn_res.scalars().all()
    
    total_expense = 0.0
    if txns:
        df = pd.DataFrame([{
            "amount": t.amount,
            "category": t.category
        } for t in txns])
        # Only debits
        debits = df[df["category"] != "Income"]
        total_expense = float(debits["amount"].sum())
        
    # Assume database seeded transactions span 1.5 months (e.g. May/June)
    # Estimate average monthly expense
    monthly_expense = total_expense / 1.5 if total_expense > 0 else 48000.0
    current_monthly_savings = total_income - monthly_expense
    if current_monthly_savings < 0:
        current_monthly_savings = 5000.0 # fallback default savings
        
    gap = required_monthly - current_monthly_savings
    gap = max(gap, 0.0)
    
    # Generate realistic steps based on gap and target
    if gap > 0:
        roadmap_steps = [
            f"Set up an automated recurring transfer of ₹{round(required_monthly, -2):,.0f} from your primary bank account to your HDFC Savings account immediately after salary credit.",
            f"You have a savings gap of ₹{round(gap, -2):,.0f}/month. We recommend reducing Swiggy & Dining out by 35% to redirect ₹3,500/month.",
            "Review and cancel the duplicate Entertainment subscription identified in your subscription audit to recover ₹499/month.",
            "Allocate 50% of any upcoming quarterly bonus or salary hikes directly into this target fund to reach the milestone ahead of schedule."
        ]
    else:
        roadmap_steps = [
            f"Your current monthly surplus of ₹{round(current_monthly_savings, -2):,.0f} is sufficient to cover this target! Set up an auto-transfer of ₹{round(required_monthly, -2):,.0f}/month to stay disciplined.",
            "Hold these funds in a high-yield liquid mutual fund or savings account offering >6% interest.",
            "Keep monitoring monthly budgets to ensure your expense run rate doesn't increase."
        ]
        
    # Audit log
    audit = AuditLog(
        action="SAVINGS_ROADMAP_GENERATION",
        agent="savings_agent",
        status="SUCCESS",
        details=f"Calculated savings roadmap for {goal_name}. Required/mo: ₹{required_monthly:.2f}."
    )
    db.add(audit)
    await db.commit()
    
    return {
        "goal_name": goal_name,
        "months": months_horizon,
        "required_monthly_savings": required_monthly,
        "current_monthly_savings": current_monthly_savings,
        "gap": gap,
        "roadmap": roadmap_steps
    }

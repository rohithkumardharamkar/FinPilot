from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.core.database import get_db
from api.auth import get_current_user
from src.models.db_models import Budget, Transaction, AuditLog
from pydantic import BaseModel
import pandas as pd

router = APIRouter(prefix="/budgets", tags=["Budgets"])

# --- Request Schemas ---
class BudgetCreateRequest(BaseModel):
    category: str
    amount: float

# --- Routes ---

@router.get("")
async def list_budgets(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch budgets
    stmt = select(Budget)
    res = await db.execute(stmt)
    budgets = res.scalars().all()
    
    # Fetch latest month transactions to compute spent
    txn_stmt = select(Transaction)
    txn_res = await db.execute(txn_stmt)
    txns = txn_res.scalars().all()
    
    spent_map = {}
    if txns:
        df = pd.DataFrame([{
            "date": pd.to_datetime(t.date),
            "category": t.category,
            "amount": t.amount
        } for t in txns])
        
        # Get latest month in transactions
        latest_date = df["date"].max()
        current_month_df = df[(df["date"].dt.month == latest_date.month) & (df["date"].dt.year == latest_date.year)]
        
        spent_map = current_month_df.groupby("category")["amount"].sum().to_dict()
        
    return [
        {
            "id": b.id,
            "category": b.category,
            "amount": b.budget_amount,
            "spent": float(spent_map.get(b.category, 0.0))
        }
        for b in budgets
    ]

@router.post("")
async def create_or_update_budget(
    req: BudgetCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Budget).where(Budget.category.ilike(req.category))
    res = await db.execute(stmt)
    budget = res.scalar_one_or_none()
    
    if budget:
        old_amount = budget.budget_amount
        budget.budget_amount = req.amount
        action_msg = f"Updated budget limit for {req.category} from ₹{old_amount} to ₹{req.amount}."
    else:
        budget = Budget(category=req.category, budget_amount=req.amount)
        db.add(budget)
        action_msg = f"Created new budget limit for {req.category} set to ₹{req.amount}."
        
    audit = AuditLog(
        action="BUDGET_MODIFICATION",
        agent="budget_advisor",
        status="SUCCESS",
        details=action_msg
    )
    db.add(audit)
    await db.commit()
    
    return {
        "id": budget.id,
        "category": budget.category,
        "amount": budget.budget_amount,
        "message": "Budget successfully saved."
    }

@router.post("/generate")
async def generate_ai_budgets(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch all transactions to see categories and average spending
    stmt = select(Transaction)
    res = await db.execute(stmt)
    txns = res.scalars().all()
    
    if not txns:
        raise HTTPException(status_code=400, detail="Cannot generate budgets. No transaction history found.")
        
    df = pd.DataFrame([{
        "category": t.category,
        "amount": t.amount
    } for t in txns])
    
    # Calculate average spending per category
    cat_spend = df.groupby("category")["amount"].mean().to_dict()
    
    generated_count = 0
    for category, avg_spend in cat_spend.items():
        if category in ["Income", "Unassigned"]:
            continue
            
        # Target limit = 1.25x of average transaction value times an assumed 4 transactions per month,
        # or simply set to a realistic rounded limit like 1.5x of total category spend / 3 (months)
        # Let's calculate total spend in category and divide by distinct months
        # To make it simple: set budget to total spend in that category + 10%, capped at reasonable values
        total_cat_spend = df[df["category"] == category]["amount"].sum()
        suggested_limit = float(round(total_cat_spend * 1.15, -2))
        if suggested_limit < 1000:
            suggested_limit = 1000.0
            
        # Check if budget already exists
        b_stmt = select(Budget).where(Budget.category.ilike(category))
        b_res = await db.execute(b_stmt)
        budget = b_res.scalar_one_or_none()
        
        if not budget:
            budget = Budget(category=category, budget_amount=suggested_limit)
            db.add(budget)
            generated_count += 1
            
    if generated_count > 0:
        audit = AuditLog(
            action="AI_BUDGET_GENERATION",
            agent="budget_agent",
            status="SUCCESS",
            details=f"Automatically generated {generated_count} category budgets based on spend trends."
        )
        db.add(audit)
        await db.commit()
        
    return {
        "message": f"AI budget optimization complete. Generated {generated_count} new category budgets.",
        "generated_count": generated_count
    }

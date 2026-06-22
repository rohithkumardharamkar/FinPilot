from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from src.core.database import get_db
from api.auth import get_current_user
from src.models.db_models import Transaction, Account, Income
from services.file_service import FileService
import pandas as pd
from datetime import datetime

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("")
async def list_transactions(
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Transaction).order_by(desc(Transaction.date)).limit(limit)
    res = await db.execute(stmt)
    txns = res.scalars().all()
    
    return [
        {
            "id": t.transaction_id,
            "date": t.date,
            "merchant": t.merchant,
            "amount": t.amount,
            "account_type": t.account_type,
            "description": t.description,
            "category": t.category,
            "confidence_score": 1.0,
            "is_recurring": t.is_subscription,
            "transaction_type": "credit" if t.category == "Income" else "debit"
        }
        for t in txns
    ]

@router.get("/accounts")
async def list_accounts(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Account)
    res = await db.execute(stmt)
    accounts = res.scalars().all()
    
    return [
        {
            "id": a.account_name,
            "account_name": a.account_name,
            "account_type": a.account_type,
            "balance": a.balance
        }
        for a in accounts
    ]

@router.post("/upload")
async def upload_statement(
    file: UploadFile = File(...),
    account_name: str = Form(...),
    account_type: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    file_svc = FileService(db)
    content = await file.read()
    try:
        res = await file_svc.ingest_statement(file.filename, content, account_name, account_type)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_analytics(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch all transactions
    stmt = select(Transaction)
    res = await db.execute(stmt)
    txns = res.scalars().all()
    
    # Fetch income
    inc_stmt = select(Income)
    inc_res = await db.execute(inc_stmt)
    income_row = inc_res.scalars().first()
    total_income = (income_row.salary + income_row.other_income) if income_row else 92000.0
    
    if not txns:
        return {
            "overview": {
                "total_income": total_income,
                "total_expense": 0.0,
                "savings_rate": 100.0,
                "net_savings": total_income
            },
            "category_breakdown": [],
            "monthly_trend": [],
            "merchant_ranking": [],
            "weekend_weekday": []
        }
        
    df = pd.DataFrame([{
        "date": pd.to_datetime(t.date),
        "merchant": t.merchant,
        "amount": t.amount,
        "category": t.category,
        "type": "credit" if t.category == "Income" else "debit"
    } for t in txns])
    
    df["is_weekend"] = df["date"].dt.dayofweek.isin([5, 6])
    debits = df[df["type"] == "debit"]
    total_expense = float(debits["amount"].sum())
    net_savings = total_income - total_expense
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0.0
    
    overview = {
        "total_income": total_income,
        "total_expense": total_expense,
        "savings_rate": round(savings_rate, 2),
        "net_savings": net_savings
    }
    
    # Category breakdown
    cat_grp = debits.groupby("category")["amount"].sum().reset_index()
    category_breakdown = [
        {"name": row["category"], "value": float(row["amount"])}
        for _, row in cat_grp.iterrows()
    ]
    
    # Monthly Trend (last 6 months, matching the chart format)
    df["month_str"] = df["date"].dt.strftime("%b")
    df["year_month"] = df["date"].dt.to_period("M")
    
    monthly_grp = df.groupby(["year_month", "month_str", "type"])["amount"].sum().unstack(fill_value=0.0).reset_index()
    monthly_trend = []
    
    # If we have monthly data, sort and format
    monthly_grp = monthly_grp.sort_values("year_month")
    for _, row in monthly_grp.iterrows():
        # Use database income or fall back
        inc_val = float(row.get("credit", 0.0))
        if inc_val == 0.0:
            inc_val = total_income
        monthly_trend.append({
            "month": row["month_str"],
            "Income": inc_val,
            "Expense": float(row.get("debit", 0.0))
        })
        
    # If less than 2 months, fallback to mock trend for display
    if len(monthly_trend) < 2:
        monthly_trend = [
            { "month": "Jan", "Income": 80000, "Expense": 45000 },
            { "month": "Feb", "Income": 82000, "Expense": 48000 },
            { "month": "Mar", "Income": 80000, "Expense": 52000 },
            { "month": "Apr", "Income": 85000, "Expense": 42000 },
            { "month": "May", "Income": 85000, "Expense": 49000 },
            { "month": "Jun", "Income": total_income, "Expense": total_expense }
        ]
        
    # Merchant ranking
    merch_grp = debits.groupby("merchant").agg(
        count=("amount", "count"),
        total=("amount", "sum")
    ).reset_index()
    merch_grp = merch_grp.sort_values(by="total", ascending=False).head(5)
    merchant_ranking = [
        {
            "merchant": row["merchant"],
            "count": int(row["count"]),
            "total": float(row["total"])
        }
        for _, row in merch_grp.iterrows()
    ]
    
    # Weekend weekday split
    weekend_grp = debits.groupby("is_weekend")["amount"].sum().to_dict()
    
    weekend_val = float(weekend_grp.get(True, 0.0))
    weekday_val = float(weekend_grp.get(False, 0.0))
    total_split = weekend_val + weekday_val
    
    weekend_pct = (weekend_val / total_split * 100) if total_split > 0 else 32.0
    weekday_pct = (weekday_val / total_split * 100) if total_split > 0 else 68.0
    
    weekend_weekday = [
        {"name": "Weekdays", "value": round(weekday_pct, 1)},
        {"name": "Weekends", "value": round(weekend_pct, 1)}
    ]
    
    return {
        "overview": overview,
        "category_breakdown": category_breakdown,
        "monthly_trend": monthly_trend,
        "merchant_ranking": merchant_ranking,
        "weekend_weekday": weekend_weekday
    }

from typing import Dict, Any, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import Transaction, Income, Budget, SavingsGoal, Account, Subscription, AuditLog
import pandas as pd
from src.tools.analysis import analyze_spending_patterns_tool, detect_anomalies_tool

async def track_budget_variance_tool(db: AsyncSession) -> Dict[str, Any]:
    """
    Budget Variance Tracker: Compares actual category expenses against budgets.
    Formula: Variance = Actual - Budget.
    """
    try:
        # Get budgets
        b_stmt = select(Budget)
        b_res = await db.execute(b_stmt)
        budgets = b_res.scalars().all()
        
        # Get current month transactions
        t_stmt = select(Transaction)
        t_res = await db.execute(t_stmt)
        txns = t_res.scalars().all()
        
        if not txns:
            return {
                "status": "success",
                "data": {"variances": []},
                "metadata": {}
            }
            
        df = pd.DataFrame([{
            "category": t.category,
            "amount": t.amount
        } for t in txns])
        
        actual_spend = df.groupby("category")["amount"].sum().to_dict()
        
        variances = []
        for b in budgets:
            category = b.category
            limit = b.budget_amount
            actual = actual_spend.get(category, 0.0)
            variance = actual - limit
            pct_used = (actual / limit * 100) if limit > 0 else 0.0
            
            variances.append({
                "category": category,
                "budget_limit": limit,
                "actual_spend": actual,
                "variance": variance,
                "percentage_used": round(pct_used, 2),
                "status": "OVERSPENT" if variance > 0 else "UNDER_BUDGET"
            })
            
        return {
            "status": "success",
            "data": {"variances": variances},
            "metadata": {"count": len(variances)}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }

async def track_savings_goals_tool(db: AsyncSession) -> Dict[str, Any]:
    """
    Savings Goal Tracker: Calculates savings goal completeness and ETA.
    Formula: Completion = Current Saved / Target Amount.
    """
    try:
        stmt = select(SavingsGoal)
        result = await db.execute(stmt)
        goals = result.scalars().all()
        
        # Assume standard average monthly savings is ₹5,000 (or calculated from income - expenses)
        avg_monthly_savings = 5000.0
        
        data_list = []
        for g in goals:
            remaining = g.target_amount - g.current_saved
            completion_pct = (g.current_saved / g.target_amount * 100.0) if g.target_amount > 0 else 100.0
            eta_months = (remaining / avg_monthly_savings) if avg_monthly_savings > 0 else float('inf')
            
            data_list.append({
                "goal_name": g.goal_name,
                "target_amount": g.target_amount,
                "current_saved": g.current_saved,
                "remaining_amount": remaining,
                "completion_percentage": round(completion_pct, 2),
                "eta_months": round(eta_months, 1) if eta_months != float('inf') else "N/A",
                "target_date": g.target_date
            })
            
        return {
            "status": "success",
            "data": {"goals": data_list},
            "metadata": {"count": len(data_list)}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }

async def calculate_wellness_score_tool(db: AsyncSession) -> Dict[str, Any]:
    """
    Financial Wellness Scorer: Computes score out of 100 based on weighted metrics.
    Weights: Savings Rate (30%), Budget Adherence (25%), Debt Ratio (25%), Emergency Fund (20%).
    """
    try:
        # Get total income
        inc_stmt = select(Income)
        inc_res = await db.execute(inc_stmt)
        income_row = inc_res.scalars().first()
        total_income = (income_row.salary + income_row.other_income) if income_row else 55000.0
        
        # Get total spend
        txn_stmt = select(Transaction)
        txn_res = await db.execute(txn_stmt)
        txns = txn_res.scalars().all()
        total_spend = sum(t.amount for t in txns if t.date.startswith("2026-06")) # June 2026 current month
        # Fallback if no current month
        if total_spend == 0:
            total_spend = sum(t.amount for t in txns if "2026-06" in t.date)
        if total_spend == 0:
            total_spend = sum(t.amount for t in txns)
            
        # Get accounts for Debt & Emergency Fund
        acc_stmt = select(Account)
        acc_res = await db.execute(acc_stmt)
        accounts = acc_res.scalars().all()
        
        # 1. Savings Rate Score (Weight: 30%)
        net_savings = total_income - total_spend
        savings_rate = (net_savings / total_income) if total_income > 0 else 0.0
        
        if savings_rate >= 0.20:
            savings_score = 100
        elif savings_rate >= 0.10:
            savings_score = 80
        elif savings_rate >= 0.0:
            savings_score = 50
        else:
            savings_score = 10  # Negative savings rate
            
        # 2. Budget Adherence Score (Weight: 25%)
        # Get variance
        var_res = await track_budget_variance_tool(db)
        variances = var_res.get("data", {}).get("variances", [])
        
        if not variances:
            budget_score = 100
        else:
            overspent_count = sum(1 for v in variances if v["status"] == "OVERSPENT")
            total_budgets = len(variances)
            budget_score = 100 - (overspent_count / total_budgets * 100) if total_budgets > 0 else 100
            
        # 3. Debt Ratio Score (Weight: 25%)
        credit_card_debt = 0.0
        for acc in accounts:
            if acc.account_type == "Credit Card" and acc.balance < 0:
                credit_card_debt += abs(acc.balance)
                
        debt_ratio = credit_card_debt / total_income if total_income > 0 else 0.0
        if debt_ratio <= 0.10:
            debt_score = 100
        elif debt_ratio <= 0.30:
            debt_score = 80
        elif debt_ratio <= 0.50:
            debt_score = 50
        else:
            debt_score = 20
            
        # 4. Emergency Fund Score (Weight: 20%)
        liquid_assets = 0.0
        for acc in accounts:
            if acc.account_type in ["Bank Account", "UPI", "Wallets"] and acc.balance > 0:
                liquid_assets += acc.balance
                
        # Assume average monthly expenses is ₹25,000
        avg_monthly_expenses = 25000.0
        months_covered = liquid_assets / avg_monthly_expenses if avg_monthly_expenses > 0 else 0.0
        
        if months_covered >= 6.0:
            emergency_score = 100
        elif months_covered >= 3.0:
            emergency_score = 80
        elif months_covered >= 1.0:
            emergency_score = 50
        else:
            emergency_score = 20
            
        # Weighted Overall Score
        overall_score = (savings_score * 0.30) + (budget_score * 0.25) + (debt_score * 0.25) + (emergency_score * 0.20)
        
        return {
            "status": "success",
            "data": {
                "overall_wellness_score": round(overall_score, 1),
                "savings_rate_score": savings_score,
                "savings_rate_actual": round(savings_rate * 100, 2),
                "budget_adherence_score": budget_score,
                "debt_ratio_score": debt_score,
                "debt_ratio_actual": round(debt_ratio, 2),
                "emergency_fund_score": emergency_score,
                "months_covered_actual": round(months_covered, 2),
                "liquid_savings": liquid_assets
            },
            "metadata": {"engine": "financial_scorer"}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }

async def generate_financial_report_tool(db: AsyncSession) -> Dict[str, Any]:
    """
    Personalized Report Generator: Compiles wellness score, budget variances, 
    spending patterns, and anomalies into a structured report.
    """
    try:
        # Load all components
        wellness = await calculate_wellness_score_tool(db)
        w_data = wellness.get("data", {})
        
        variances = await track_budget_variance_tool(db)
        v_list = variances.get("data", {}).get("variances", [])
        
        patterns = await analyze_spending_patterns_tool(db)
        p_data = patterns.get("data", {})
        
        anom_res = await detect_anomalies_tool(db)
        anoms = anom_res.get("data", {}).get("anomalies", [])
        
        goals = await track_savings_goals_tool(db)
        g_list = goals.get("data", {}).get("goals", [])
        
        # Build Markdown Report
        report = []
        report.append("# MONTHLY PERSONAL FINANCIAL HEALTH REPORT")
        report.append(f"### Overall Financial Wellness Score: **{w_data.get('overall_wellness_score', 'N/A')}/100**")
        report.append("---")
        
        # Score factors
        report.append("## Financial Health Breakdown")
        report.append(f"- **Savings Rate Score**: {w_data.get('savings_rate_score')}/100 (Actual: {w_data.get('savings_rate_actual')}% of income)")
        report.append(f"- **Budget Adherence Score**: {w_data.get('budget_adherence_score')}/100")
        report.append(f"- **Debt-to-Income Score**: {w_data.get('debt_ratio_score')}/100 (Debt Ratio: {w_data.get('debt_ratio_actual')})")
        report.append(f"- **Emergency Fund Score**: {w_data.get('emergency_fund_score')}/100 (Covering: {w_data.get('months_covered_actual')} months of expenses)")
        report.append("")
        
        # Budget variances
        report.append("## Budget Variance Status")
        if v_list:
            report.append("| Category | Limit | Actual Spend | Variance | Status |")
            report.append("| --- | --- | --- | --- | --- |")
            for v in v_list:
                report.append(f"| {v['category']} | ₹{v['budget_limit']} | ₹{v['actual_spend']} | ₹{v['variance']} | {v['status']} |")
        else:
            report.append("No budgets tracked.")
        report.append("")
        
        # Spending patterns
        report.append("## Spending Patterns & Trends")
        report.append(f"- **Average Daily Spend**: ₹{p_data.get('average_daily_spend', 0.0)}")
        report.append(f"- **Weekend Spending**: {p_data.get('weekend_spend_percentage', 0.0)}% of total layout")
        report.append(f"- **Peak Food Hours**: {p_data.get('dining_hour_peak', 'N/A')}")
        report.append("")
        
        # Savings progress
        report.append("## Savings Goals Progress")
        if g_list:
            for g in g_list:
                report.append(f"- **{g['goal_name']}**: ₹{g['current_saved']} saved out of ₹{g['target_amount']} (**{g['completion_percentage']}%** completed). Est. ETA: {g['eta_months']} months.")
        else:
            report.append("No savings goals defined.")
        report.append("")
        
        # Anomalies
        report.append("## Fraud & Anomaly Alerts")
        high_risk = [a for a in anoms if a["risk_score"] >= 60]
        if high_risk:
            for h in high_risk:
                report.append(f"- **WARNING (Risk Score: {h['risk_score']})**: {h['merchant']} transaction of ₹{h['amount']} on {h['date']}.")
                for r in h["reasons"]:
                    report.append(f"  - *Reason*: {r}")
        else:
            report.append("No suspicious transactions or fraud alerts found.")
        report.append("")
        
        # Actionable recommendations
        report.append("## Personalized Actionable Recommendations")
        recs = []
        if w_data.get('savings_rate_actual', 0.0) < 15.0:
            recs.append("Increase your monthly savings rate to at least 15% by cutting discretionary shopping layouts.")
        if any(v['status'] == "OVERSPENT" for v in v_list):
            overspent = [v['category'] for v in v_list if v['status'] == "OVERSPENT"]
            recs.append(f"You have overspent in category: **{', '.join(overspent)}**. Please reduce swiggy/dining orders immediately.")
        # Check Spotify unused subscription
        async with db.begin_nested() if db.in_transaction() else db as transaction:
            sub_res = await db.execute(select(Subscription).where((Subscription.merchant.ilike("spotify")) & (Subscription.is_used == True)))
            spotify_sub = sub_res.scalar_one_or_none()
            if spotify_sub:
                recs.append("Cancel unused Spotify monthly subscription (saving ₹119/month).")
                
        if w_data.get('months_covered_actual', 0.0) < 3.0:
            recs.append("Your emergency fund covers less than 3 months of layout. Allocate ₹3,000/month from salary to HDFC Bank savings account.")
            
        if not recs:
            recs.append("Your financial health looks excellent. Maintain your current budget structures!")
            
        for i, r in enumerate(recs, 1):
            report.append(f"{i}. {r}")
            
        final_markdown = "\n".join(report)
        
        return {
            "status": "success",
            "data": {
                "report_content": final_markdown,
                "wellness_score": w_data.get('overall_wellness_score')
            },
            "metadata": {"reporter": "financial_report_generator"}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }

async def audit_report_tool(limit: int, db: AsyncSession) -> Dict[str, Any]:
    """Retrieves recent audit logs and summaries of guardrail event logs."""
    try:
        stmt = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
        res = await db.execute(stmt)
        logs = res.scalars().all()
        
        logs_data = []
        blocked_count = 0
        passed_count = 0
        
        for l in logs:
            if l.status == "BLOCKED":
                blocked_count += 1
            else:
                passed_count += 1
                
            logs_data.append({
                "log_id": l.log_id,
                "timestamp": l.timestamp.isoformat(),
                "action": l.action,
                "agent": l.agent,
                "status": l.status,
                "details": l.details
            })
            
        summary = f"Audit Report Summary: Checked last {len(logs)} security event logs. Blocked: {blocked_count}, Passed: {passed_count}."
        
        return {
            "status": "success",
            "data": {
                "summary": summary,
                "recent_logs": logs_data,
                "blocked_count": blocked_count,
                "passed_count": passed_count
            },
            "metadata": {"reporter": "audit_logs_compiler"}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }

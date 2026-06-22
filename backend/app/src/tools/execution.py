from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import Subscription, Budget, SavingsGoal, Account, AuditLog

async def cancel_subscription_tool(merchant: str, db: AsyncSession) -> Dict[str, Any]:
    """Cancels a subscription (marks it as unused)."""
    try:
        stmt = select(Subscription).where(Subscription.merchant.ilike(merchant))
        res = await db.execute(stmt)
        sub = res.scalar_one_or_none()
        if not sub:
            return {
                "status": "failed",
                "data": {},
                "metadata": {"error": f"Subscription for '{merchant}' not found."}
            }
            
        old_status = sub.is_used
        sub.is_used = False
        
        # Log to Audit
        log = AuditLog(
            action="CANCEL_SUBSCRIPTION",
            agent="execution_agent",
            status="SUCCESS",
            details=f"Cancelled subscription for {sub.merchant}. Prior usage: {old_status} -> New: False"
        )
        db.add(log)
        await db.commit()
        
        return {
            "status": "success",
            "data": {
                "merchant": sub.merchant,
                "amount": sub.amount,
                "is_used": False
            },
            "metadata": {"action": "cancel_subscription"}
        }
    except Exception as e:
        await db.rollback()
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }

async def update_budget_tool(category: str, new_limit: float, db: AsyncSession) -> Dict[str, Any]:
    """Updates the budget limit for a specific category."""
    try:
        stmt = select(Budget).where(Budget.category.ilike(category))
        res = await db.execute(stmt)
        budget = res.scalar_one_or_none()
        
        action_type = "UPDATE_BUDGET"
        if not budget:
            # Create a new budget limit
            budget = Budget(category=category, budget_amount=new_limit)
            db.add(budget)
            action_type = "CREATE_BUDGET"
            old_limit = 0.0
        else:
            old_limit = budget.budget_amount
            budget.budget_amount = new_limit
            
        await db.flush()
        
        # Log to Audit
        log = AuditLog(
            action=action_type,
            agent="execution_agent",
            status="SUCCESS",
            details=f"Set budget limit for {category} to ₹{new_limit}. Old limit: ₹{old_limit}"
        )
        db.add(log)
        await db.commit()
        
        return {
            "status": "success",
            "data": {
                "category": category,
                "budget_limit": new_limit
            },
            "metadata": {"action": "update_budget"}
        }
    except Exception as e:
        await db.rollback()
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }

async def transfer_savings_tool(goal_name: str, amount_to_transfer: float, db: AsyncSession) -> Dict[str, Any]:
    """Transfers funds into a savings goal (deducts from GPay/HDFC Bank and adds to Goal)."""
    try:
        # Check savings goal
        goal_stmt = select(SavingsGoal).where(SavingsGoal.goal_name.ilike(goal_name))
        goal_res = await db.execute(goal_stmt)
        goal = goal_res.scalar_one_or_none()
        if not goal:
            return {
                "status": "failed",
                "data": {},
                "metadata": {"error": f"Savings goal '{goal_name}' not found."}
            }
            
        # Deduct from HDFC Bank/GPay (find the first account with enough balance)
        acc_stmt = select(Account).where(Account.account_name == "HDFC Bank")
        acc_res = await db.execute(acc_stmt)
        account = acc_res.scalar_one_or_none()
        
        if not account or account.balance < amount_to_transfer:
            # Fall back to GPay
            acc_stmt2 = select(Account).where(Account.account_name == "GPay")
            acc_res2 = await db.execute(acc_stmt2)
            account = acc_res2.scalar_one_or_none()
            
        if not account or account.balance < amount_to_transfer:
            return {
                "status": "failed",
                "data": {},
                "metadata": {"error": "Insufficient funds in HDFC Bank and GPay to complete the transfer."}
            }
            
        # Modify account balance and goal saved
        old_balance = account.balance
        account.balance -= amount_to_transfer
        
        old_saved = goal.current_saved
        goal.current_saved += amount_to_transfer
        
        # Log to Audit
        log = AuditLog(
            action="TRANSFER_SAVINGS",
            agent="execution_agent",
            status="SUCCESS",
            details=f"Transferred ₹{amount_to_transfer} from {account.account_name} to savings goal '{goal.goal_name}'"
        )
        db.add(log)
        await db.commit()
        
        return {
            "status": "success",
            "data": {
                "goal_name": goal.goal_name,
                "amount_transferred": amount_to_transfer,
                "current_saved": goal.current_saved,
                "source_account": account.account_name,
                "account_new_balance": account.balance
            },
            "metadata": {"action": "transfer_savings"}
        }
    except Exception as e:
        await db.rollback()
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }

async def send_email_report_tool(recipient_email: str, subject: str, body: str) -> Dict[str, Any]:
    """Sends an email with the specified subject and body."""
    from src.core.email import send_email
    success = send_email(subject, body, recipient_email)
    if success:
        return {
            "status": "success",
            "data": {
                "recipient": recipient_email,
                "subject": subject
            },
            "metadata": {"action": "send_email_report"}
        }
    else:
        return {
            "status": "failed",
            "data": {},
            "metadata": {"error": "Failed to send email. Check SMTP logs and credentials."}
        }


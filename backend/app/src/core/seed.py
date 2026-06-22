import csv
import os
import datetime
from sqlalchemy.future import select
from src.core.database import SessionLocal
from src.models.db_models import (
    Transaction, Income, Budget, SavingsGoal, Account, Subscription,
    SummaryMemory, ReflectionMemory, Goal, Preference, EntityMemory, EpisodicMemory
)

async def seed_data():
    async with SessionLocal() as db:
        print("Checking and seeding missing financial dummy data from CSV files...")
        data_dir = "dummy_data"
        
        # 1. Seed Accounts
        accounts_file = os.path.join(data_dir, "accounts.csv")
        if os.path.exists(accounts_file):
            with open(accounts_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row["account_name"]
                    exist_res = await db.execute(select(Account).where(Account.account_name == name))
                    if exist_res.scalar_one_or_none() is not None:
                        continue
                    account = Account(
                        account_name=name,
                        account_type=row["account_type"],
                        balance=float(row["balance"])
                    )
                    db.add(account)
            await db.flush()

        # 2. Seed Budgets
        budget_file = os.path.join(data_dir, "budget.csv")
        if os.path.exists(budget_file):
            with open(budget_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    category = row["category"]
                    exist_res = await db.execute(select(Budget).where(Budget.category == category))
                    if exist_res.scalar_one_or_none() is not None:
                        continue
                    budget = Budget(
                        category=category,
                        budget_amount=float(row["budget_amount"])
                    )
                    db.add(budget)
            await db.flush()

        # 3. Seed Income
        income_file = os.path.join(data_dir, "income.csv")
        if os.path.exists(income_file):
            with open(income_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # check if any income row exists
                    exist_res = await db.execute(select(Income))
                    if exist_res.scalars().first() is not None:
                        continue
                    income = Income(
                        salary=float(row["salary"]),
                        other_income=float(row["other_income"])
                    )
                    db.add(income)
            await db.flush()

        # 4. Seed Savings Goals
        goals_file = os.path.join(data_dir, "goals.csv")
        if os.path.exists(goals_file):
            with open(goals_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row["goal_name"]
                    exist_res = await db.execute(select(SavingsGoal).where(SavingsGoal.goal_name == name))
                    if exist_res.scalar_one_or_none() is not None:
                        continue
                    goal = SavingsGoal(
                        goal_name=name,
                        target_amount=float(row["target_amount"]),
                        current_saved=float(row["current_saved"]),
                        target_date=row["target_date"]
                    )
                    db.add(goal)
            await db.flush()

        # 5. Seed Transactions
        transactions_file = os.path.join(data_dir, "transactions.csv")
        if os.path.exists(transactions_file):
            with open(transactions_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    txn_id = row["transaction_id"]
                    exist_res = await db.execute(select(Transaction).where(Transaction.transaction_id == txn_id))
                    if exist_res.scalar_one_or_none() is not None:
                        continue
                    
                    is_sub = False
                    merchant_lower = row["merchant"].lower()
                    if merchant_lower in ["netflix", "spotify", "chatgpt"]:
                        is_sub = True
                        
                    txn = Transaction(
                        transaction_id=txn_id,
                        date=row["date"],
                        merchant=row["merchant"],
                        amount=float(row["amount"]),
                        account_type=row["account_type"],
                        description=row.get("description", ""),
                        category=row.get("category", ""),
                        is_subscription=is_sub
                    )
                    db.add(txn)
            await db.flush()

        # 6. Seed Subscriptions
        default_subs = [
            {"merchant": "Netflix", "amount": 649.0, "frequency": "Monthly", "is_used": True},
            {"merchant": "Spotify", "amount": 119.0, "frequency": "Monthly", "is_used": False},
            {"merchant": "ChatGPT", "amount": 1700.0, "frequency": "Monthly", "is_used": True}
        ]
        for sub_data in default_subs:
            exist_res = await db.execute(select(Subscription).where(Subscription.merchant == sub_data["merchant"]))
            if exist_res.scalar_one_or_none() is None:
                sub = Subscription(
                    merchant=sub_data["merchant"],
                    amount=sub_data["amount"],
                    frequency=sub_data["frequency"],
                    is_used=sub_data["is_used"]
                )
                db.add(sub)

        # 7. Seed Summary Memory
        exist_res = await db.execute(select(SummaryMemory).where(SummaryMemory.user_id == "user_1"))
        if exist_res.scalar_one_or_none() is None:
            default_summary = (
                "User has an active monthly salary of ₹50,000 and ₹5,000 in other income. "
                "Main savings goal is Europe Trip (₹3,00,000 target, ₹1,20,000 saved). "
                "Budgets are set for Food (₹5,000), Transport (₹3,000), Shopping (₹5,000) and Entertainment (₹2,000). "
                "Subscribed to Netflix (₹649/m), Spotify (₹119/m, unused), and ChatGPT (₹1700/m)."
            )
            db.add(SummaryMemory(user_id="user_1", profile_id=1, summary_text=default_summary))

        # 8. Seed Reflections
        exist_res = await db.execute(select(ReflectionMemory).where(ReflectionMemory.user_id == "user_1"))
        if exist_res.scalars().first() is None:
            reflections = [
                ReflectionMemory(
                    user_id="user_1",
                    timestamp=datetime.datetime.utcnow(),
                    issue="Detected overspending in Food category.",
                    lesson_learned="Recommend reducing dining out and Swiggy orders by at least ₹2,000 to improve budget adherence."
                ),
                ReflectionMemory(
                    user_id="user_1",
                    timestamp=datetime.datetime.utcnow(),
                    issue="Detected unused subscription for Spotify.",
                    lesson_learned="Recommend cancelling Spotify immediately to save ₹119/month."
                )
            ]
            for r in reflections:
                db.add(r)

        # 9. Seed Goals
        exist_goals = await db.execute(select(Goal).where(Goal.user_id == "user_1"))
        if exist_goals.scalars().first() is None:
            goals_data = [
                Goal(user_id="user_1", goal_description="Europe Trip savings goal", target_value=300000.0, target_date="2027-12-31", status="active", progress=40.0),
                Goal(user_id="user_1", goal_description="Buy a new MacBook Pro", target_value=200000.0, target_date="2026-12-31", status="active", progress=25.0)
            ]
            for g in goals_data:
                db.add(g)

        # 10. Seed Preferences
        exist_pref = await db.execute(select(Preference).where(Preference.user_id == "user_1"))
        if exist_pref.scalars().first() is None:
            preferences_data = [
                Preference(user_id="user_1", preference_type="report_frequency", preference_value="Monthly"),
                Preference(user_id="user_1", preference_type="email_recipient", preference_value="user@example.com"),
                Preference(user_id="user_1", preference_type="alert_threshold", preference_value="80%")
            ]
            for p in preferences_data:
                db.add(p)

        # 11. Seed Entity Memory
        exist_entity = await db.execute(select(EntityMemory).where(EntityMemory.user_id == "user_1"))
        if exist_entity.scalars().first() is None:
            entities_data = [
                EntityMemory(user_id="user_1", entity_name="name", entity_value="John Doe", confidence_score=1.0),
                EntityMemory(user_id="user_1", entity_name="email", entity_value="user@example.com", confidence_score=1.0),
                EntityMemory(user_id="user_1", entity_name="preferred_bank", entity_value="HDFC Bank", confidence_score=0.9)
            ]
            for e in entities_data:
                db.add(e)

        # 12. Seed Episodic Memory
        exist_episodic = await db.execute(select(EpisodicMemory).where(EpisodicMemory.user_id == "user_1"))
        if exist_episodic.scalars().first() is None:
            episodic_data = [
                EpisodicMemory(user_id="user_1", memory="User requested details about reducing dining expenses.", importance=0.8),
                EpisodicMemory(user_id="user_1", memory="User was advised to cancel unused Spotify subscription to save money.", importance=0.9)
            ]
            for ep in episodic_data:
                db.add(ep)

        await db.commit()
        print("Financial database seeded and entries populated successfully.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_data())

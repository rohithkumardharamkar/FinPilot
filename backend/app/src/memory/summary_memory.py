from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.db_models import SummaryMemory, ChatMessage
from src.core.config import settings

async def retrieve_summary(user_id: str, db: AsyncSession) -> str:
    """Retrieve compressed financial summary from SQLite. Returns a generated summary if none exists."""
    result = await db.execute(select(SummaryMemory).where(SummaryMemory.user_id == user_id))
    sm = result.scalar_one_or_none()
    if sm:
        return sm.summary_text
        
    generated = (
        "User is active with default income (₹55,000/month). "
        "Savings goals are Europe Trip (₹3,00,000). "
        "Budget limits are set for Food, Transport, Shopping, and Entertainment."
    )
    
    sm = SummaryMemory(user_id=user_id, summary_text=generated)
    db.add(sm)
    await db.commit()
    return generated

async def generate_summary(user_id: str, info: Dict[str, Any], db: AsyncSession) -> str:
    """Explicitly generate and save a formatted summary of financial history in SQLite."""
    summary_text = (
        f"Income: Salary ₹{info.get('salary', 0.0)}, Other ₹{info.get('other_income', 0.0)}. "
        f"Savings target: ₹{info.get('savings_target', 0.0)}. "
        f"Total budget limits set: ₹{info.get('total_budget', 0.0)}."
    )
    
    result = await db.execute(select(SummaryMemory).where(SummaryMemory.user_id == user_id))
    sm = result.scalar_one_or_none()
    if sm:
        sm.summary_text = summary_text
    else:
        sm = SummaryMemory(user_id=user_id, summary_text=summary_text)
        db.add(sm)
        
    await db.commit()
    return summary_text

async def update_summary(user_id: str, new_summary: str, db: AsyncSession) -> None:
    """Overwrite summary in SQLite."""
    result = await db.execute(select(SummaryMemory).where(SummaryMemory.user_id == user_id))
    sm = result.scalar_one_or_none()
    if sm:
        sm.summary_text = new_summary
    else:
        sm = SummaryMemory(user_id=user_id, summary_text=new_summary)
        db.add(sm)
        
    await db.commit()

async def check_and_trigger_summarization(user_id: str, thread_id: str, db: AsyncSession) -> Optional[str]:
    """Check message history length and dynamically trigger summarization every 20 messages."""
    stmt = select(ChatMessage).where(ChatMessage.user_id == user_id, ChatMessage.thread_id == thread_id)
    res = await db.execute(stmt)
    messages = res.scalars().all()
    count = len(messages)
    
    if count > 0 and count % 20 == 0:
        from src.agents.router import call_model
        from langchain_core.messages import HumanMessage
        
        history_text = "\n".join([f"{msg.role}: {msg.message}" for msg in messages])
        
        prompt = f"""
        Analyze the following conversation history and generate a concise, updated summary of the user's financial profile, goals, preferences, and key discussion points.
        Keep it under 300 words.
        
        Conversation History:
        {history_text}
        """
        
        try:
            llm_res = await call_model([HumanMessage(content=prompt)], settings.FAST_MODEL)
            new_summary = llm_res["text"]
            await update_summary(user_id, new_summary, db)
            return new_summary
        except Exception as e:
            print(f"Error during dynamic summarization: {e}")
            
    return None


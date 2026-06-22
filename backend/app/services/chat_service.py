from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import ChatMessage

class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_thread_history(self, user_id: str, thread_id: str) -> list[dict]:
        stmt = select(ChatMessage).where(
            ChatMessage.user_id == user_id,
            ChatMessage.thread_id == thread_id
        ).order_by(ChatMessage.timestamp)
        res = await self.db.execute(stmt)
        messages = res.scalars().all()
        return [
            {
                "role": m.role,
                "content": m.message,
                "timestamp": m.timestamp.isoformat()
            }
            for m in messages
        ]

    async def get_user_threads(self, user_id: str) -> list[dict]:
        stmt = select(ChatMessage.thread_id).where(ChatMessage.user_id == user_id).distinct()
        res = await self.db.execute(stmt)
        threads = res.scalars().all()
        
        thread_list = []
        for tid in threads:
            title_stmt = select(ChatMessage.message).where(
                ChatMessage.user_id == user_id,
                ChatMessage.thread_id == tid
            ).order_by(ChatMessage.timestamp).limit(1)
            title_res = await self.db.execute(title_stmt)
            first_msg = title_res.scalar_one_or_none() or "Empty Conversation Thread"
            thread_list.append({
                "thread_id": tid,
                "title": first_msg[:60] + "..." if len(first_msg) > 60 else first_msg
            })
        return thread_list

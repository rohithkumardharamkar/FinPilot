from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.conversation import Conversation

class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_session_id(self, session_id: str) -> list[Conversation]:
        stmt = select(Conversation).where(Conversation.session_id == session_id).order_by(Conversation.created_at)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, session_id: str, user_message: str, assistant_response: str) -> Conversation:
        conv = Conversation(
            session_id=session_id,
            user_message=user_message,
            assistant_response=assistant_response
        )
        self.db.add(conv)
        await self.db.flush()
        return conv

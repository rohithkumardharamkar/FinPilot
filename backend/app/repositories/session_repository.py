from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.session import Session

class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_session_id(self, session_id: str) -> Session:
        stmt = select(Session).where(Session.session_id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> list[Session]:
        stmt = select(Session).where(Session.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, session_id: str, user_id: str) -> Session:
        session = Session(session_id=session_id, user_id=user_id)
        self.db.add(session)
        await self.db.flush()
        return session

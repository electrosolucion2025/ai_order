from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db

class DatabaseService:
    def __init__(self):
        self.db_session = None

    async def init_session(self):
        async for session in get_db():
            self.db_session = session
            break

    async def get_session(self) -> AsyncSession:
        if self.db_session is None:
            await self.init_session()
        return self.db_session

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from datetime import datetime
import uuid

from core.config import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

session_local = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with session_local() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

import asyncio

from db.database import engine
from db.base import Base

from db.models.message import Message


async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


asyncio.run(init())

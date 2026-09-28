from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from . import config

engine = create_async_engine(config.DATABASE_URL, pool_size=20, max_overflow=10)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    client_id: Mapped[str] = mapped_column(String(64), index=True)
    sender_id: Mapped[str] = mapped_column(String(16))
    to: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def _ts(x: float) -> datetime:
    return datetime.fromtimestamp(x, tz=timezone.utc)


async def upsert_final(msg: dict, status: str, provider: str | None, finished: float):
    stmt = insert(Message).values(
        id=msg["id"], client_id=msg["client_id"], sender_id=msg["sender_id"],
        to=msg["to"], body=msg["message"], status=status,
        retry_count=msg["retry_count"], provider=provider,
        created_at=_ts(msg["created_at"]), finished_at=_ts(finished),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={"status": status, "retry_count": msg["retry_count"],
              "provider": provider, "finished_at": _ts(finished)},
    )
    async with SessionLocal() as s:
        await s.execute(stmt)
        await s.commit()


async def get_message(msg_id: str):
    async with SessionLocal() as s:
        row = (await s.execute(select(Message).where(Message.id == msg_id))).scalar_one_or_none()
    if not row:
        return None
    return {"status": row.status, "retry_count": row.retry_count, "provider": row.provider}

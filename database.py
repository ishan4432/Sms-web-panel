from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = (
    "postgresql+asyncpg://sms_user:password123@localhost/sms_gateway"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=True
)

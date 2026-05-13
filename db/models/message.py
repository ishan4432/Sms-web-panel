from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime
)

from datetime import datetime

from db.base import Base


class Message(Base):

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)

    to_number = Column(String, nullable=False)

    message = Column(String, nullable=False)

    status = Column(String, default="queued")

    retry_count = Column(Integer, default=0)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    delivered_at = Column(
        DateTime,
        nullable=True
    )

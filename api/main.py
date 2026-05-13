from fastapi import FastAPI, Header
from fastapi.responses import HTMLResponse

from sqlalchemy import select, func, update
from datetime import datetime

import redis
import json

from api.auth import (
    hash_password,
    verify_password,
    create_token
)

from db.session import AsyncSessionLocal
from db.models.message import Message

app = FastAPI()

# ---------------------------------------------------
# REDIS CONNECTION
# ---------------------------------------------------

r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

# ---------------------------------------------------
# API KEY VERIFICATION
# ---------------------------------------------------

def verify_api_key(x_api_key):

    if not x_api_key:
        return False

    return True

# ---------------------------------------------------
# HOME ROUTE
# ---------------------------------------------------

@app.get("/")
def home():

    return {
        "message": "SMS API running"
    }

# ---------------------------------------------------
# RATE LIMIT FUNCTION
# ---------------------------------------------------

def is_rate_limited(phone_number):

    key = f"rate:{phone_number}"

    current = r.get(key)

    if current is None:

        r.set(key, 1, ex=60)

        return False

    elif int(current) < 5:

        r.incr(key)

        return False

    else:

        return True

# ---------------------------------------------------
# SEND SMS
# ---------------------------------------------------

@app.post("/sms/send")
async def send_sms(
    phone_number: str,
    message: str,
    x_api_key: str = Header(None)
):

    # Verify API Key
    if not verify_api_key(x_api_key):

        return {
            "error": "Invalid API Key"
        }

    # Rate Limit Check
    if is_rate_limited(phone_number):

        return {
            "error": "Rate limit exceeded"
        }

    # Save message in PostgreSQL
    async with AsyncSessionLocal() as session:

        msg = Message(
            to_number=phone_number,
            message=message,
            status="queued"
        )

        session.add(msg)

        await session.commit()

        await session.refresh(msg)

    # Push message to Redis queue
    job = {
        "id": msg.id,
        "phone_number": phone_number,
        "message": message,
        "retry_count": 0
    }

    r.lpush(
        "sms_queue",
        json.dumps(job)
    )

    return {
        "message_id": msg.id,
        "status": msg.status
    }

# ---------------------------------------------------
# CHECK SMS STATUS
# ---------------------------------------------------

@app.get("/sms/status/{message_id}")
async def get_status(message_id: int):

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Message).where(
                Message.id == message_id
            )
        )

        msg = result.scalar_one_or_none()

        if not msg:

            return {
                "error": "Message not found"
            }

        return {
            "message_id": msg.id,
            "status": msg.status
        }

# ---------------------------------------------------
# ANALYTICS
# ---------------------------------------------------

@app.get("/analytics")
async def analytics():

    async with AsyncSessionLocal() as session:

        total = await session.scalar(
            select(func.count(Message.id))
        )

        delivered = await session.scalar(
            select(func.count(Message.id))
            .where(Message.status == "delivered")
        )

        failed = await session.scalar(
            select(func.count(Message.id))
            .where(Message.status == "failed")
        )

        queued = await session.scalar(
            select(func.count(Message.id))
            .where(Message.status == "queued")
        )

        processing = await session.scalar(
            select(func.count(Message.id))
            .where(Message.status == "processing")
        )

    queue_size = r.llen("sms_queue")

    retry_queue = r.zcard("sms_retry_queue")

    return {
        "total_messages": total,
        "delivered": delivered,
        "failed": failed,
        "queued": queued,
        "processing": processing,
        "queue_size": queue_size,
        "retry_queue": retry_queue
    }

# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():

    with open("templates/dashboard.html") as f:

        return f.read()

# ---------------------------------------------------
# REGISTER
# ---------------------------------------------------

@app.post("/register")
def register(username: str, password: str):

    hashed = hash_password(password)

    return {
        "message": "User registered successfully",
        "username": username
    }

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

@app.post("/login")
def login(username: str, password: str):

    token = create_token({
        "username": username
    })

    return {
        "access_token": token
    }

# ---------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "running"
    }

@app.post("/dlr")
async def dlr_callback(
    message_id: int,
    status: str
):

    async with AsyncSessionLocal() as session:

        await session.execute(
            update(Message)
            .where(Message.id == message_id)
            .values(
                status=status,
                delivered_at=datetime.utcnow()
            )
        )

        await session.commit()

    print(
        f"📬 DLR received for SMS {message_id}"
    )

    return {
        "message": "DLR updated",
        "message_id": message_id,
        "status": status
    }

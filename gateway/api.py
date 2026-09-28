import hashlib
import time
import uuid
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from . import config, db, queues
from .token_bucket import TokenBucket

IDEM_TTL = 86400  # 24h


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = aioredis.BlockingConnectionPool.from_url(
        config.REDIS_URL, decode_responses=True, max_connections=200, timeout=5
    )
    app.state.redis = aioredis.Redis(connection_pool=pool)
    app.state.bucket = TokenBucket(app.state.redis, config.BUCKET_CAPACITY, config.BUCKET_RATE)
    await db.init_models()
    yield
    await app.state.redis.aclose()


app = FastAPI(lifespan=lifespan)


class SendRequest(BaseModel):
    to: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    message: str = Field(min_length=1, max_length=1600)
    sender_id: str = Field(default="GATEWAY", max_length=11)


@app.get("/health")
async def health(request: Request):
    await request.app.state.redis.ping()
    return {"status": "ok"}


@app.post("/sms/send", status_code=202)
async def send(
    req: SendRequest,
    request: Request,
    x_client_id: str = Header(default="default"),
    idempotency_key: str | None = Header(default=None),
):
    r = request.app.state.redis

    allowed, _, retry_ms = await request.app.state.bucket.allow(x_client_id)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded",
                            headers={"Retry-After": str(max(1, retry_ms // 1000))})

    msg_id = str(uuid.uuid4())
    ikey = None
    if idempotency_key:
        if len(idempotency_key) > 128:
            raise HTTPException(400, "Idempotency-Key too long (max 128)")
        fp = hashlib.sha256(f"{req.to}|{req.sender_id}|{req.message}".encode()).hexdigest()[:16]
        ikey = f"idem:{x_client_id}:{idempotency_key}"
        # SET NX is atomic: exactly one concurrent request wins the key
        won = await r.set(ikey, f"{msg_id}|{fp}", nx=True, ex=IDEM_TTL)
        if not won:
            existing = await r.get(ikey)
            if existing:
                existing_id, existing_fp = existing.split("|")
                if existing_fp != fp:
                    raise HTTPException(422, "Idempotency-Key reused with a different payload")
                return {"message_id": existing_id, "status": "queued", "duplicate": True}

    msg = {
        "id": msg_id,
        "client_id": x_client_id,
        "sender_id": req.sender_id,
        "to": req.to,
        "message": req.message,
        "retry_count": 0,
        "created_at": time.time(),
    }
    try:
        await queues.accept(r, msg)
    except Exception:
        if ikey:
            await r.delete(ikey)      # don't let a failed enqueue poison the key
        raise
    return {"message_id": msg_id, "status": "queued", "duplicate": False}


@app.get("/sms/status/{message_id}")
async def status(message_id: str, request: Request):
    data = await request.app.state.redis.hgetall(queues.status_key(message_id))
    if data:
        return {"message_id": message_id, **data}
    row = await db.get_message(message_id)
    if row:
        return {"message_id": message_id, **row}
    raise HTTPException(404, "Unknown message id")

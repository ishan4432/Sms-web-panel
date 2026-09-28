import json
import random
import time

from . import config

QUEUE = "sms:queue"
RETRY_ZSET = "sms:retry"
DLQ = "sms:dlq"
HB_TTL = 15          # worker heartbeat expires after 15s
HB_INTERVAL = 5


def status_key(msg_id: str) -> str:
    return f"msg:{msg_id}"


def processing_key(worker_id: str) -> str:
    return f"sms:processing:{worker_id}"


def hb_key(worker_id: str) -> str:
    return f"sms:hb:{worker_id}"


async def accept(r, msg: dict) -> None:
    """Hot path: one pipelined round trip. No DB write here."""
    pipe = r.pipeline(transaction=False)
    pipe.hset(status_key(msg["id"]), mapping={"status": "queued", "retry_count": 0})
    pipe.expire(status_key(msg["id"]), 86400)
    pipe.lpush(QUEUE, json.dumps(msg))
    await pipe.execute()


# ---- reliable consumption: message is moved (not popped) into a per-worker list ----

async def claim(r, worker_id: str, timeout: int = 1):
    """Atomically move one message from the queue to this worker's processing list."""
    return await r.blmove(QUEUE, processing_key(worker_id), timeout, "RIGHT", "LEFT")


async def ack(r, worker_id: str, raw: str) -> None:
    await r.lrem(processing_key(worker_id), 1, raw)


async def requeue(r, worker_id: str, raw: str) -> None:
    pipe = r.pipeline(transaction=True)
    pipe.rpush(QUEUE, raw)                      # front of the consuming end
    pipe.lrem(processing_key(worker_id), 1, raw)
    await pipe.execute()


async def heartbeat(r, worker_id: str) -> None:
    await r.set(hb_key(worker_id), 1, ex=HB_TTL)


async def reap_dead(r) -> int:
    """Recover messages from workers whose heartbeat expired (crashed / killed)."""
    if not await r.set("sms:reaper:lock", 1, nx=True, ex=10):
        return 0
    recovered = 0
    async for key in r.scan_iter(match="sms:processing:*", count=100):
        wid = key.split(":", 2)[2]
        if await r.exists(hb_key(wid)):
            continue
        while await r.lmove(key, QUEUE, "RIGHT", "RIGHT"):
            recovered += 1
    return recovered


# ---- retries with exponential backoff ----

def backoff_delay(retry_count: int) -> float:
    """retry 1..5 -> 1,2,4,8,16 seconds (+/- jitter)."""
    base = min(2 ** (retry_count - 1), config.BACKOFF_CAP_S)
    return base * random.uniform(1 - config.BACKOFF_JITTER, 1 + config.BACKOFF_JITTER)


async def schedule_retry(r, msg: dict) -> float:
    delay = backoff_delay(msg["retry_count"])
    await r.zadd(RETRY_ZSET, {json.dumps(msg): time.time() + delay})
    return delay


_MOVE_DUE = """
local due = redis.call('ZRANGEBYSCORE', KEYS[1], '-inf', ARGV[1], 'LIMIT', 0, ARGV[2])
for _, m in ipairs(due) do
  redis.call('ZREM', KEYS[1], m)
  redis.call('LPUSH', KEYS[2], m)
end
return #due
"""


async def move_due_retries(r, batch: int = 500) -> int:
    return await r.eval(_MOVE_DUE, 2, RETRY_ZSET, QUEUE, time.time(), batch)


async def push_dlq(r, msg: dict) -> None:
    await r.lpush(DLQ, json.dumps(msg))


async def set_status(r, msg_id: str, **fields) -> None:
    await r.hset(status_key(msg_id), mapping=fields)

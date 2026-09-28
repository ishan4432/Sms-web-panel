import json
import random
import time

from . import config

QUEUE = "sms:queue"
RETRY_ZSET = "sms:retry"
DLQ = "sms:dlq"


def status_key(msg_id: str) -> str:
    return f"msg:{msg_id}"


async def accept(r, msg: dict) -> None:
    pipe = r.pipeline(transaction=False)
    pipe.hset(status_key(msg["id"]), mapping={"status": "queued", "retry_count": 0})
    pipe.expire(status_key(msg["id"]), 86400)
    pipe.lpush(QUEUE, json.dumps(msg))
    await pipe.execute()


async def pop(r, timeout: int = 1):
    item = await r.brpop(QUEUE, timeout=timeout)
    return json.loads(item[1]) if item else None


def backoff_delay(retry_count: int) -> float:
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

import asyncio
import logging
import time

import redis.asyncio as aioredis

from . import config, db, queues
from .provider import ProviderError, send

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("worker")


async def process(r, msg: dict):
    try:
        provider = await send(msg["to"], msg["message"])
    except ProviderError:
        msg["retry_count"] += 1
        if msg["retry_count"] > config.MAX_RETRIES:
            await queues.push_dlq(r, msg)
            await queues.set_status(r, msg["id"], status="failed", retry_count=msg["retry_count"])
            await db.upsert_final(msg, "failed", None, time.time())
            log.info("DLQ       %s after %d retries", msg["id"][:8], config.MAX_RETRIES)
        else:
            delay = await queues.schedule_retry(r, msg)
            await queues.set_status(r, msg["id"], status="retrying", retry_count=msg["retry_count"])
            log.info("RETRY #%d  %s in %.1fs", msg["retry_count"], msg["id"][:8], delay)
        return

    await queues.set_status(r, msg["id"], status="delivered", retry_count=msg["retry_count"])
    await db.upsert_final(msg, "delivered", provider, time.time())
    log.info("DELIVERED %s (retries=%d)", msg["id"][:8], msg["retry_count"])


async def consumer(r):
    while True:
        try:
            msg = await queues.pop(r)
            if msg:
                await process(r, msg)
        except Exception:
            log.exception("worker error")
            await asyncio.sleep(0.5)


async def retry_mover(r):
    while True:
        try:
            if not await queues.move_due_retries(r):
                await asyncio.sleep(0.2)
        except Exception:
            log.exception("retry mover error")
            await asyncio.sleep(0.5)


async def main():
    pool = aioredis.BlockingConnectionPool.from_url(
        config.REDIS_URL, decode_responses=True,
        max_connections=config.WORKER_CONCURRENCY + 10, timeout=10,
    )
    r = aioredis.Redis(connection_pool=pool)
    await db.init_models()
    log.info("worker up: concurrency=%d fail_rate=%.2f latency=%sms",
             config.WORKER_CONCURRENCY, config.PROVIDER_FAIL_RATE, config.PROVIDER_LATENCY_MS)
    tasks = [asyncio.create_task(consumer(r)) for _ in range(config.WORKER_CONCURRENCY)]
    tasks.append(asyncio.create_task(retry_mover(r)))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())

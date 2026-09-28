import asyncio, time
import redis.asyncio as redis
from gateway.token_bucket import TokenBucket

CONC = 200  # max in-flight Redis calls


async def main():
    pool = redis.BlockingConnectionPool.from_url(
        "redis://localhost:6379", max_connections=CONC, timeout=10
    )
    r = redis.Redis(connection_pool=pool)
    sem = asyncio.Semaphore(CONC)
    tb = TokenBucket(r, capacity=2000, refill_rate=1000)

    async def hit():
        async with sem:
            return await tb.allow("bench")

    # 1) Burst: 2500 near-instant requests -> expect ~2000 allowed
    await r.delete("rl:bench")
    t0 = time.monotonic()
    results = await asyncio.gather(*[hit() for _ in range(2500)])
    dt = time.monotonic() - t0
    allowed = sum(1 for ok, _, _ in results if ok)
    print(f"burst: {allowed}/2500 allowed in {dt*1000:.0f}ms (expect ~2000)")

    # 2) Sustained: 1500 req/s for 10s -> settles near 1000/s once the bucket drains
    await r.delete("rl:bench")
    total_allowed = 0
    start = time.monotonic()
    for sec in range(10):
        tick = time.monotonic()
        res = await asyncio.gather(*[hit() for _ in range(1500)])
        a = sum(1 for ok, _, _ in res if ok)
        total_allowed += a
        print(f"sec {sec}: allowed {a}/1500")
        await asyncio.sleep(max(0, 1 - (time.monotonic() - tick)))
    elapsed = time.monotonic() - start
    print(f"avg allowed/s: {total_allowed / elapsed:.0f}")
    await r.aclose()

asyncio.run(main())

"""Open-loop load generator. Usage: python -m tests.loadtest RATE DURATION_S [CLIENTS]"""
import asyncio
import sys
import time

import aiohttp

URL = "http://localhost:8001/sms/send"


async def one(session, start, i, rate, clients, tag, lat, codes):
    sched = start + i / rate
    delay = sched - time.perf_counter()
    if delay > 0:
        await asyncio.sleep(delay)
    try:
        async with session.post(
            URL,
            json={"to": "+919999999999", "message": f"load-{tag}-{i}"},
            headers={"X-Client-Id": f"load-{i % clients}"},
        ) as resp:
            await resp.read()
            code = resp.status
    except Exception:
        code = "error"
    end = time.perf_counter()
    codes[code] = codes.get(code, 0) + 1
    if code == 202:
        lat.append((end - sched) * 1000)   # measured from the SCHEDULED send time


def pct(sorted_vals, p):
    return sorted_vals[min(len(sorted_vals) - 1, int(len(sorted_vals) * p))]


async def main():
    rate = int(sys.argv[1])
    duration = int(sys.argv[2])
    clients = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    total = rate * duration
    tag = int(time.time())
    lat, codes = [], {}
    conn = aiohttp.TCPConnector(limit=1000)
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        start = time.perf_counter() + 0.5
        t0 = time.perf_counter()
        await asyncio.gather(*[one(session, start, i, rate, clients, tag, lat, codes)
                               for i in range(total)])
        wall = time.perf_counter() - t0
    lat.sort()
    ok = codes.get(202, 0)
    print(f"tag={tag} target={rate}/s duration={duration}s requests={total}")
    print(f"status codes: {codes}")
    print(f"achieved: {ok / wall:.0f} accepted/s over {wall:.1f}s")
    if lat:
        print(f"latency ms  p50={pct(lat,.5):.1f}  p95={pct(lat,.95):.1f}  "
              f"p99={pct(lat,.99):.1f}  max={lat[-1]:.1f}")
    print(f"message filter for SQL: body like 'load-{tag}-%'")

asyncio.run(main())

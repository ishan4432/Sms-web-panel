# Benchmarks

Environment: Ubuntu, single node, Redis 7 (native), Python 3.14.

## Retry backoff (PROVIDER_FAIL_RATE=1.0)
Delays follow 1/2/4/8/16s with +/-10% jitter; message moves to DLQ after 5 retries.

    07:34:16 RETRY #1  e2448424 in 0.9s
    07:34:17 RETRY #2  e2448424 in 1.9s
    07:34:19 RETRY #3  e2448424 in 3.8s
    07:34:23 RETRY #4  e2448424 in 7.8s
    07:34:31 RETRY #5  e2448424 in 15.3s
    07:34:47 DLQ       e2448424 after 5 retries

## Token bucket (capacity 2000, refill 1000/s, Redis Lua, atomic)

    burst: 2197/2500 allowed in 372ms (2000 reserve + ~200 refilled during run)
    sec 0: allowed 1500/1500
    sec 1: allowed 1500/1500
    sec 2: allowed 1133/1500
    sec 3: allowed 1001/1500
    sec 4: allowed 996/1500
    sec 5: allowed 1013/1500
    sec 6: allowed 1002/1500
    sec 7: allowed 994/1500
    sec 8: allowed 1041/1500
    sec 9: allowed 1036/1500

Sustained throughput settles at ~1000/s (the refill rate) after the burst reserve drains.

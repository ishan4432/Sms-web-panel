import asyncio
import logging
import os
import random
import statistics
import time
from collections import deque

import redis.asyncio as aioredis

from . import config

log = logging.getLogger("provider")

LATENCY_LIMIT_MS = float(os.getenv("FAILOVER_LATENCY_MS", "200"))
WINDOW = 20
MIN_SAMPLES = 10
COOLDOWN_S = 10.0
TIMEOUT_S = 1.0


class ProviderError(Exception):
    pass


class Provider:
    def __init__(self, name: str):
        self.name = name
        self.samples = deque(maxlen=WINDOW)
        self.state = "closed"
        self.open_until = 0.0
        self.trial = False


PRIMARY = Provider("provider_a")
BACKUP = Provider("provider_b")

_redis = None
_chaos = {"ts": 0.0, "vals": {}}


async def _extra_ms(name: str) -> float:
    global _redis
    now = time.monotonic()
    if now - _chaos["ts"] > 0.5:
        _chaos["ts"] = now
        try:
            if _redis is None:
                _redis = aioredis.from_url(config.REDIS_URL, decode_responses=True)
            vals = await _redis.hgetall("chaos")
            _chaos["vals"] = {k: float(v) for k, v in vals.items()}
        except Exception:
            pass
    return _chaos["vals"].get(f"{name}_ms", 0.0)


def _choose() -> Provider:
    if PRIMARY.state == "closed":
        return PRIMARY
    if time.monotonic() >= PRIMARY.open_until and not PRIMARY.trial:
        PRIMARY.trial = True
        log.warning("BREAKER provider_a HALF-OPEN (trial call)")
        return PRIMARY
    return BACKUP


def _record(p: Provider, ms: float) -> None:
    if p is not PRIMARY:
        return
    if p.trial:
        p.trial = False
        if ms <= LATENCY_LIMIT_MS:
            p.state = "closed"
            p.samples.clear()
            log.warning("BREAKER provider_a CLOSED (trial %.0f ms)", ms)
        else:
            p.open_until = time.monotonic() + COOLDOWN_S
            log.warning("BREAKER provider_a stays OPEN (trial %.0f ms)", ms)
        return
    if p.state != "closed":
        return
    p.samples.append(ms)
    if len(p.samples) >= MIN_SAMPLES:
        med = statistics.median(p.samples)
        if med > LATENCY_LIMIT_MS:
            p.state = "open"
            p.open_until = time.monotonic() + COOLDOWN_S
            log.warning("BREAKER provider_a OPEN (median %.0f ms > %.0f ms), failing over to provider_b",
                        med, LATENCY_LIMIT_MS)


async def _call(p: Provider, extra_ms: float) -> None:
    await asyncio.sleep((config.PROVIDER_LATENCY_MS + extra_ms) / 1000 * random.uniform(0.9, 1.1))
    if random.random() < config.PROVIDER_FAIL_RATE:
        raise ProviderError(f"{p.name} simulated failure")


async def send(to: str, message: str) -> str:
    p = _choose()
    extra = await _extra_ms(p.name)
    t0 = time.perf_counter()
    try:
        await asyncio.wait_for(_call(p, extra), TIMEOUT_S)
    except asyncio.TimeoutError:
        _record(p, (time.perf_counter() - t0) * 1000)
        raise ProviderError(f"{p.name} timeout")
    except ProviderError:
        _record(p, (time.perf_counter() - t0) * 1000)
        raise
    _record(p, (time.perf_counter() - t0) * 1000)
    return p.name

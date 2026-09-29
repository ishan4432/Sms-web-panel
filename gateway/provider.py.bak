import asyncio
import random

from . import config


class ProviderError(Exception):
    pass


async def send(to: str, text: str) -> str:
    await asyncio.sleep(config.PROVIDER_LATENCY_MS / 1000 * random.uniform(0.5, 1.5))
    if random.random() < config.PROVIDER_FAIL_RATE:
        raise ProviderError("simulated provider failure")
    return "mock-provider"

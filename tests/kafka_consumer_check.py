import asyncio
import json
import sys

from aiokafka import AIOKafkaConsumer


async def main():
    seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    c = AIOKafkaConsumer(
        "sms.lifecycle", bootstrap_servers="localhost:9092",
        auto_offset_reset="earliest", group_id=None,
    )
    await c.start()
    counts = {}
    try:
        end = asyncio.get_event_loop().time() + seconds
        while asyncio.get_event_loop().time() < end:
            batch = await c.getmany(timeout_ms=1000)
            for tp, msgs in batch.items():
                for m in msgs:
                    e = json.loads(m.value)["event"]
                    counts[e] = counts.get(e, 0) + 1
    finally:
        await c.stop()
    print("kafka event counts:", counts)


asyncio.run(main())

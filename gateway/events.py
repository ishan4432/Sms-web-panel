import json
import logging
import os
import time

from aiokafka import AIOKafkaProducer

log = logging.getLogger("events")
TOPIC = "sms.lifecycle"
_producer = None


async def get_producer():
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(bootstrap_servers=os.getenv("KAFKA_URL", "localhost:9092"))
        await _producer.start()
    return _producer


async def emit(event_type: str, msg: dict, **extra):
    try:
        p = await get_producer()
        payload = {"event": event_type, "message_id": msg["id"], "ts": time.time(), **extra}
        await p.send_and_wait(TOPIC, json.dumps(payload).encode())
    except Exception:
        log.exception("kafka emit failed (non-fatal)")

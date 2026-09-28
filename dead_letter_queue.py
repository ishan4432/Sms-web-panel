import os
import redis
import json


r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=6379,
    decode_responses=True
)


DLQ = "dead_letter_queue"


def push_to_dlq(message):

    r.rpush(
        DLQ,
        json.dumps(message)
    )

    print("☠️ Message moved to Dead Letter Queue")


def get_dlq_messages():

    messages = r.lrange(
        DLQ,
        0,
        -1
    )

    return [
        json.loads(msg)
        for msg in messages
    ]


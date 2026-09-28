import os
import json
import redis


redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=6379,
    decode_responses=True
)


QUEUE_NAME = "sms_queue"


def enqueue_message(data):

    redis_client.rpush(
        QUEUE_NAME,
        json.dumps(data)
    )

    print(f"📥 Message queued: {data}")


def dequeue_message():

    item = redis_client.lpop(QUEUE_NAME)

    if item:
        return json.loads(item)

    return None



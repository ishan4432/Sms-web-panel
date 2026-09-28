import os
import redis
import json


r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=6379,
    decode_responses=True
)


RETRY_QUEUE = "retry_queue"


def enqueue_retry(message):

    r.rpush(
        RETRY_QUEUE,
        json.dumps(message)
    )

    print("🔁 Message added to retry queue")


def dequeue_retry():

    item = r.lpop(RETRY_QUEUE)

    if item:
        return json.loads(item)

    return None


import redis
import json

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)


def enqueue_message(message_data):

    redis_client.rpush(
        "sms_queue",
        json.dumps(message_data)
    )

    print("Message pushed to Redis queue")

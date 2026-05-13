import asyncio
import redis
import json

# Redis connection
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

# Max retry limit
MAX_RETRIES = 3


async def retry_worker():

    print("🔁 Retry worker started...")

    while True:

        # Wait for failed jobs
        job = r.brpop("sms_retry_queue")

        if not job:
            continue

        _, data = job

        sms = json.loads(data)

        retry_count = sms.get("retry_count", 0)

        print(
            f"🔁 Retrying SMS {sms['id']} "
            f"(Attempt {retry_count})"
        )

        # Wait before retry
        await asyncio.sleep(5)

        # If exceeded retries -> DLQ
        if retry_count >= MAX_RETRIES:

            r.lpush(
                "dead_letter_queue",
                json.dumps(sms)
            )

            print(
                f"💀 SMS {sms['id']} moved to dead letter queue"
            )

        else:

            # Push back to main queue
            r.lpush(
                "sms_queue",
                json.dumps(sms)
            )

            print(
                f"♻ SMS {sms['id']} pushed back to sms_queue "
                f"(Retry {retry_count})"
            )


asyncio.run(retry_worker())

import asyncio
import redis
import json

from sqlalchemy import update

from providers.fake import FakeProvider

from db.session import AsyncSessionLocal
from db.models.message import Message

# Redis connection
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)


async def process_sms():

    print("🚀 Worker started...")

    provider = FakeProvider()

    while True:

        # Wait for SMS job
        job = r.brpop("sms_queue")

        if not job:
            continue

        _, data = job

        sms = json.loads(data)

        message_id = sms["id"]

        print(f"📩 Processing SMS {message_id}")

        async with AsyncSessionLocal() as session:

            # Update status -> processing
            await session.execute(
                update(Message)
                .where(Message.id == message_id)
                .values(status="processing")
            )

            await session.commit()

            # Send SMS using provider layer
            result = await provider.send_sms(
                sms["phone_number"],
                sms["message"]
            )

            status = result["status"]

            # If failed -> push to retry queue
            if status == "failed":

                retry_job = {
                      "id": message_id,
                      "phone_number": sms["phone_number"],
                      "message": sms["message"],
                      "retry_count": sms.get("retry_count", 0) + 1
                }

                r.lpush(
                    "sms_retry_queue",
                    json.dumps(retry_job)
                )

                print(
                    f"🔁 SMS {message_id} added to retry queue"
                )

            # Update final status in PostgreSQL
            await session.execute(
                update(Message)
                .where(Message.id == message_id)
                .values(status=status)
            )

            await session.commit()

            print(
                f"✅ SMS {message_id} -> {status}"
            )


asyncio.run(process_sms())

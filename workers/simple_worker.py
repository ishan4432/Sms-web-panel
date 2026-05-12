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

    while True:

        # Wait for SMS job
        job = r.brpop("sms_queue")

        if not job:
            continue

        _, data = job

        sms = json.loads(data)

        message_id = sms["id"]

        print(f"📩 Processing SMS {message_id}")

        provider = FakeProvider()

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

            # Update final status
            await session.execute(
                update(Message)
                .where(Message.id == message_id)
                .values(status=result["status"])
            )

            await session.commit()

            print(
                f"✅ SMS {message_id} -> {result['status']}"
            )


asyncio.run(process_sms())

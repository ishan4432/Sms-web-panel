import redis
import json
import asyncio

from db import get_connection

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)


async def process_messages():

    print("Worker started...")

    while True:

        _, data = redis_client.blpop("sms_queue")

        message = json.loads(data)

        print("\nProcessing message:")
        print(message)

        conn = await get_connection()

        # Store message initially
        await conn.execute(
            """
            INSERT INTO messages (
                message_id,
                source_addr,
                destination_addr,
                short_message,
                status
            )
            VALUES ($1, $2, $3, $4, $5)
            """,
            message["message_id"],
            message["source_addr"],
            message["destination_addr"],
            message["short_message"],
            "PROCESSING"
        )

        print("Message stored with PROCESSING status")

        # Simulate delivery delay
        await asyncio.sleep(5)

        # Update status to DELIVERED
        await conn.execute(
            """
            UPDATE messages
            SET status = $1
            WHERE message_id = $2
            """,
            "DELIVERED",
            message["message_id"]
        )

        print("Message marked as DELIVERED")

        await conn.close()


asyncio.run(process_messages())

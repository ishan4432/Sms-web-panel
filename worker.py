import time
import random

from redis_queue import dequeue_message
from providers.http_provider import HTTPProvider
from database import save_sms


provider = HTTPProvider()

print("🚀 SMS Worker Started")


while True:

    sms = dequeue_message()

    if sms:

        print("\n📨 Processing SMS")
        print(sms)

        response = provider.send_sms(
            destination=sms["destination_addr"],
            message=sms["message"]
        )

        statuses = [
            "DELIVRD",
            "FAILED",
            "EXPIRED"
        ]

        sms["status"] = random.choice(statuses)

        print("\n📡 Delivery Report")
        print({
            "message_id": sms["message_id"],
            "status": sms["status"]
        })

        save_sms(sms)

    time.sleep(1)


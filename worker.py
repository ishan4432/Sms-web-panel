import time
import random

from redis_queue import dequeue_message

from router import select_provider

from retry_queue import (
    enqueue_retry,
    dequeue_retry
)

from dead_letter_queue import (
    push_to_dlq
)

from providers.http_provider import send_http_sms

from database import save_sms


MAX_RETRIES = 3


def process_sms(sms):

    print("\n📨 Processing SMS")
    print(sms)

    success = random.choice([
        True,
        False
    ])

    if success:

        provider = select_provider( sms["destination_addr"] )

        print( f"\n🛰️ Selected Provider: {provider['name']}" )

        

        response = send_http_sms(
            sms["destination_addr"],
            sms["message"]
        )

        print("\n✅ SMS Delivered")

        sms["status"] = "DELIVRD"

        save_sms(sms)

        return

    retries = sms.get(
        "retry_count",
        0
    )

    retries += 1

    sms["retry_count"] = retries

    print(
        f"\n❌ Provider failed | Retry: {retries}"
    )

    if retries >= MAX_RETRIES:

        sms["status"] = "FAILED"

        push_to_dlq(sms)

        save_sms(sms)

        return

    print("⏳ Retrying in 5 seconds")

    time.sleep(5)

    enqueue_retry(sms)


print("🚀 SMS Worker Started")


while True:

    sms = dequeue_message()

    if not sms:
        sms = dequeue_retry()

    if not sms:
        time.sleep(1)
        continue

    process_sms(sms)



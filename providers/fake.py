import asyncio
import random

from providers.base import BaseProvider


class FakeProvider(BaseProvider):

    async def send_sms(
        self,
        phone_number,
        message
    ):

        print(f"📤 Sending SMS to {phone_number}")

        await asyncio.sleep(2)

        # Random success/failure
        success = random.choice([True, False])

        if success:

            print("✅ SMS Sent")

            return {
                "status": "delivered"
            }

        else:

            print("❌ SMS Failed")

            return {
                "status": "failed"
            }

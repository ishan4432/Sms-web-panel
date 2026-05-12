import asyncio

from providers.base import BaseProvider


class FakeProvider(BaseProvider):

    async def send_sms(
        self,
        phone_number,
        message
    ):

        print(f"📤 Sending SMS to {phone_number}")

        await asyncio.sleep(2)

        print("✅ SMS Sent")

        return {
            "status": "delivered"
        }

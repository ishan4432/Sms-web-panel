import asyncio

from providers.smpp import SMPPProvider


async def main():

    provider = SMPPProvider(
        host="127.0.0.1",
        port=2776,
        username="smppclient1",
        password="password"
    )

    try:

        await provider.connect()

        await provider.send_sms(
            phone_number="919999999999",
            message="Hello from SMPP Gateway 🚀"
        )

    finally:

        await provider.disconnect()

asyncio.run(main())


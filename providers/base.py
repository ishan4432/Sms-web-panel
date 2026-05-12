class BaseProvider:

    async def send_sms(
        self,
        phone_number,
        message
    ):
        raise NotImplementedError

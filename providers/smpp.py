import smpplib.client
import smpplib.consts

from providers.base import BaseProvider


class SMPPProvider(BaseProvider):

    def __init__(
        self,
        host="127.0.0.1",
        port=2776,
        username="smppclient1",
        password="password"
    ):

        self.host = host
        self.port = port
        self.username = username
        self.password = password

        self.client = smpplib.client.Client(
            self.host,
            self.port
        )

    async def connect(self):

        try:

            print("🔌 Connecting to SMPP server...")

            self.client.connect()

            self.client.bind_transceiver(
                system_id=self.username,
                password=self.password
            )

            print("✅ SMPP bind successful")

        except Exception as e:

            print(f"❌ SMPP Connection Error: {e}")

            try:
                self.client.disconnect()
            except:
                pass

            raise

    async def send_sms(
        self,
        phone_number,
        message
    ):

        try:

            self.client.send_message(

                source_addr_ton=smpplib.consts.SMPP_TON_INTL,
                source_addr_npi=smpplib.consts.SMPP_NPI_ISDN,

                dest_addr_ton=smpplib.consts.SMPP_TON_INTL,
                dest_addr_npi=smpplib.consts.SMPP_NPI_ISDN,

                source_addr="SMPP",

                destination_addr=phone_number,

                short_message=message.encode("utf-8")
            )

            print(
                f"📤 SMPP SMS sent to {phone_number}"
            )

            return {
                "status": "sent"
            }

        except Exception as e:

            print(f"❌ SMPP Error: {e}")

            return {
                "status": "failed"
            }

    async def disconnect(self):

        try:

            self.client.unbind()
            self.client.disconnect()

            print("✅ SMPP disconnected")

        except:
            pass


import asyncio
import struct

from redis_queue import enqueue_message
from submit_sm import parse_submit_sm
from bind_parser import parse_bind

from auth import (
    authenticate,
    get_client_config,
    has_balance,
    deduct_balance
)

from rate_limiter import is_allowed

from parser import parse_pdu
from constants import *


HOST = "0.0.0.0"
PORT = 2776


async def send_pdu(
    writer,
    command_id,
    sequence_number,
    body=b""
):

    length = 16 + len(body)

    response = struct.pack(
        ">IIII",
        length,
        command_id,
        0,
        sequence_number
    ) + body

    writer.write(response)

    await writer.drain()


async def handle_client(reader, writer):

    addr = writer.get_extra_info("peername")

    print(f"\n✅ Client connected: {addr}")

    current_client = None

    while True:

        data = await reader.read(1024)

        if not data:
            break

        pdu = parse_pdu(data)

        print("\n📦 Incoming PDU")
        print(pdu)

        command_id = pdu["command_id"]
        seq = pdu["sequence_number"]

        # BIND
        if command_id == BIND_TRANSCEIVER:

            print("🔐 bind_transceiver received")

            bind_data = parse_bind(
                pdu["body"]
            )

            print("\n🔑 Credentials")
            print(bind_data)

            is_valid = authenticate(
                bind_data["system_id"],
                bind_data["password"]
            )

            if not is_valid:

                print("❌ Authentication failed")

                response = struct.pack(
                    ">IIII",
                    16,
                    BIND_TRANSCEIVER_RESP,
                    0x0000000E,
                    seq
                )

                writer.write(response)

                await writer.drain()

                break

            print("✅ Authentication successful")

            current_client = bind_data["system_id"]

            body = b"smpp-server\x00"

            await send_pdu(
                writer,
                BIND_TRANSCEIVER_RESP,
                seq,
                body
            )

        # SUBMIT_SM
        elif command_id == SUBMIT_SM:

            print("📤 submit_sm received")

            client_config = get_client_config(
                current_client
            )

            tps_limit = client_config["tps"]

            print(
                f"⚡ TPS Limit: {tps_limit}"
            )

            allowed = is_allowed(
                current_client,
                tps_limit
            )

            if not allowed:

                print("🚫 TPS limit exceeded")

                response = struct.pack(
                    ">IIII",
                    16,
                    SUBMIT_SM_RESP,
                    0x00000058,
                    seq
                )

                writer.write(response)

                await writer.drain()

                continue

            if not has_balance(current_client):

                print("💰 Insufficient balance")

                response = struct.pack(
                    ">IIII",
                    16,
                    SUBMIT_SM_RESP,
                    0x00000045,
                    seq
                )

                writer.write(response)

                await writer.drain()

                continue

            sms = parse_submit_sm(
                pdu["body"]
            )

            print("\n📨 Decoded SMS")
            print(sms)

            message_id = f"msg_{seq}"

            sms["message_id"] = message_id
            sms["status"] = "QUEUED"

            enqueue_message(sms)

            remaining_balance = deduct_balance(
                current_client
            )

            print(
                f"💳 Remaining Balance: {remaining_balance}"
            )

            message_id_bytes = (
                message_id.encode() + b"\x00"
            )

            await send_pdu(
                writer,
                SUBMIT_SM_RESP,
                seq,
                message_id_bytes
            )

        # ENQUIRE_LINK
        elif command_id == ENQUIRE_LINK:

            print("❤️ enquire_link received")

            await send_pdu(
                writer,
                ENQUIRE_LINK_RESP,
                seq
            )

        # UNBIND
        elif command_id == UNBIND:

            print("❌ unbind received")

            await send_pdu(
                writer,
                UNBIND_RESP,
                seq
            )

            break

        else:

            print(
                f"⚠️ Unknown command: {hex(command_id)}"
            )

    writer.close()

    await writer.wait_closed()

    print("🔌 Client disconnected")


async def main():

    server = await asyncio.start_server(
        handle_client,
        HOST,
        PORT
    )

    print(f"🚀 SMPP Server running on {HOST}:{PORT}")

    async with server:
        await server.serve_forever()


asyncio.run(main())


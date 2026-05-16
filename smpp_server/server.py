import asyncio
import struct

from redis_queue import enqueue_message

HOST = "0.0.0.0"
PORT = 2776


async def handle_client(reader, writer):

    addr = writer.get_extra_info("peername")

    print(f"New client connected: {addr}")

    while True:

        data = await reader.read(1024)

        if not data:
            break

        print("\nReceived raw bytes:")
        print(data)

        # SMPP Header = 16 bytes
        header = data[:16]

        command_length, command_id, command_status, sequence_number = struct.unpack(
            "!IIII",
            header
        )

        print("\nParsed SMPP Header:")
        print("command_length:", command_length)
        print("command_id:", hex(command_id))
        print("sequence_number:", sequence_number)

        # bind_transceiver
        if command_id == 0x00000009:

            print("\nReceived bind_transceiver")

            response_command_id = 0x80000009

            system_id = b"SMPPServer\x00"

            response_length = 16 + len(system_id)

            response_pdu = struct.pack(
                "!IIII",
                response_length,
                response_command_id,
                0x00000000,
                sequence_number
            ) + system_id

            writer.write(response_pdu)

            await writer.drain()

            print("\nSent bind_transceiver_resp")

        # submit_sm
        elif command_id == 0x00000004:

            print("\nReceived submit_sm")

            body = data[16:]

            print("\nsubmit_sm body:")
            print(body)

            try:

                # Parse source address
                service_type_end = body.find(b"\x00")

                offset = service_type_end + 1

                source_addr_ton = body[offset]
                offset += 1

                source_addr_npi = body[offset]
                offset += 1

                source_addr_end = body.find(b"\x00", offset)

                source_addr = body[offset:source_addr_end].decode()

                offset = source_addr_end + 1

                # Parse destination address
                dest_addr_ton = body[offset]
                offset += 1

                dest_addr_npi = body[offset]
                offset += 1

                dest_addr_end = body.find(b"\x00", offset)

                destination_addr = body[offset:dest_addr_end].decode()

                # Extract short_message cleanly
                sm_length = body[-32]

                short_message_bytes = body[-sm_length:]

                short_message = short_message_bytes.decode(
                    errors="ignore"
                )

                # Remove invalid characters
                short_message = short_message.replace("\x00", "")
                short_message = short_message.replace("\x1f", "")

                print("\nParsed SMS:")
                print("FROM:", source_addr)
                print("TO:", destination_addr)
                print("MESSAGE:", short_message)

                # Push to Redis queue
                message_data = {
                    "message_id": "msg12345",
                    "source_addr": source_addr,
                    "destination_addr": destination_addr,
                    "short_message": short_message,
                    "status": "RECEIVED"
                }

                enqueue_message(message_data)

                print("\nMessage pushed to Redis queue")

                # submit_sm_resp
                response_command_id = 0x80000004

                message_id = b"msg12345\x00"

                response_length = 16 + len(message_id)

                response_pdu = struct.pack(
                    "!IIII",
                    response_length,
                    response_command_id,
                    0x00000000,
                    sequence_number
                ) + message_id

                writer.write(response_pdu)

                await writer.drain()

                print("\nSent submit_sm_resp")

            except Exception as e:
                print("Parsing error:", e)

    print("Client disconnected")

    writer.close()
    await writer.wait_closed()


async def main():

    server = await asyncio.start_server(
        handle_client,
        HOST,
        PORT
    )

    print(f"SMPP Server running on {HOST}:{PORT}")

    async with server:
        await server.serve_forever()


asyncio.run(main())

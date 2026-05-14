import asyncio
import struct

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
        
        # bind_transceiver command id
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


 elif command_id == 0x00000004:

    print("\nReceived submit_sm")

    body = data[16:]

    print("\nsubmit_sm body:")
    print(body)

    try:

        parts = body.split(b"\x00")

        source_addr = parts[1].decode()
        destination_addr = parts[2].decode()

        sm_length = body[-32]

        short_message = body[-sm_length:].decode()

        print("\nParsed SMS:")
        print("FROM:", source_addr)
        print("TO:", destination_addr)
        print("MESSAGE:", short_message)

    except Exception as e:
       

        # bind_transceiver command id
             print("Parsing error:", e)
             print("\nReceived bind_transceiver")

            # SMPP bind_transceiver_resp
             response_command_id = 0x80000009

             system_id = b"SMPPServer\x00"

             response_length = 16 + len(system_id)

             response_pdu = struct.pack(
                "!IIII",
             response_length,
             response_command_id,
             0x00000000,  # command_status = ESME_ROK
             sequence_number
             ) + system_id

             writer.write(response_pdu)

             await writer.drain()

             print("\nSent bind_transceiver_resp")

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

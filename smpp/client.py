import socket
import struct

HOST = "127.0.0.1"
PORT = 2776


def create_bind_transceiver():

    body = (
        b"smppclient1\x00"
        b"password\x00"
        b"\x00"
        b"4\x00"
        b"\x00"
        b"\x00"
        b"\x00"
    )

    command_length = 16 + len(body)

    header = struct.pack(
        "!IIII",
        command_length,
        0x00000009,  # bind_transceiver
        0x00000000,
        1
    )

    return header + body


def create_submit_sm():

    body = (
        b"\x00"                      # service_type
        b"\x01"                      # source_addr_ton
        b"\x01"                      # source_addr_npi
        b"TEST\x00"                  # source_addr

        b"\x01"                      # dest_addr_ton
        b"\x01"                      # dest_addr_npi
        b"919999999999\x00"          # destination_addr

        b"\x00"                      # esm_class
        b"\x00"                      # protocol_id
        b"\x00"                      # priority_flag

        b"\x00"                      # schedule_delivery_time
        b"\x00"                      # validity_period

        b"\x00"                      # registered_delivery
        b"\x00"                      # replace_if_present_flag
        b"\x00"                      # data_coding
        b"\x00"                      # sm_default_msg_id

        b"\x1f"                      # sm_length = 31 bytes

        b"Hello from my own SMPP Server"
    )

    command_length = 16 + len(body)

    header = struct.pack(
        "!IIII",
        command_length,
        0x00000004,  # submit_sm
        0x00000000,
        2
    )

    return header + body


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("Connecting to SMPP Server...")

sock.connect((HOST, PORT))

print("Connected!")

# Send bind_transceiver
bind_pdu = create_bind_transceiver()

sock.sendall(bind_pdu)

response = sock.recv(1024)

print("Bind Response:")
print(response)

# Send submit_sm
submit_pdu = create_submit_sm()

print("Sending submit_sm...")

sock.sendall(submit_pdu)

print("submit_sm sent!")

sock.close()

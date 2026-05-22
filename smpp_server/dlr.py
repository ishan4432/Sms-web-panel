import struct

from constants import *


async def send_delivery_receipt(
    writer,
    sequence_number,
    message_id,
    destination_addr
):

    dlr_text = (
        f"id:{message_id} "
        f"stat:DELIVRD "
        f"err:000"
    )

    body = (
        b"\x00" 
         + b"\x01" 
         + b"\x01" 
         + b"SMSC\x00" 
         + b"\x01" 
         + b"\x01" 
         + destination_addr.encode() 
         + b"\x00"
         + b"\x00" 
         + b"\x00" 
         + b"\x00" 
         + b"\x00" 
         + b"\x00" 
         + b"\x00" 
         + b"\x00" 
         + bytes([len(dlr_text)]) 
         + dlr_text.encode()
    )

    length = 16 + len(body)

    pdu = struct.pack(
        ">IIII",
        length,
        DELIVER_SM,
        0,
        sequence_number
    ) + body

    writer.write(pdu)

    await writer.drain()

    print("\n📬 deliver_sm DLR sent")


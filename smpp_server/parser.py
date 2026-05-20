import struct


def parse_pdu(data):

    header = struct.unpack(">IIII", data[:16])

    return {
        "length": header[0],
        "command_id": header[1],
        "command_status": header[2],
        "sequence_number": header[3],
        "body": data[16:]
    }

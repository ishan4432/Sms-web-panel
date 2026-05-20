def extract_cstring(data, start):

    end = data.find(b"\x00", start)

    value = data[start:end].decode()

    return value, end + 1


def parse_bind(body):

    pos = 0

    system_id, pos = extract_cstring(body, pos)

    password, pos = extract_cstring(body, pos)

    return {
        "system_id": system_id,
        "password": password
    }


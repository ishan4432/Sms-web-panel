def extract_cstring(data, start):

    end = data.find(b"\x00", start)

    value = data[start:end].decode(errors="ignore")

    return value, end + 1


def parse_submit_sm(body):

    pos = 0

    # service_type
    _, pos = extract_cstring(body, pos)

    # source TON/NPI
    pos += 2

    # source_addr
    source_addr, pos = extract_cstring(body, pos)

    # dest TON/NPI
    pos += 2

    # destination_addr
    destination_addr, pos = extract_cstring(body, pos)

    # esm_class
    pos += 1

    # protocol_id
    pos += 1

    # priority_flag
    pos += 1

    # schedule_delivery_time
    _, pos = extract_cstring(body, pos)

    # validity_period
    _, pos = extract_cstring(body, pos)

    # registered_delivery
    pos += 1

    # replace_if_present_flag
    pos += 1

    # data_coding
    data_coding = body[pos]
    pos += 1

    # sm_default_msg_id
    pos += 1

    # sm_length
    sm_length = body[pos]
    pos += 1

    # short_message
    short_message = body[pos:pos + sm_length]

    try:
        message = short_message.decode("utf-8")
    except:
        message = short_message.decode(errors="ignore")

    return {
        "source_addr": source_addr,
        "destination_addr": destination_addr,
        "message": message,
        "data_coding": data_coding
    }


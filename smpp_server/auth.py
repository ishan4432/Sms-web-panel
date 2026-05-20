
CLIENTS = {
    "smppclient1": "password",
    "client2": "secret123"
}


def authenticate(system_id, password):

    if system_id not in CLIENTS:
        return False

    return CLIENTS[system_id] == password


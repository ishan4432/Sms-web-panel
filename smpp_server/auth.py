CLIENTS = {

    "smppclient1": {
        "password": "password",
        "tps": 5,
        "balance": 100
    },

    "enterpriseA": {
        "password": "secret123",
        "tps": 100,
        "balance": 1000
    },

    "trial_user": {
        "password": "trial123",
        "tps": 1,
        "balance": 10
    }
}


def authenticate(system_id, password):

    if system_id not in CLIENTS:
        return False

    return (
        CLIENTS[system_id]["password"]
        == password
    )


def get_client_config(system_id):

    return CLIENTS.get(system_id)

def has_balance(system_id, cost=1):

    client = CLIENTS.get(system_id)

    if not client:
        return False

    return client["balance"] >= cost


def deduct_balance(system_id, cost=1):

    CLIENTS[system_id]["balance"] -= cost

    return CLIENTS[system_id]["balance"]





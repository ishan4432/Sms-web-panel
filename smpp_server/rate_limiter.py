import time

client_requests = {}


def is_allowed(client_id, tps_limit):

    now = time.time()

    if client_id not in client_requests:
        client_requests[client_id] = []

    requests = client_requests[client_id]

    # keep only requests from last second
    requests = [
        t for t in requests
        if now - t < 1
    ]

    client_requests[client_id] = requests

    if len(requests) >= tps_limit:
        return False

    requests.append(now)

    return True


import requests


def send_http_sms(phone_number, message):

    payload = {
        "to": phone_number,
        "message": message
    }

    print("\n🌍 Sending to HTTP Provider")
    print(payload)

    response = requests.post(
        "https://httpbin.org/post",
        json=payload
    )

    print(
        f"\n✅ Provider Response: {response.status_code}"
    )

    return response.json()


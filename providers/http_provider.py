import requests


class HTTPProvider:

    def send_sms(
        self,
        destination,
        message
    ):

        payload = {
            "to": destination,
            "message": message
        }

        print("\n🌍 Sending to HTTP Provider")
        print(payload)

        # FAKE API for now
        response = requests.post(
            "https://httpbin.org/post",
            json=payload
        )

        print(f"\n✅ Provider Response: {response.status_code}")

        return response.json()


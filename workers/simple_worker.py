import time
from sms_queue.simple_queue import pop_from_queue, push_to_queue


push_to_queue({"to": "+91", "msg": "test"})

def worker():
    print("🚀 Worker started...")

    while True:
        print("👀 Checking queue...")

        data = pop_from_queue()

        if data:
            print("✅ Processing SMS:", data)
        else:
            print("😴 Queue empty, waiting...")
            time.sleep(1)

if __name__ == "__main__":
    worker()

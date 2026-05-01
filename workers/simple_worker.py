import redis
import sqlite3
import json
import time

# Redis connection
r = redis.Redis(host='localhost', port=6379, db=0)

# DB connection
conn = sqlite3.connect("messages.db", check_same_thread=False)
cursor = conn.cursor()


def send_sms_mock(phone, message):
    print(f"Sending SMS to {phone}: {message}")
    time.sleep(2)
    return True  # simulate success


while True:
    print("Waiting for job...")

    # 1. Get job from Redis
    _, data = r.brpop("sms_queue")
    job = json.loads(data)

    message_id = job["id"]

    try:
        # 2. Update → processing
        cursor.execute(
            "UPDATE messages SET status = ? WHERE id = ?",
            ("processing", message_id)
        )
        conn.commit()

        # 3. Send SMS
        success = send_sms_mock(job["phone_number"], job["message"])

        # 4. Final status
        if success:
            cursor.execute(
                "UPDATE messages SET status = ? WHERE id = ?",
                ("sent", message_id)
            )
        else:
            cursor.execute(
                "UPDATE messages SET status = ? WHERE id = ?",
                ("failed", message_id)
            )

        conn.commit()

    except Exception as e:
        print("Error:", e)

        cursor.execute(
            "UPDATE messages SET status = ? WHERE id = ?",
            ("failed", message_id)
        )
        conn.commit()

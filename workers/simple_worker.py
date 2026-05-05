import redis
import sqlite3
import json
import time
import random

r = redis.Redis(host='localhost', port=6379, db=0)

conn = sqlite3.connect("messages.db", check_same_thread=False)
cursor = conn.cursor()


def send_sms_mock(phone, message):
    print(f"Sending SMS to {phone}: {message}")
    time.sleep(2)
    return random.choice([True, False])  # randomly success/fail


while True:
    print("Waiting for job...")

    _, data = r.brpop("sms_queue")
    job = json.loads(data)

    message_id = job["id"]

    # 1. mark processing
    cursor.execute(
        "UPDATE messages SET status = ? WHERE id = ?",
        ("processing", message_id)
    )
    conn.commit()

    # 2. try sending
    success = send_sms_mock(job["phone_number"], job["message"])

    if success:
        cursor.execute(
            "UPDATE messages SET status = ? WHERE id = ?",
           ("sent", message_id)
        )
        conn.commit()

        print(f"📤 Sent to provider (awaiting DLR): {message_id}")

    else:
    # 🔍 get current retry count from DB
        cursor.execute(
            "SELECT retry_count FROM messages WHERE id = ?",
           (message_id,)
        )
        retry_count = cursor.fetchone()[0]

    if retry_count < 3:
        retry_count += 1
        print(f"🔁 Retry {retry_count} for {message_id}")

        cursor.execute(
            "UPDATE messages SET retry_count = ?, status = ? WHERE id = ?",
            (retry_count, "queued", message_id)
        )
        conn.commit()

        # 🔥 delayed retry (ZSET)
        retry_time = time.time() + (5 * retry_count)

        r.zadd("sms_retry_queue", {
            json.dumps(job): retry_time
        })

    else:
        cursor.execute(
            "UPDATE messages SET status = ? WHERE id = ?",
            ("failed", message_id)
        )
        conn.commit()

        print(f"❌ Failed permanently: {message_id}")

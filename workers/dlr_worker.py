import sqlite3
import time
import random

conn = sqlite3.connect("messages.db", check_same_thread=False)
cursor = conn.cursor()

print("📡 DLR worker started...")

while True:
    # get messages that are waiting for delivery confirmation
    cursor.execute(
        "SELECT id FROM messages WHERE status = 'sent'"
    )
    messages = cursor.fetchall()

    for msg in messages:
        message_id = msg[0]

        print(f"⏳ Checking delivery for {message_id}...")

        # simulate network delay
        time.sleep(2)

        # simulate delivery result
        delivered = random.choice([True, False])

        if delivered:
            status = "delivered"
        else:
            status = "failed"

        cursor.execute(
            "UPDATE messages SET status = ? WHERE id = ?",
            (status, message_id)
        )
        conn.commit()

        print(f"📬 DLR update: {message_id} → {status}")

    time.sleep(3)

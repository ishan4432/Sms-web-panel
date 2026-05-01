from fastapi import FastAPI
import sqlite3
import uuid
import redis
import json

app = FastAPI()

# Database connection
conn = sqlite3.connect("messages.db", check_same_thread=False)
cursor = conn.cursor()

# Redis connection
r = redis.Redis(host='localhost', port=6379, db=0)


@app.get("/")
def home():
    return {"message": "SMS API running"}


@app.post("/sms/send")
def send_sms(phone_number: str, message: str):

    # 1. Generate ID
    message_id = str(uuid.uuid4())

    # 2. Save to DB
    cursor.execute(
        "INSERT INTO messages (id, phone_number, message, status) VALUES (?, ?, ?, ?)",
        (message_id, phone_number, message, "queued")
    )
    conn.commit()

    # 3. Push to Redis queue
    job = {
        "id": message_id,
        "phone_number": phone_number,
        "message": message
    }

    r.lpush("sms_queue", json.dumps(job))

    return {
        "message_id": message_id,
        "status": "queued"
    }


@app.get("/sms/status/{message_id}")
def get_status(message_id: str):

    cursor.execute(
        "SELECT id, phone_number, message, status, retry_count FROM messages WHERE id = ?",
        (message_id,)
    )

    row = cursor.fetchone()

    if not row:
        return {"error": "Message not found"}

    return {
        "id": row[0],
        "phone_number": row[1],
        "message": row[2],
        "status": row[3],
        "retry_count": row[4]
    }

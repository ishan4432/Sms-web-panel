from fastapi import Header
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3
import uuid
import redis
import json
from api.auth import (
    hash_password,
    verify_password,
    create_token
)

app = FastAPI()

# Database connection
conn = sqlite3.connect(
    "messages.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

conn.commit()
# Database connection

# Redis connection
r = redis.Redis(host='localhost', port=6379, db=0)

def verify_api_key(x_api_key):

    cursor.execute(
        "SELECT * FROM api_keys WHERE api_key = ?",
        (x_api_key,)
    )

    return cursor.fetchone()

@app.get("/")
def home():
    return {"message": "SMS API running"}


# 🔥 RATE LIMIT FUNCTION
def is_rate_limited(phone_number):
    key = f"rate:{phone_number}"

    current = r.get(key)

    if current is None:
        r.set(key, 1, ex=60)
        return False

    elif int(current) < 5:
        r.incr(key)
        return False

    else:
        return True


# 📩 SEND SMS
@app.post("/sms/send")
@app.post("/sms/send")
def send_sms(
    phone_number: str,
    message: str,
    x_api_key: str = Header(None)
):

    if not verify_api_key(x_api_key):
        return {"error": "Invalid API Key"}

    # rest of code

    # 🔥 RATE LIMIT CHECK
    if is_rate_limited(phone_number):
        return {"error": "Rate limit exceeded. Try again later."}

    # Generate ID
    message_id = str(uuid.uuid4())

    # Save in DB
    cursor.execute(
        "INSERT INTO messages (id, phone_number, message, status) VALUES (?, ?, ?, ?)",
        (message_id, phone_number, message, "queued")
    )
    conn.commit()

    # Push to Redis
    job = {
        "id": message_id,
        "phone_number": phone_number,
        "message": message
    }

    r.lpush("sms_queue", json.dumps(job))

    return {"message_id": message_id, "status": "queued"}


# 📊 CHECK STATUS
@app.get("/sms/status/{message_id}")
def get_status(message_id: str):

    cursor.execute(
        "SELECT status FROM messages WHERE id = ?",
        (message_id,)
    )
    result = cursor.fetchone()

    if result:
        return {"message_id": message_id, "status": result[0]}
    else:
        return {"error": "Message not found"}

@app.get("/analytics")
def analytics():

    total = cursor.execute(
        "SELECT COUNT(*) FROM messages"
    ).fetchone()[0]

    delivered = cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE status='delivered'"
    ).fetchone()[0]

    failed = cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE status='failed'"
    ).fetchone()[0]

    queued = cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE status='queued'"
    ).fetchone()[0]

    processing = cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE status='processing'"
    ).fetchone()[0]
    queue_size = r.llen("sms_queue")

    processing = cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE status='processing'"
    ).fetchone()[0]

    retry_queue = r.zcard("sms_retry_queue")
    return {
        "total_messages": total,
        "delivered": delivered,
        "failed": failed,
        "queued": queued,
        "processing": processing,
        "queue_size": queue_size,
        "retry_queue": retry_queue
    }

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():

    with open("templates/dashboard.html") as f:
        return f.read()

@app.post("/register")
def register(username: str, password: str):

    hashed = hash_password(password)

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed)
        )

        conn.commit()

        return {
            "message": "User registered successfully"
        }

    except Exception as e:
        
        return {
            "error": str(e)
        }

@app.post("/login")
def login(username: str, password: str):

    user = cursor.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()

    if not user:
        return {
            "error": "User not found"
        }

    stored_password = user[2]

    if not verify_password(password, stored_password):
        return {
            "error": "Wrong password"
        }

    token = create_token({
        "username": username
    })

    return {
        "access_token": token
    }

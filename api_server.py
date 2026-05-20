from fastapi import FastAPI
from pydantic import BaseModel
from redis_queue import enqueue_message
from database import cursor

app = FastAPI()

class SMSRequest(BaseModel):

    source_addr: str
    destination_addr: str
    message: str


@app.get("/health")
async def health():

    return {
        "status": "running"
    }


@app.post("/send-sms")
async def send_sms(data: SMSRequest):

    sms = {
        "source_addr": data.source_addr,
        "destination_addr": data.destination_addr,
        "message": data.message,
        "message_id": "api_msg_001",
        "status": "QUEUED"
    }

    enqueue_message(sms)

    return {
        "message": "SMS queued",
        "sms": sms
    }


@app.get("/sms-logs")
async def sms_logs():

    cursor.execute("""
    SELECT
        message_id,
        source_addr,
        destination_addr,
        message,
        status
    FROM sms_logs
    """)

    rows = cursor.fetchall()

    logs = []

    for row in rows:

        logs.append({
            "message_id": row[0],
            "source_addr": row[1],
            "destination_addr": row[2],
            "message": row[3],
            "status": row[4]
        })

    return logs


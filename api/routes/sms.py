from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/sms", tags=["SMS"])

class SMS(BaseModel):
    to: str
    message: str
    sender_id: str

@router.post("/send")
def send_sms(sms: SMS):
    print("Sending SMS...")
    print(sms)
    return {"status": "SMS received"}

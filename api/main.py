from fastapi import FastAPI
from api.routes.sms import router as sms_router

app = FastAPI()

@app.get("/")
def home():
    return {"message": "SMS Gateway is running"}

app.include_router(sms_router)

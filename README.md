# Sms-web-panel
Scalable SMS Gateway  using Kafka-based event-driven architecture, async workers, and SMPP integration

#Day 1
📩 SMS Gateway
This project is being built step-by-step to understand backend systems and messaging architecture.
🚀 Day 1
Project setup
FastAPI app created
Basic API structure
🛠 Tech Stack
Python
FastAPI
Uvicorn
▶️ Run the project
uvicorn main:app --reload

Open in browser:
http://127.0.0.1:8000

📘 API Docs

http://127.0.0.1:8000/docs

🎯 Goal

To build a scalable SMS gateway.

---

# 🚀 Day 2

## 📩 SMS Send API

On Day 2, the project was extended to include a real SMS sending endpoint with proper request validation and service layer architecture.

### ✅ Features Added
- `/sms/send` API endpoint
- Request validation using Pydantic schemas
- Service layer for handling business logic
- Clean separation of concerns (API → Service)

### 🔄 Request Flow

User → API → Validation → Service Layer

### 📥 Example Request

```json
{
  "to": "+919999999999",
  "message": "Hello World",
  "sender_id": "TEST"
}
{
  "status": "queued"
}

✅ Day 1 completed
🔜 Day 2 coming next

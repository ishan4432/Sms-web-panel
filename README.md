# 📩 SMS Web Panel

A scalable SMS gateway inspired by Jasmin SMS, built using a Kafka-based event-driven architecture, async workers, and SMPP integration.

---

## 🎯 Goal
To build a production-grade SMS gateway capable of handling high-throughput messaging systems.

---

# 🚀 Day 1 – Project Setup

## 🧩 What was done
- FastAPI project setup
- Basic API structure
- Initial project architecture

## 🛠 Tech Stack
- Python
- FastAPI
- Uvicorn

## ▶️ Run the project
```bash
uvicorn main:app --reload

🚀 Day 2 – SMS Send API
📩 Features Added
/sms/send API endpoint
Request validation using Pydantic
Service layer implementation
Clean architecture (API → Service)
🔄 Request Flow

User → API → Validation → Service Layer

📥 Example Request
{
  "to": "+919999999999",
  "message": "Hello World",
  "sender_id": "TEST"
}
📤 Example Response
{
  "status": "queued"
}

🚀 Day 3 – Queue & Worker System
⚙️ Features Added
Background worker system
Basic queue implementation (in-memory)
Continuous worker processing loop
🔄 System Evolution
Before:

Client → API → Service → Print

Now:

Client → API → Queue → Worker → Process

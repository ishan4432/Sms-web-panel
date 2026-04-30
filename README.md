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
bash
uvicorn main:app --reload

## 🚀 Day 2 – SMS Send API
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

## 🚀 Day 3 – Queue & Worker System
⚙️ Features Added
Background worker system
Basic queue implementation (in-memory)
Continuous worker processing loop
🔄 System Evolution
Before:

Client → API → Service → Print

## 🚀 Day 4 – Redis Queue Integration

⚙️ Features Added

Integrated Redis as a message broker (replacing in-memory queue)
Implemented persistent queue using Redis lists
Introduced RPUSH / BLPOP based queue processing
Improved system reliability (messages persist even if API restarts)

🔄 System Evolution

Before:

Client → API → In-Memory Queue → Worker → Process

Now:

Client → API → Redis Queue → Worker → Process

🧠 Key Learning

Introduction to message brokers (Redis)
Producer–Consumer architecture
Decoupling API from processing layer
Basics of distributed system design

## 🚀 Day 5 – Background Worker System (Stabilized Pipeline)

⚙️ Features Added

Built persistent background worker using Redis blocking queue (BLPOP)
Implemented continuous message consumption loop
Established real async processing pipeline
Verified end-to-end message flow (API → Redis → Worker)

📩 Working Flow

Client → FastAPI → Redis Queue → Worker → Processing

🧠 Key Learning

Event-driven architecture
Background job processing
Producer–Consumer pattern in real systems
How modern messaging systems (like WhatsApp/notification services) work internally
Debugging distributed components (API, Redis, Worker)

Client → API → Queue → Worker → Process

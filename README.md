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

# 🚀 SMS Gateway System (Day 6)

Today I upgraded my SMS system from a simple API to a **real asynchronous backend architecture**.
---
## 🔥 What I Built Today
### ✅ 1. Redis-Based Queue System
- Implemented Redis as a message broker
- API pushes SMS jobs into queue
- Worker consumes jobs asynchronously
---
### ✅ 2. Worker System (Background Processing)
- Created a separate worker service
- Processes SMS jobs independently from API
- Simulates real telecom message flow
---
### ✅ 3. Message Status Tracking (CORE FEATURE)
Each SMS now has lifecycle states:

# 🚀 SMS Gateway System (Day 7)

This project simulates a real-world SMS gateway system with asynchronous processing, retry logic, and status tracking.

## 🔥 Features

### ✅ 1. Asynchronous SMS Processing

* API does not send SMS directly
* Messages are pushed to Redis queue
* Worker processes them in background

---

### ✅ 2. Worker System

* Separate service for handling SMS jobs
* Simulates real telecom backend behavior

---

### ✅ 3. Message Status Tracking

Each SMS goes through:

queued → processing → sent → failed


Stored in SQLite database and updated in real-time

---
### ✅ 4. Retry Mechanism (Day 7)

* Automatically retries failed messages (max 3 attempts)
* Delay between retries
* Tracks retry_count in database
* Marks message as failed after max retries
---
## 🧠 Architecture
Client
↓
FastAPI (API Layer)
↓
Redis Queue
↓
Worker Service
↓
SQLite Database

---
## ⚙️ Tech Stack
* Python
* FastAPI
* Redis
* SQLite
---
## 🧪 Example

A message may:

* Fail initially
* Retry 2 times
* Finally succeed → status = sent, retry_count = 2
---
## 🚧 Next Improvements

* Delayed queue using Redis ZSET (remove sleep)
* Delivery reports (DLR)
* Dashboard for monitoring
* API authentication
---
## 📌 Learning Outcome

This project helped me understand:

* Async system design
* Background workers
* Failure handling & retries
* Real backend architecture patterns


Client → API → Queue → Worker → Process

# 🚀 SMS Gateway System (Day 8)

This project simulates a real-world SMS gateway with async processing, retry logic, and delayed queue handling.

---

## 🔥 Features

### ✅ 1. Asynchronous Processing

* API pushes messages to Redis queue
* Worker processes SMS in background

---

### ✅ 2. Message Status Tracking

Each SMS goes through:
queued → processing → sent → failed

Stored in SQLite database

---

### ✅ 3. Retry Mechanism

* Retries failed messages up to 3 times
* Tracks retry_count in database

---

### ✅ 4. Delayed Queue (NEW 🚀)

* Removed blocking `sleep()`
* Uses Redis **Sorted Set (ZSET)** for scheduling retries
* Separate retry worker handles delayed jobs

---

## 🧠 Architecture

Client
↓
FastAPI (API)
↓
Redis Queue
↓
Worker (send SMS)
↓
❌ Fail → Redis ZSET (delayed retry)
↓
Retry Worker
↓
Back to Queue
↓
Worker → sent / failed

---

## ⚙️ Tech Stack

* Python
* FastAPI
* Redis (Queue + ZSET)
* SQLite

---

## 💡 Key Learning

* Avoid blocking operations (`sleep`) in workers
* Use delayed queues for retry scheduling
* Design systems that expect failure

---

## 🚧 Next Steps

* Delivery Reports (DLR)
* Rate limiting
* Dashboard UI
* Kafka integration

---

# SMS Gateway System – Day 9

This project simulates a real-world SMS gateway with async processing, retry logic, delayed queue handling, and analytics tracking.

---

# 🚀 Features

## ✅ Async SMS Processing
- API pushes messages into Redis queue
- Background worker processes SMS asynchronously

## ✅ Message Status Tracking
Each SMS goes through:

```text
queued → processing → delivered / failed

# SMS Gateway System - Day 10

## ✅ Dashboard UI
Added a dashboard for monitoring SMS gateway activity.

Dashboard features:
- Total messages count
- Delivered SMS count
- Failed SMS count
- Queued messages
- Processing messages
- Real-time analytics display

The dashboard fetches data from the `/analytics` API endpoint.

## ✅ Authentication System (Day 11)

Added JWT-based authentication system.

Features:
- User registration
- User login
- Password hashing using bcrypt
- JWT token generation
- Secure authentication flow

Endpoints added:

```http
POST /register
POST /login

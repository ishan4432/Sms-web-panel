import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://sms:sms@localhost:5432/sms")

BUCKET_CAPACITY = int(os.getenv("BUCKET_CAPACITY", "2000"))
BUCKET_RATE = int(os.getenv("BUCKET_RATE", "1000"))

MAX_RETRIES = 5
BACKOFF_CAP_S = 16
BACKOFF_JITTER = 0.1

PROVIDER_LATENCY_MS = float(os.getenv("PROVIDER_LATENCY_MS", "50"))
PROVIDER_FAIL_RATE = float(os.getenv("PROVIDER_FAIL_RATE", "0.15"))

WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "50"))

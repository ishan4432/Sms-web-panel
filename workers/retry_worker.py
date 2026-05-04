import redis
import time
import json

r = redis.Redis(host='localhost', port=6379, db=0)

print("Retry worker started...")

while True:
    current_time = time.time()

    # get all jobs whose retry time has come
    jobs = r.zrangebyscore("sms_retry_queue", 0, current_time)

    for job in jobs:
        # move job back to main queue
        r.lpush("sms_queue", job)

        # remove from retry queue
        r.zrem("sms_retry_queue", job)

        print("🔁 Moved retry job back to queue")

    time.sleep(2)

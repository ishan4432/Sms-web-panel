from sms_queue.simple_queue import push_to_queue

def enqueue_sms(data):
    push_to_queue(data)
    print("Added to queue:", data)

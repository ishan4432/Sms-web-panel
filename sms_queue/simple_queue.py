from collections import deque

queue = deque()

def push_to_queue(data):
    queue.append(data)

def pop_from_queue():
    if queue:
        return queue.popleft()
    return None

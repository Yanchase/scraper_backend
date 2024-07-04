# dynamic_stream_handler.py
import logging
from collections import deque
from flask import Response, stream_with_context


class DynamicStreamHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        self.subscribers = []

    def emit(self, record):
        message = self.format(record)
        for subscriber in self.subscribers:
            if subscriber["level"] <= record.levelno:
                subscriber["queue"].append(message)

    def register_subscriber(self, level):
        queue = deque()
        self.subscribers.append({"level": level, "queue": queue})
        return queue

    def stream_logs(self, queue):
        def generator():
            while True:
                while queue:
                    yield f"data: {queue.popleft()}\n\n"

        return Response(stream_with_context(generator()), mimetype="text/event-stream")

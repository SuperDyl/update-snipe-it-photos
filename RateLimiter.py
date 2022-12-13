from collections import deque
from datetime import time, datetime
from time import sleep
import requests


class RateLimiter:
    api_url: str
    time_limit: int
    request_limit: int
    request_queue: deque[datetime]

    def __init__(self, api_url: str, time_limit: int = 60, request_limit: int = 120):
        self.api_url = api_url
        self.time_limit = time_limit
        self.request_limit = request_limit
        self.request_queue = deque()

    @staticmethod
    def seconds_elapsed(time1: datetime) -> float:
        return (datetime.now() - time1).total_seconds()

    def _clean_requests_queue(self):
        while self.seconds_elapsed(self.request_queue[0]) > self.time_limit:
            self.request_queue.pop()

    def _wait(self):
        self._clean_requests_queue()

        if len(self.request_queue) >= self.request_limit:
            sleep(self.time_limit - self.seconds_elapsed(self.request_queue[0]))

    def _add_request(self):
        self.request_queue.append(datetime.now())

    def get(self, url: str, *args, **kwargs) -> requests.Response:
        self._wait()
        self._add_request()

        # setup url here

        return requests.get(r'/'.join(self.api_url, url))

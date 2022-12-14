import random
from collections import deque
from datetime import datetime
from time import sleep
from typing import Optional, Callable, Any

import requests

RL = Any


class RateLimiter:
    api_url: str
    time_limit: int
    request_limit: int
    request_queue: deque[datetime]
    random_sleep: Callable[[RL], float]

    @staticmethod
    def _random_wait(rate_limiter: RL) -> float:
        minimum: float = (rate_limiter.time_limit / rate_limiter.request_limit) / 2
        maximum: float = minimum * 3
        return random.uniform(minimum, maximum)

    def __init__(self,
                 api_url: str,
                 time_limit: int = 60,
                 request_limit: int = 120,
                 random_sleep: Optional[Callable[[None], float]] = None):
        self.api_url = api_url
        self.time_limit = time_limit
        self.request_limit = request_limit
        self.request_queue = deque()
        self.random_sleep = random_sleep if random_sleep is not None else self._random_wait

    @staticmethod
    def seconds_elapsed(time1: datetime) -> float:
        return (datetime.now() - time1).total_seconds()

    def _clean_requests_queue(self) -> None:
        while self.request_queue and self.seconds_elapsed(self.request_queue[0]) > self.time_limit:
            self.request_queue.pop()

    def _wait(self) -> bool:
        self._clean_requests_queue()

        if len(self.request_queue) >= self.request_limit:
            sleep(self.time_limit - self.seconds_elapsed(self.request_queue[0]))
            return True
        return False

    def _add_request(self) -> None:
        self.request_queue.append(datetime.now())

    def _combine_url(self, added_url: str) -> str:
        return self.api_url if not added_url else ''.join((self.api_url, added_url))

    def _request_preprocessing(self) -> None:
        if not self._wait():
            sleep(self.random_sleep(self))
        self._add_request()

    def get(self, url: str, *args, **kwargs) -> requests.Response:
        self._request_preprocessing()
        return requests.get(self._combine_url(url), *args, **kwargs)

    def put(self, url: str, *args, **kwargs) -> requests.Response:
        self._request_preprocessing()
        return requests.put(self._combine_url(url), *args, **kwargs)

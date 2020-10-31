import asyncio
import requests

from collections import deque
from datetime import datetime, timedelta

class lichess_integration():

    def __init__(self):
        self.base_url = "https://lichess.org"
        self.bad_status_code = 429
        self.relax_timeout = timedelta(seconds = 60)
        self.default_timeout = timedelta(seconds = 1)
        self.next_request_time = datetime.now()
        self.request_queue = deque()
        self.request_id = 0

    def add_game_request(self, username):
        url = f"/api/user/{username}/current-game"
        payload = {
            'moves':"false",
            'opening': "false",
        }
        self.request_id += 1
        self.request_queue.append((self.request_id, url, payload))
        return self.request_id

    def handle_next_request(self):
        if len(self.request_queue) == 0:
            return None

        if datetime.now() < self.next_request_time:
            return None

        request_id, url, payload = self.request_queue.popleft()

        request = requests.get(self.base_url + url, payload)

        if request.status_code == self.bad_status_code:
            self.next_request_time = datetime.now() + self.relax_timeout
        else:
            self.next_request_time = datetime.now() + self.default_timeout

        return request_id, request


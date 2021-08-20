import asyncio
import requests
import typing

from collections import deque, namedtuple
from datetime import datetime, timedelta


BASE_URL = "https://lichess.org"
BAD_STATUS = 429
RELAX_TIMEOUT   = timedelta(seconds = 60)
DEFAULT_TIMEOUT = timedelta(seconds = 1)
MAX_GAMES_PER_REQUEST = 300

METHOD       = typing.Literal["GET", "POST"]
REQUEST_KIND = typing.Literal["GAME_META_DATA", "USER_CURRENT_GAME", "CUSTOM"]

open_request = namedtuple("open_request", "request_id, request")

# Used to bundle multiple game requests together since lichess supports exporting up to 300 games at a time
# Possibly over-engineered for the small scale that I will use this in, but worth it nonetheless
def merge_requests(elements, new_request, request_id, max_elements=MAX_GAMES_PER_REQUEST):
    request_with_id = open_request(request_id, new_request)
    if len(elements) == 0 or len(elements[-1].request.data) == max_elements:
        elements.append(request_with_id)
        return elements[-1].request_id
    partial_request = elements[-1].request
    free_slots = max_elements - len(partial_request.data)
    print(free_slots)
    partial_request.data.extend(new_request.data[:free_slots])
    if free_slots >= len(new_request.data):
        return elements[-1].request_id
    new_request.data = new_request.data[:free_slots]
    elements.append(request_with_id)
    return request_id

def append_request(elements, new_request, request_id):
    request_with_id = open_request(request_id, new_request)
    elements.append(request_with_id)
    return request_id

queue_handler = {
  "GAME_META_DATA": merge_requests,
  "USER_CURRENT_GAME": append_request,
  "CUSTOM": append_request
}

urls = {
  "GAME_META_DATA": "/games/export/_ids",
  "USER_CURRENT_GAME": "/api/games/user/{}" 
}

default_params = {
  "GAME_META_DATA": {'moves': 'false', 'opening': 'false'},
  "USER_CURRENT_GAME": {'max': 10, 'moves': 'false', 'opening': 'false'},
  "CUSTOM": {}
}

build_data = lambda x: ",".join(x) if x else None


def build_game_meta_data_request(data: list[str], params: dict[str, str] ={}):
    request_params = default_params["GAME_META_DATA"]
    request_params.update(default_params)
    return lichess_request(method="POST", request_kind="GAME_META_DATA", url=urls["GAME_META_DATA"], params=request_params, data=data)

def build_user_current_game_request(player: str, opponent: str, params: dict[str, str] ={}):
    request_params = default_params["GAME_META_DATA"]
    request_params.update(params)
    request_params["vs"] = opponent
    return lichess_request(method="GET", request_kind="USER_CURRENT_GAME", url=urls["USER_CURRENT_GAME"].format(player), params=request_params)

class lichess_request():

    def __init__(self, method: METHOD, request_kind: REQUEST_KIND, url: str =None, params: dict[str, str] =None, data: list[str] =None):
        self.method = method
        self.request_kind = request_kind
        self.url = url
        self.params = params
        self.data = data

    def build_request(self):
        return requests.Request(method=self.method, url=BASE_URL + self.url, data=build_data(self.data), params=self.params)


# Has different queues for different types of request, since e.g. game requests can be merged to save bandwidth
class request_handler():

    def __init__(self):
        self.request_queue = {kind: deque() for kind in typing.get_args(REQUEST_KIND)}
        self.total_requests = 0
        self.open_requests = 0
        self.next_request_time = datetime.now()
        self.session = requests.Session()
        self.results = {}

    def add_request(self, request: lichess_request):
        self.total_requests += 1
        kind = request.request_kind

        relevant_queue = self.request_queue[kind]
        request_id =  queue_handler[kind](relevant_queue, request, self.total_requests)

        self.open_requests += request_id == self.total_requests
        return request_id

    def get_next_request(self):
        if self.open_requests == 0:
            return None
        # select queue which contains the next request to be made
        selected_queue = min(self.request_queue.values(), key = lambda vs: vs[0].request_id if vs else float('inf'))
        self.open_requests -= 1
        return selected_queue.popleft()

    def make_next_request(self):
        if self.open_requests == 0 or datetime.now() < self.next_request_time:
            return None

        request_id, request = self.get_next_request()
        prepared_request = request.build_request().prepare()
        answer = self.session.send(prepared_request)

        if answer.status_code == BAD_STATUS:
            self.next_request_time = datetime.now() + RELAX_TIMEOUT
        else:
            self.next_request_time = datetime.now() + DEFAULT_TIMEOUT

        self.results[request_id] = answer
        return request_id, answer.status_code

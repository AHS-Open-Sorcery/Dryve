from typing import List
from request import *
from trip import *
from datetime import datetime


class User:
    name: str
    id: str

    def __init__(self, name, _id):
        self.name = name
        self.id = _id
        self.requests = []
        self.offers = []

    def __eq__(self, other):
        return other.id == self.id

    def request_join(self, trip, pickup) -> Request:
        req = Request(self, trip, pickup)
        return req

    def make_offer(self, origin, dest, capacity: int, arrival: datetime): # -> Trip
        trip = Trip(origin, dest, self, capacity, arrival)
        return trip


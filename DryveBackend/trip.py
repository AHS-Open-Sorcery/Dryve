from location import *
from typing import List, Tuple, Any
from datetime import datetime
import random


class Trip:
    origin: Location
    dest: Location
    # driver: User
    riders: List[Tuple[Any, Location]]  # User, Location
    capacity: int
    arrival_time: datetime
    id: str

    def __init__(self, origin: Location, dest: Location, driver, capacity: int, arrival: datetime):
        self.origin = origin
        self.dest = dest
        self.driver = driver
        self.riders = []
        self.capacity = int(capacity)
        self.arrival_time = arrival
        self.id = random_trip_id()

    def is_full(self):
        return len(self.riders) >= self.capacity

    def pickup_locations(self):
        return list(map(lambda _tuple: _tuple[1], self.riders))

    def rider_users(self):
        return list(map(lambda _tuple: _tuple[0], self.riders))

    def remove_rider(self, rider) -> bool:
        pair = None
        for user, loc in self.riders:
            if user.id == rider.id:
                pair = (user, loc)
        if pair is None:
            return False
        self.riders.remove(pair)
        return True


def random_trip_id():
    id_alphabet = list(range(ord('a'), ord('z') + 1)) + list(range(ord('1'), ord('9') + 1))
    output = ''
    for i in range(6):
        output += chr(random.choice(id_alphabet))
    return output
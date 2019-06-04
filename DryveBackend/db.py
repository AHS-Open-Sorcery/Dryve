from typing import Optional

from google.cloud import firestore
from user import *
from trip import *
from request import *
from location import *
from datetime import datetime, timedelta
import json


def normalize(datetime_ns):
    return datetime.combine(datetime_ns.date(), datetime_ns.time())


class Database:
    client: firestore.Client

    def __init__(self):
        self.client = firestore.Client()

    def get_trip(self, id_: str) -> Optional[Trip]:
        print(f"get trip {id_}")
        stream = self.client.collection('trips').document(id_).get()
        if stream.exists:
            obj = stream.to_dict()
            trip = Trip(
                Location.from_repr(obj["origin"]),
                Location.from_repr(obj["dest"]),
                self.get_user(obj["driver"]),
                obj["capacity"],
                normalize(obj["arrival_time"])
            )
            trip.riders = []
            for rider_repr in obj["riders"]:
                rider_id, pickup = json.loads(rider_repr)
                trip.riders.append((self.get_user(rider_id), Location.from_repr(pickup)))
            trip.id = obj["id"]
            return trip
        else:
            return None

    def store_trip(self, trip: Trip):
        self.client.collection('trips').document(trip.id).set({
            "origin": trip.origin.repr(),
            "dest": trip.dest.repr(),
            "driver": trip.driver.id,
            "riders": list(map(lambda pair: json.dumps([pair[0].id, pair[1].repr()]), trip.riders)),
            "capacity": trip.capacity,
            "arrival_time": trip.arrival_time,
            "id": trip.id
        })
        self.store_user(trip.driver)
        for pair in trip.riders:
            self.store_user(pair[0])

    def add_request(self, request: Request):
        self.store_trip(request.trip)
        self.store_user(request.rider)
        _, doc = self.client.collection('requests').add({
            "trip": request.trip.id,
            "rider": request.rider.id,
            "pickup": request.pickup.repr()
        })
        request.id = doc.id
        return doc.id

    def remove_request(self, request: Request):
        self.client.collection('requests').document(request.id).delete()

    def store_user(self, user) -> firestore.DocumentReference:
        doc = self.client.collection('users').document(str(user.id))
        doc.set({
            "name": user.name,
            "id": user.id,
            "offers": list(map(lambda trip: trip.id, user.offers)),
            "requests": list(map(lambda req: req.id, user.requests))
        })
        return doc

    def get_user(self, user_id: int):
        docs = self.client.collection('users').document(str(user_id)).get()
        if docs.exists:
            obj = docs.to_dict()
            output = User(obj["name"], obj["id"])
            output.offers = list(map(lambda _id: self.get_trip(_id), obj["offers"]))
            output.requests = list(map(lambda _id: self.get_request(_id), obj["requests"]))
            return output
        else:
            return None

    def get_request(self, req_id: str):
        print(f"get request {req_id}")
        reqs = self.client.collection('requests').document(req_id).get()
        if reqs.exists:
            obj = reqs.to_dict()
            output = Request(
                self.get_user(obj["rider"]),
                self.get_trip(obj["trip"]),
                Location.from_repr(obj["pickup"])
            )
            output.id = reqs.id
            return output
        else:
            return None

    def remove_trip(self, trip: Trip):
        self.client.collection('trips').document(trip.id).delete()

    def query_trip(self, dest: Location, time: datetime = datetime.now()):
        stream = self.client.collection('trips').get()
        for trip_doc in stream:
            trip_dest = Location.from_repr(trip_doc.to_dict()["dest"])
            arr_time = normalize(trip_doc.to_dict()["arrival_time"])
            if trip_dest.is_close_to(dest) and \
                    (timedelta(minutes=30) > arr_time - time > timedelta(seconds=0)) or \
                    (timedelta(minutes=30) > time - arr_time > timedelta(seconds=0)):
                yield trip_doc.id

    def requests_of_trip(self, trip: Trip):
        results = self.client.collection("requests").where('trip', '==', trip.id)
        return list(map(lambda req_obj: self.get_request(req_obj.id), results.get()))

    def trips_of_driver(self, driver: User):
        results = self.client.collection("trips").where("driver", "==", driver.id)
        return list(map(lambda trip_obj: self.get_trip(trip_obj.id), results.get()))

    def trips_of_rider(self, rider: User):
        for trip_obj in self.client.collection("trips").get():
            for rider_json in trip_obj.to_dict()["riders"]:
                if rider_json.startswith(f'["{rider.id}",'):
                    yield self.get_trip(trip_obj.id)

    def rider_has_requested(self, rider: User, trip: Trip):
        for req in self.requests_of_trip(trip):
            if req.rider.id == rider.id:
                return True
        return False

    def rider_leave_trip(self, rider: User, trip: Trip):
        for pair in trip.riders:
            if pair[0] == rider:
                trip.riders.remove(pair)
                self.store_trip(trip)
                return True
        return False

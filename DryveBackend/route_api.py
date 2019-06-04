from trip import *
import googlemaps
from secrets import *
from urllib.parse import urlencode
from typing import List
from datetime import timedelta

client = googlemaps.Client(MAPS_API_KEY)

def find_route_url(trip: Trip):
    return "https://www.google.com/maps/dir/?api=1&" + urlencode({
        "origin": trip.origin.full_address(),
        "origin_place_id": trip.origin.place_id,
        "destination": trip.dest.full_address(),
        "destination_place_id": trip.dest.place_id,
        "waypoints": "|".join(map(lambda loc: loc.full_address(), trip.pickup_locations())),
        "waypoint_place_ids": "|".join(map(lambda loc: loc.place_id, trip.pickup_locations()))
    })

def geocode(address) -> List[dict]:
    return client.geocode(address)


class Route:
    response: dict
    trip: Trip

    def __init__(self, trip: Trip):
        waypoints = list(map(Location.full_address, trip.pickup_locations()))
        self.response = client.directions(
            origin=trip.origin.full_address(), destination=trip.dest.full_address(), waypoints=waypoints,
            arrival_time=trip.arrival_time, optimize_waypoints=True)[0]
        self.trip = trip

    def duration_minutes(self):
        return sum(map(lambda leg: leg['duration']['value'], self.response['legs'])) / 60.0

    def distance_miles(self):
        return sum(map(lambda leg: leg['distance']['value'], self.response['legs'])) / 1609.344

    def legs_durations_distances(self):
        return list(map(lambda leg: (leg['duration']['text'], leg['distance']['text']), self.response['legs']))

    def suggested_start_time(self):
        return self.trip.arrival_time - timedelta(minutes=self.duration_minutes())
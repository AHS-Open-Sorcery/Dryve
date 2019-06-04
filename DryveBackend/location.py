from math import hypot


class Location:
    geocode: dict
    lat: float
    long: float
    place_id: str

    def __init__(self, geocode: dict):
        self.geocode = geocode
        self.lat = geocode["geometry"]["location"]["lat"]
        self.long = geocode["geometry"]["location"]["lng"]
        self.place_id = geocode["place_id"]

    def full_address(self):
        return self.geocode['formatted_address']

    def repr(self):
        return self.geocode

    def is_close_to(self, other):
        return hypot(other.lat - self.lat, other.long - self.long) < 0.05

    @staticmethod
    def from_repr(repr: dict):
        return Location(repr)
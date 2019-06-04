class Request:
    # trip: Trip
    # rider: User
    # pickup: Location
    id: str

    def __init__(self, rider, trip, pickup):
        self.rider = rider
        self.trip = trip
        self.pickup = pickup

    def accept(self):
        self.trip.riders.append((self.rider, self.pickup))

    def un_accept(self):
        if (self.rider, self.pickup) in self.trip.riders:
            self.trip.riders.remove((self.rider, self.pickup))

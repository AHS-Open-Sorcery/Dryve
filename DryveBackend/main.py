from flask import *
from route_api import *
from user import *
from google.oauth2 import id_token
from google.auth.transport import requests
from os import urandom
from datetime import *
from db import *
import request as req_pkg
from route_api import *

app = Flask(__name__)
app.secret_key = urandom(32)

db = Database()


@app.context_processor
def logged_in():
    if "name" in session:
        return dict(logged_in=1)  # Return 1 if logged in, otherwise 0
    else:
        return dict(logged_in=0)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/drive", methods={"GET", "POST"})
def drive():

    if not logged_in()['logged_in']:
        session['prev'] = request.url
        return redirect("/login")

    if request.method == "POST":
        # have the user create a new trip
        origin: Location
        destination: Location
        capacity: int
        origin_address = request.form.get("origin")
        destination_address = request.form.get("destination")
        capacity = request.form.get("capacity")
        date = request.form.get("date")
        time = request.form.get("time")

        if isinstance(time, str) and isinstance(date, str):
            time = datetime.time(datetime.strptime(time, "%H:%M"))
            date = datetime.date(datetime.strptime(date, "%m/%d/%Y"))
            dt = datetime.combine(date, time)

        print(dt)
        print(origin_address, destination_address)

        try:
            origin = Location(geocode(origin_address)[0])
            destination = Location(geocode(destination_address)[0])
        except:
            return render_template("drive.html", message="Location(s) not found, Please try again")
        try:
            date_time = datetime.combine(date, time)  # TODO convert to datetime
        except:
            return render_template("drive.html", message="Invalid Time, Please try again")
        print(origin, destination)

        driver = db.get_user(session['name'])
        trip = Trip(origin, destination, driver, capacity, date_time)
        db.store_trip(trip)
        session['trip_id'] = trip.id
        return redirect("/drive/success")

    return render_template("drive.html", message="")


@app.route("/drive/success")
def success():

    if not logged_in()['logged_in']:
        session['prev'] = request.url
        return redirect("/login")

    trip_id = session['trip_id']
    session['trip_id'] = 0
    return render_template("trip_done.html", id=trip_id)


@app.route("/ride", methods={"GET", "POST"})
def ride():

    if not logged_in()['logged_in']:
        session['prev'] = request.url
        return redirect("/login")

    if request.method == "POST":
        # have the user create a new trip
        ride_id = request.form.get("ride_id")
        pickup_address = request.form.get("pickup")
        trip = None

        try:
            trip = db.get_trip(ride_id)
            pass
        except Exception as e:
            return render_template("ride.html", message="Ride not found")
        if trip is None:
            return render_template("ride.html", message="Ride not found")

        pickup_location = None
        try:
            pickup_location = Location(geocode(pickup_address)[0])
        except:
            return render_template("ride.html", message="Location not found, Please try again")

        if trip.is_full():
            return render_template("ride.html", message="Ride is full, unable to request")

        rider: User
        rider = db.get_user(session['name'])

        if db.rider_has_requested(rider, trip):
            return render_template("ride.html", message="You have already requested to join this ride")

        if rider.id == trip.driver.id:
            return render_template("ride.html", message="You may not join your own ride")

        ride_request = req_pkg.Request(rider, trip, pickup_location)
        db.add_request(ride_request)

    return render_template("ride.html", message="", id=request.args.get("id"))


@app.route("/manageTrip")
def manageTrips():

    if not logged_in()['logged_in']:
        session['prev'] = request.url
        return redirect("/login")

    user = db.get_user(session['name'])
    drive_trips = db.trips_of_driver(user)
    ride_trips = db.trips_of_rider(user)
    return render_template("manageAll.html", trips=drive_trips, ride_trips=ride_trips)


@app.route("/manageTrip/<trip_id>")
def manageTrip(trip_id):

    if not logged_in()['logged_in']:
        session['prev'] = request.url
        return redirect("/login")

    trip = db.get_trip(trip_id)
    if trip is None:
        return 'no trip with id ' + trip_id

    try:
        route = Route(trip)
        legs = route.legs_durations_distances()
        waypoints = [trip.driver.name] + list(map(lambda user: user[0].name, trip.riders)) + [trip.dest.full_address()]
        for i in range(len(legs)):
            legs[i] = (legs[i][0], legs[i][1], waypoints[i], waypoints[i + 1])

        return render_template("manage.html", trip_id=trip_id, requests=db.requests_of_trip(trip),
                               maps_url=find_route_url(trip), trip=trip, num_riders=len(trip.riders), riders=trip.riders,
                               start_time=route.suggested_start_time(), distance=route.distance_miles(), time=route.duration_minutes(),
                               legs=legs, is_rider=db.get_user(session["name"]) in trip.rider_users())
    except IndexError:
        db.remove_trip(trip)
        return 'no routes available, trip removed'


@app.route("/accept")
def accept():

    if not logged_in()['logged_in']:
        session['prev'] = request.url
        return redirect("/login")

    req_id = request.args.get("id")

    if req_id is None:
        return 'missing arguments', 422

    req = db.get_request(req_id)
    if req is None:
        return 'bad request ID ' + req_id

    if session['name'] != req.trip.driver.id:
        return 'you are not the driver of this trip, so you can\'t accept', 403

    req.accept()
    db.store_trip(req.trip)
    db.remove_request(req)
    return render_template("accept.html", num_riders=len(req.trip.riders), name=req.rider.name, id=req.trip.id)


@app.route("/deny")
def deny_request():
    req_id = request.args.get("id")
    req = db.get_request(req_id)
    if req is None:
        return 'bad request ID: ' + req_id, 422
    db.remove_request(req)
    return render_template("deny.html", num_riders=len(req.trip.riders), name=req.rider.name, id=req.trip.id)


@app.route("/leave")
def leave_trip():
    trip_id = request.args.get("id")
    user_id = session.get("name")

    if user_id is None:
        session["prev"] = request.url
        return redirect('/login')
    if trip_id is None:
        return 'missing trip id', 422

    trip = db.get_trip(trip_id)
    if trip is None:
        return 'no such trip with id ' + trip_id, 404
    user = db.get_user(user_id)

    if user not in trip.rider_users():
        return 'you are not a rider of this trip', 422

    db.rider_leave_trip(user, trip)
    return 'you successfully left this trip'


@app.route("/kick")
def kick_rider():
    trip_id = request.args.get("trip")
    rider_id = request.args.get("rider")
    user_id = session.get("name")

    if user_id is None:
        session["prev"] = request.url
        return redirect('/login')
    if None in [trip_id, rider_id]:
        return 'missing args', 422

    trip = db.get_trip(trip_id)
    rider = db.get_user(rider_id)
    user = db.get_user(user_id)

    if trip is None:
        return f'no trip with id {trip_id}', 422
    if rider is None:
        return f'no such rider', 404

    if rider not in trip.rider_users():
        return 'such rider not riding in such trip', 422
    if user != trip.driver:
        return 'you are not the driver, you cannot kick riders', 403

    trip.remove_rider(rider)
    db.store_trip(trip)
    return f'you successfully kicked {rider.name} out of trip {trip.id}'

# TODO use query_trip


@app.route("/login", methods={"GET", "POST"})
def login():

    if request.method == "POST":

        try:
            # Specify the CLIENT_ID of the app that accesses the backend:
            idinfo = id_token.verify_oauth2_token(request.form["id_token"], requests.Request(),
                                                  "774990506311-e1ot6iitq72uvnk4f5stsc1rfjqr8le6.apps.googleusercontent.com")

            # Or, if multiple clients access the backend server:
            # idinfo = id_token.verify_oauth2_token(token, requests.Request())
            # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
            #     raise ValueError('Could not verify audience.')

            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            # If auth request is from a G Suite domain:
            # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
            #     raise ValueError('Wrong hosted domain.')

            # ID token is valid. Get the user's Google Account ID from the decoded token.
            userid = idinfo['sub']
            session['name'] = userid
            user = User(idinfo['name'], userid)
            db.store_user(user)
            prev = session.get('prev')
            return redirect(prev if prev is not None else '/drive')
        except ValueError:
            # Invalid token
            pass

    return render_template("login.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/logout")
def logout():
    session.clear()
    return render_template("logout.html")


if __name__ == "__main__":
    app.run()

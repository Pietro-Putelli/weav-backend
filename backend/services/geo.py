from django.contrib.gis.geos import Point
from haversine import haversine, Unit
import requests

from django.config import MAP_BOX_ACCESS_TOKEN
from services.utils import safe_list_get


def get_distance_from(venue_point, user_point):
    venue_position = [venue_point.x, venue_point.y]
    user_position = [user_point.x, user_point.y]

    distance = haversine(venue_position, user_position, unit=Unit.METERS)

    if distance < 1000:
        return f"{round(distance)} m"
    return f"{round(distance / 1000, 1)} km"


def get_position(params):
    city = params.get("city")
    longitude = float(params.get("longitude"))
    latitude = float(params.get("latitude"))

    return city, [longitude, latitude]


def create_point(data):
    coordinate = data.get("coordinate")
    latitude = coordinate.get("latitude")
    longitude = coordinate.get("longitude")
    return Point(longitude, latitude)


def get_place_id(coordinate):
    response = requests.get(
        f"https://api.mapbox.com/geocoding/v5/mapbox.places/{coordinate.x}"
        f",{coordinate.y}.json?types=place&limit=1&access_token={MAP_BOX_ACCESS_TOKEN}"
    )

    data = response.json()
    features = data.get("features")

    place = safe_list_get(features, 0)

    if place is not None:
        return place.get("id")

    return None

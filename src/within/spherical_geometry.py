from math import atan2, cos, degrees, radians, sin, sqrt
from typing import Tuple

EARTH_RADIUS = 6371  # km (average)


def great_circle_halfway_point(
    start_latitude: float,
    start_longitude: float,
    end_latitude: float,
    end_longitude: float,
) -> Tuple[float, float]:
    """
    Half-way point along a great circle path between the two points.
    Return (latitude, longitude) in degrees.
    """
    start_lat = radians(start_latitude)
    end_lat = radians(end_latitude)
    start_long = radians(start_longitude)
    long_delta = radians(end_longitude - start_longitude)

    Bx = cos(end_lat) * cos(long_delta)
    By = cos(end_lat) * sin(long_delta)
    mid_lat = atan2(
        sin(start_lat) + sin(end_lat), sqrt((cos(start_lat) + Bx) ** 2 + By**2)
    )
    mid_long = start_long + atan2(By, cos(start_lat) + Bx)
    return (degrees(mid_lat), degrees(mid_long))


def great_circle_distance(
    start_latitude: float,
    start_longitude: float,
    end_latitude: float,
    end_longitude: float,
    radius: float = EARTH_RADIUS,
) -> float:
    """
    This uses the haversine formula to calculate the great-circle distance
    between two points on a sphere.
    """
    start_lat = radians(start_latitude)
    end_lat = radians(end_latitude)
    lat_delta = radians(start_latitude - end_latitude)
    long_delta = radians(end_longitude - start_longitude)

    haversine = (
        sin(lat_delta / 2) ** 2
        + cos(start_lat) * cos(end_lat) * sin(long_delta / 2) ** 2
    )
    fractional_dist = 2 * atan2(sqrt(haversine), sqrt(1 - haversine))

    return fractional_dist * radius


def get_bearing(
    start_latitude: float,
    start_longitude: float,
    end_latitude: float,
    end_longitude: float,
) -> float:
    """
    Great circle bearing between two coordinates
    Input and output are in degrees [0; 360[
    """
    start_latitude = radians(start_latitude)
    end_latitude = radians(end_latitude)
    longitude_delta = radians(end_longitude - start_longitude)

    x = sin(longitude_delta) * cos(end_latitude)
    y = cos(start_latitude) * sin(end_latitude) - sin(start_latitude) * cos(
        end_latitude
    ) * cos(longitude_delta)
    bearing = degrees(atan2(x, y))

    return (bearing + 360) % 360


def get_cardinal_direction(bearing_degrees: float) -> str:
    """Bearing in degrees to one of 16 cardinal directions"""
    if bearing_degrees < (1 - 0.5) / 16 * 360:
        return "N"
    elif bearing_degrees < (2 - 0.5) / 16 * 360:
        return "NNE"
    elif bearing_degrees < (3 - 0.5) / 16 * 360:
        return "NE"
    elif bearing_degrees < (4 - 0.5) / 16 * 360:
        return "ENE"
    elif bearing_degrees < (5 - 0.5) / 16 * 360:
        return "E"
    elif bearing_degrees < (6 - 0.5) / 16 * 360:
        return "ESE"
    elif bearing_degrees < (7 - 0.5) / 16 * 360:
        return "SE"
    elif bearing_degrees < (8 - 0.5) / 16 * 360:
        return "SSE"
    elif bearing_degrees < (9 - 0.5) / 16 * 360:
        return "S"
    elif bearing_degrees < (10 - 0.5) / 16 * 360:
        return "SSW"
    elif bearing_degrees < (11 - 0.5) / 16 * 360:
        return "SW"
    elif bearing_degrees < (12 - 0.5) / 16 * 360:
        return "WSW"
    elif bearing_degrees < (13 - 0.5) / 16 * 360:
        return "W"
    elif bearing_degrees < (14 - 0.5) / 16 * 360:
        return "WNW"
    elif bearing_degrees < (15 - 0.5) / 16 * 360:
        return "NW"
    elif bearing_degrees < (16 - 0.5) / 16 * 360:
        return "NNW"
    return "N"


def get_turning_instruction(current_bearing: float, next_bearing: float) -> str:
    turning_degrees = (next_bearing - current_bearing + 360) % 360
    if turning_degrees > 180:
        turning_degrees = turning_degrees - 360
    side = "left" if turning_degrees < 0 else "right"
    if abs(turning_degrees) < 30:
        return "Continue straight"
    if abs(turning_degrees) < 60:
        return f"Bear {side}"
    if abs(turning_degrees) < 110:
        return f"Turn {side}"
    if abs(turning_degrees) < 170:
        return f"Turn a very sharp {side}"
    return "Make a U-turn"

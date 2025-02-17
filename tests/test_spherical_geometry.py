from math import pi

import pytest

from within.spherical_geometry import (
    EARTH_RADIUS,
    get_bearing,
    get_cardinal_direction,
    get_turning_instruction,
    great_circle_distance,
    great_circle_halfway_point,
)


def test_great_circle_halfway_point() -> None:
    assert great_circle_halfway_point(-10, 10, 10, -10) == (0, 0)
    assert great_circle_halfway_point(89, -90, 89, 90) == (90, 0)


def test_great_circle_distance() -> None:
    quarter_unit_circle_dist = great_circle_distance(0, 0, 0, 90, radius=1)
    assert round(quarter_unit_circle_dist, 10) == round(pi / 2, 10)
    quarter_earth_circle_dist = great_circle_distance(0, 0, 0, 90)
    assert quarter_earth_circle_dist == quarter_unit_circle_dist * EARTH_RADIUS


@pytest.mark.parametrize(
    "start_lat,start_long,end_lat,end_long,exp_bearing",
    [
        (0, 0, 30, 0, 0),
        (0, 0, 0, 30, 90),
        (0, 0, -30, 0, 180),
        (0, 0, 0, -30, 270),
    ],
)
def test_get_bearing(
    start_lat: float,
    start_long: float,
    end_lat: float,
    end_long: float,
    exp_bearing: float,
) -> None:
    bearing = get_bearing(start_lat, start_long, end_lat, end_long)
    assert bearing == exp_bearing


@pytest.mark.parametrize(
    "bearing_degrees,exp_cardinal",
    [
        (0, "N"),
        (22, "NNE"),
        (45, "NE"),
        (67, "ENE"),
        (90, "E"),
        (112, "ESE"),
        (135, "SE"),
        (159, "SSE"),
        (180, "S"),
        (200, "SSW"),
        (225, "SW"),
        (250, "WSW"),
        (270, "W"),
        (292, "WNW"),
        (315, "NW"),
        (340, "NNW"),
        (359, "N"),
    ],
)
def test_get_cardinal_direction(
    bearing_degrees: float,
    exp_cardinal: str,
) -> None:
    cardinal = get_cardinal_direction(bearing_degrees)
    assert cardinal == exp_cardinal


@pytest.mark.parametrize("start_bearing", [0, 45, 90, 180, 227, 330, 359])
@pytest.mark.parametrize(
    "turning_degrees,exp_direction",
    [
        (0, "Continue straight"),
        (90, "Turn right"),
        (115, "Turn a very sharp right"),
        (245, "Turn a very sharp left"),
        (181, "Make a U-turn"),
        (270, "Turn left"),
        (359, "Continue straight"),
    ],
)
def test_get_turning_instruction(
    start_bearing: float, turning_degrees: float, exp_direction: str
) -> None:
    next_bearing = start_bearing + turning_degrees
    direction = get_turning_instruction(start_bearing, next_bearing)
    assert direction == exp_direction

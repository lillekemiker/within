# TODO: mock API calls


import pytest

from within.address import Address
from within.routing import Route, Routing


@pytest.fixture
def starting_point() -> Address:
    return Address("Madison Square Garden", (40.750504, -73.993438))


@pytest.fixture
def destination() -> Address:
    return Address("Battery Park", (40.7048, -74.0173))


def test_route_as_the_crow_flies_distance_km(
    starting_point: Address, destination: Address
) -> None:
    routing = Routing(
        starting_point=starting_point,
        destination=destination,
        transport_mode="walk",
    )
    assert round(routing.as_the_crow_flies_distance_km, 3) == 5.465


def test_midway_coordinate(starting_point: Address, destination: Address) -> None:
    routing = Routing(
        starting_point=starting_point,
        destination=destination,
        transport_mode="walk",
    )
    mid_lat, mid_long = routing.midway_coordinate
    assert (round(mid_lat, 6), round(mid_long, 6)) == (40.727653, -74.005373)


def test_routing_shortest_routes(starting_point: Address, destination: Address) -> None:
    routing = Routing(
        starting_point=starting_point,
        destination=destination,
        transport_mode="drive",
    )
    shortest_routes = routing.shortest_routes(2)
    assert len(shortest_routes) == 2
    assert all(isinstance(route, Route) for route in shortest_routes)
    assert shortest_routes[0].total_length_m <= shortest_routes[1].total_length_m
    assert 6000 <= shortest_routes[0].total_length_m <= 6200
    assert all(route.description[0].startswith("Head ") for route in shortest_routes)
    assert all(
        route.description[-1] == "Arriving at your destination."
        for route in shortest_routes
    )

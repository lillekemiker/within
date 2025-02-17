from typing import Iterator
from unittest.mock import Mock, patch

import pytest

from within.cli import main


@pytest.fixture
def mock_Address() -> Iterator[Mock]:
    address = Mock(spec_set=["location_description", "latitude", "longitude"])
    address.location_description = "test"
    address.latitude = 1.2
    address.longitude = 3.4
    with patch("within.cli.Address") as mock_address_class:
        mock_address_class.return_value = address
        yield mock_address_class


@pytest.fixture
def mock_Routing() -> Iterator[Mock]:
    route = Mock(spec_set=["description", "total_length_m"])
    route.description = "test"
    route.total_length_m = 1000.0
    routing = Mock(spec_set=["shortest_routes"])
    routing.shortest_routes.return_value = [route]
    with patch("within.cli.Routing") as mock_routing_class:
        mock_routing_class.return_value = routing
        yield mock_routing_class


def test_main(mock_Address: Mock, mock_Routing: Mock) -> None:
    cli_args = [
        "--start",
        "start_address",
        "--destination",
        "end_address",
        "--transport-mode",
        "drive",
        "--num-suggestions",
        "1",
    ]
    with patch("sys.argv", ["cli.py", *cli_args]):
        main()

    assert mock_Address.call_count == 2
    assert mock_Address.call_args_list[0][0][0] == "start_address"
    assert mock_Address.call_args_list[1][0][0] == "end_address"

    start_address = end_address = mock_Address.return_value
    assert mock_Routing.call_count == 1
    assert mock_Routing.call_args[0] == (start_address, end_address, "drive")

    routing = mock_Routing.return_value
    assert routing.shortest_routes.call_count == 1
    assert routing.shortest_routes.call_args[0][0] == 1

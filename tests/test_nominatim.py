import json
from pathlib import Path
from typing import Iterator
from unittest.mock import Mock, create_autospec, patch

import pytest
from requests import Response

from within.nominatim import NOMINATIM_ENDPOINT, REQUEST_TIMEOUT, coords_from_addresses


@pytest.fixture
def mock_response() -> Mock:
    response: Mock = create_autospec(Response, instance=True)
    response.json.return_value = [
        {
            "lat": 40.7829932,
            "lon": -73.95892501810057,
        }
    ]
    response.status_code = 200
    return response


@pytest.fixture
def no_cache() -> Iterator[None]:
    with patch("within.nominatim.USE_CACHE", False):
        yield


def test_coords_from_address(mock_response: Mock, no_cache: None) -> None:
    with patch("within.nominatim.sleep") as mock_sleep:
        with patch("within.nominatim.requests.get") as mock_get:
            mock_get.return_value = mock_response
            resp = coords_from_addresses(["1071 5th Ave, New York", "Guggenheim"])
    assert resp[0] == resp[1] == (40.7829932, -73.95892501810057)
    assert mock_sleep.call_count == 1
    assert mock_sleep.call_args[0][0] == 1
    assert mock_get.call_count == 2
    assert mock_get.call_args[0][0] == NOMINATIM_ENDPOINT
    assert mock_get.call_args[1]["params"] == {
        "q": "Guggenheim",
        "format": "json",
        "limit": 1,
        "dedupe": 0,
    }
    assert mock_get.call_args[1]["timeout"] == REQUEST_TIMEOUT


def test_coords_from_address_uses_cache(mock_response: Mock, tmp_path: Path) -> None:
    cache_file_path = tmp_path / "cache.json"
    with patch("within.nominatim.CACHE_FILE_PATH", cache_file_path):
        with patch("within.nominatim.sleep") as mock_sleep:
            with patch("within.nominatim.requests.get") as mock_get:
                mock_get.return_value = mock_response
                # saves to cache
                resp = coords_from_addresses(["1071 5th Ave, New York", "Guggenheim"])
                # reads from cache
                resp2 = coords_from_addresses(["1071 5th Ave, New York", "Guggenheim"])
    assert resp == resp2
    assert resp[0] == resp[1] == (40.7829932, -73.95892501810057)
    assert mock_sleep.call_count == 1  # Should not be called when reading from cache
    assert mock_sleep.call_args[0][0] == 1
    assert mock_get.call_count == 2  # Not 4 since the last 2 were cached
    assert mock_get.call_args[0][0] == NOMINATIM_ENDPOINT
    assert mock_get.call_args[1]["params"] == {
        "q": "Guggenheim",
        "format": "json",
        "limit": 1,
        "dedupe": 0,
    }
    assert mock_get.call_args[1]["timeout"] == REQUEST_TIMEOUT
    # Check what was written to cache
    assert cache_file_path.exists()
    with cache_file_path.open("r") as fh:
        cached_data = json.load(fh)
    assert cached_data == {
        "1071 5th Ave, New York": mock_response.json.return_value,
        "Guggenheim": mock_response.json.return_value,
    }

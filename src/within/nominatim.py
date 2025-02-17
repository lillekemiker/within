import json
from pathlib import Path
from time import sleep
from typing import Dict, List, Optional, Tuple

import requests
from typing_extensions import TypedDict

NOMINATIM_ENDPOINT = "https://nominatim.openstreetmap.org/search"
REQUEST_TIMEOUT = 2  # seconds
RETRY_PAUSE = 20  # seconds
CACHE_FILE_PATH = Path(__file__).parent / "nominatim_cache.json"
USE_CACHE = True


class ResponseJSONType(TypedDict):
    lat: float
    lon: float


def _read_cache(address: str) -> Optional[List[ResponseJSONType]]:
    if not CACHE_FILE_PATH.exists():
        return None
    with CACHE_FILE_PATH.open("r") as fh:
        cached_data: Dict[str, List[ResponseJSONType]] = json.load(fh)
    return cached_data.get(address, None)


def _write_cache(address: str, result: List[ResponseJSONType]) -> None:
    cached_data: Dict[str, List[ResponseJSONType]]
    if CACHE_FILE_PATH.exists():
        with CACHE_FILE_PATH.open("r") as fh:
            cached_data = json.load(fh)
    else:
        CACHE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cached_data = {}
    cached_data[address] = result
    with CACHE_FILE_PATH.open("w") as fh:
        json.dump(cached_data, fh, sort_keys=True, indent=2)


def _coords_from_response(
    response: List[ResponseJSONType],
) -> Optional[Tuple[float, float]]:
    if not response:
        return None
    assert (
        "lat" in response[0]
    ), f"Response does not contain lat key for latitude: {response[0]}"
    assert (
        "lon" in response[0]
    ), f"Response does not contain lon key for longitude: {response[0]}"
    return (response[0]["lat"], response[0]["lon"])


def _coords_from_address(
    address: str,
    retry_count: int = 3,
) -> Tuple[Tuple[float, float] | None, bool]:
    """
    Send a HTTP GET request to the Nominatim API and return response.
    Returns ((lat, long), was_read_from_cache)
    """
    if USE_CACHE:
        cached_result = _read_cache(address)
        if cached_result is not None:
            return _coords_from_response(cached_result), True

    # Nominative wants custom headers
    headers = dict(requests.utils.default_headers())
    headers.update(
        {
            "User-Agent": "Toy street routing project",
            "referer": "https://github.com/lillekemiker/within",
            "Accept-Language": "en",
        }
    )
    params: Dict[str, str | int] = {
        "q": address,
        "format": "json",
        "limit": 1,
        "dedupe": 0,
    }

    # transmit the HTTP GET request
    response = requests.get(
        NOMINATIM_ENDPOINT,
        params=params,
        timeout=REQUEST_TIMEOUT,
        headers=headers,
    )

    # retry on 429 and 504 errors
    if response.status_code in (429, 504):
        print(
            f"{NOMINATIM_ENDPOINT} responded {response.status_code} {response.reason}"
        )
        if retry_count > 0:
            print(f"Retrying {RETRY_PAUSE} seconds")
            sleep(RETRY_PAUSE)
            return _coords_from_address(address, retry_count=retry_count - 1)
        else:
            raise Exception(f"Failed to parse address input: {address}")

    try:
        response_json: Optional[List[ResponseJSONType]] = response.json()
    except requests.JSONDecodeError:
        print(
            f"{NOMINATIM_ENDPOINT} responded {response.status_code} {response.reason}: "
            f"{response.text}"
        )
        if retry_count > 0:
            print(f"Retrying {RETRY_PAUSE} seconds")
            sleep(RETRY_PAUSE)
            return _coords_from_address(address, retry_count=retry_count - 1)
        else:
            raise Exception(f"Failed to parse address input: {address}")

    if not isinstance(response_json, list):
        # Not retrying because this is not expected to be a transient error.
        print("Nominatim API did not return a list of results.")
        raise Exception(f"Failed to parse address input: {address}")

    if USE_CACHE:
        _write_cache(address, response_json)
    return _coords_from_response(response_json), False


def coords_from_addresses(
    addresses: List[str], retry_count: int = 3
) -> List[Optional[Tuple[float, float]]]:
    """
    Takes a list of addresses and returns a list of their coordinates or None's
    for addresses that could not be resolved.
    """
    result: List[Optional[Tuple[float, float]]] = []
    for idx, address in enumerate(addresses):
        try:
            coord, was_read_from_cache = _coords_from_address(address, retry_count)
            result.append(coord)
        except Exception:
            result.append(None)
        if not was_read_from_cache and not idx == len(addresses) - 1:
            # Public API requests are limited to 1 per second
            sleep(1)
    return result

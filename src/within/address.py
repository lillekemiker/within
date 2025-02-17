# Parsing address input
import os
from typing import Optional, Tuple

from openai import OpenAI
from pydantic import BaseModel

from within.nominatim import coords_from_addresses


class GeographicLocation(BaseModel):
    longitude: float
    latitude: float


class Address:
    MODEL = "gpt-4o-mini"
    location_description: str
    _parsed_location: Optional[GeographicLocation] = None

    def __init__(
        self,
        location_description: str,
        coordinate: Optional[Tuple[float, float]] = None,
    ) -> None:
        self.location_description = location_description
        if coordinate is not None:
            self._parsed_location = GeographicLocation(
                latitude=coordinate[0], longitude=coordinate[1]
            )

    @property
    def latitude(self) -> float:
        self.parse_location_description()
        assert (
            self._parsed_location is not None
        ), f"Failed to parse address {self.location_description}"
        return self._parsed_location.latitude

    @property
    def longitude(self) -> float:
        self.parse_location_description()
        assert (
            self._parsed_location is not None
        ), f"Failed to parse address {self.location_description}"
        return self._parsed_location.longitude

    def parse_location_description(self) -> None:
        if self._parsed_location is not None:
            return
        coord = coords_from_addresses([self.location_description])[0]
        if coord is not None:
            self._parsed_location = GeographicLocation(
                latitude=coord[0], longitude=coord[1]
            )
            return
        # Nominatim parsing failed. Try OpenAI as fallback
        self.parse_location_description_with_OpenAI()

    def parse_location_description_with_OpenAI(self) -> None:
        if not os.getenv("OPENAI_API_KEY"):
            raise Exception(
                "You need to set the OPENAI_API_KEY environment variable for "
                "parsing address input with OpenAI"
            )
        client = OpenAI()
        response = client.beta.chat.completions.parse(
            messages=[
                {
                    "role": "developer",
                    "content": "You are an expert on geographical locations",
                },
                {
                    "role": "user",
                    "content": (
                        "What is the longitude, latitude of "
                        f"this location: {self.location_description}"
                    ),
                },
            ],
            model=self.MODEL,
            response_format=GeographicLocation,
        )
        self._parsed_location = response.choices[0].message.parsed

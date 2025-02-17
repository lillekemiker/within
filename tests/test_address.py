import os
from typing import Iterator
from unittest.mock import patch

import pytest
from openai.types.chat.parsed_chat_completion import (
    ParsedChatCompletion,
    ParsedChatCompletionMessage,
    ParsedChoice,
)
from openai.types.completion_usage import (
    CompletionTokensDetails,
    CompletionUsage,
    PromptTokensDetails,
)

from within.address import Address, GeographicLocation


@pytest.fixture()
def mock_openai_api_key(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    with patch.dict(os.environ, clear=True):
        monkeypatch.setenv("OPENAI_API_KEY", "fake_test_key")
        yield


@pytest.fixture
def mock_openai_coord_response() -> ParsedChatCompletion[GeographicLocation]:
    return ParsedChatCompletion[GeographicLocation](
        id="chatcmpl-B1KxiPxubHgqVx2czjxobR9IRt3yE",
        choices=[
            ParsedChoice[GeographicLocation](
                finish_reason="stop",
                index=0,
                logprobs=None,
                message=ParsedChatCompletionMessage[GeographicLocation](
                    content='{"longitude":-73.993438,"latitude":40.750504}',
                    refusal=None,
                    role="assistant",
                    audio=None,
                    function_call=None,
                    tool_calls=None,
                    parsed=GeographicLocation(longitude=-73.993438, latitude=40.750504),
                ),
            )
        ],
        created=1739658606,
        model="gpt-4o-mini-2024-07-18",
        object="chat.completion",
        service_tier="default",
        system_fingerprint="fp_00428b782a",
        usage=CompletionUsage(
            completion_tokens=17,
            prompt_tokens=80,
            total_tokens=97,
            completion_tokens_details=CompletionTokensDetails(
                accepted_prediction_tokens=0,
                audio_tokens=0,
                reasoning_tokens=0,
                rejected_prediction_tokens=0,
            ),
            prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0),
        ),
    )


@pytest.fixture
def mock_openai_address_response() -> ParsedChatCompletion[None]:
    return ParsedChatCompletion[None](
        id="chatcmpl-B1zRYHBSuLj8XI7BCNjFBbq1D2iXX",
        choices=[
            ParsedChoice[None](
                finish_reason="stop",
                index=0,
                logprobs=None,
                message=ParsedChatCompletionMessage[None](
                    content="Madison Square Garden, 4 Pennsylvania Plaza, New York, NY 10001, USA.",
                    refusal=None,
                    role="assistant",
                    audio=None,
                    function_call=None,
                    tool_calls=None,
                    parsed=None,
                ),
            )
        ],
        created=1739814216,
        model="gpt-4o-mini-2024-07-18",
        object="chat.completion",
        service_tier="default",
        system_fingerprint="fp_13eed4fce1",
        usage=CompletionUsage(
            completion_tokens=21,
            prompt_tokens=38,
            total_tokens=59,
            completion_tokens_details=CompletionTokensDetails(
                accepted_prediction_tokens=0,
                audio_tokens=0,
                reasoning_tokens=0,
                rejected_prediction_tokens=0,
            ),
            prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0),
        ),
    )


def test_address_parsing_nominatim(
    mock_openai_coord_response: ParsedChatCompletion[GeographicLocation],
    mock_openai_api_key: None,
) -> None:
    with patch("within.address.coords_from_addresses") as mock_cfa:
        # Make coords_from_addresses fail
        mock_cfa.return_value = [(40.750504, -73.993438)]
        with patch("within.address.OpenAI") as mock_OpenAI:
            mock_openai_instance = mock_OpenAI.return_value
            mock_openai_instance.beta.chat.completions.parse.return_value = (
                mock_openai_coord_response
            )
            address = Address("Madison Square Garden")
            assert address.longitude == -73.993438
            assert address.latitude == 40.750504
            assert mock_cfa.call_count == 1
            assert mock_cfa.call_args[0][0] == ["Madison Square Garden"]

            assert mock_openai_instance.beta.chat.completions.parse.call_count == 0


def test_address_sanitized_address(
    mock_openai_address_response: ParsedChatCompletion[None],
    mock_openai_api_key: None,
) -> None:
    address = Address("Madison Square Garden")
    expected_sanitized = (
        "Madison Square Garden, 4 Pennsylvania Plaza, New York, NY 10001, USA."
    )
    with patch("within.address.OpenAI") as mock_OpenAI:
        mock_openai_instance = mock_OpenAI.return_value
        mock_openai_instance.beta.chat.completions.parse.return_value = (
            mock_openai_address_response
        )
        sanitized = address.sanitized_address
    assert sanitized == expected_sanitized
    assert mock_openai_instance.beta.chat.completions.parse.call_count == 1
    call_kwargs = mock_openai_instance.beta.chat.completions.parse.call_args[1]
    assert call_kwargs == {
        "messages": [
            {
                "role": "developer",
                "content": "You are an expert on geographical locations",
            },
            {
                "role": "user",
                "content": (
                    "What is the mailing address of this location: Madison "
                    "Square Garden\nAnswer precisely with just the address."
                ),
            },
        ],
        "model": address.MODEL,
    }


def test_address_parsing_nominatim_and_sanitized_address(
    mock_openai_address_response: ParsedChatCompletion[None],
    mock_openai_api_key: None,
) -> None:
    with patch("within.address.coords_from_addresses") as mock_cfa:
        # Make coords_from_addresses fail
        mock_cfa.side_effect = [[None], [(40.750504, -73.993438)]]
        with patch("within.address.OpenAI") as mock_OpenAI:
            mock_openai_instance = mock_OpenAI.return_value
            mock_openai_instance.beta.chat.completions.parse.return_value = (
                mock_openai_address_response
            )
            address = Address("Madison Square Garden")
            assert address.longitude == -73.993438
            assert address.latitude == 40.750504
            assert mock_cfa.call_count == 2
            assert mock_cfa.call_args_list[0][0][0] == ["Madison Square Garden"]
            assert mock_cfa.call_args_list[1][0][0] == [
                "Madison Square Garden, 4 Pennsylvania Plaza, New York, NY 10001, USA."
            ]

            assert mock_openai_instance.beta.chat.completions.parse.call_count == 1
            call_kwargs = mock_openai_instance.beta.chat.completions.parse.call_args[1]
            assert call_kwargs == {
                "messages": [
                    {
                        "role": "developer",
                        "content": "You are an expert on geographical locations",
                    },
                    {
                        "role": "user",
                        "content": (
                            "What is the mailing address of this location: Madison "
                            "Square Garden\nAnswer precisely with just the address."
                        ),
                    },
                ],
                "model": address.MODEL,
            }


def test_address_parsing_openai_fallback(
    mock_openai_address_response: ParsedChatCompletion[None],
    mock_openai_coord_response: ParsedChatCompletion[GeographicLocation],
    mock_openai_api_key: None,
) -> None:
    with patch("within.address.coords_from_addresses") as mock_cfa:
        # Make coords_from_addresses fail
        mock_cfa.return_value = [None]
        with patch("within.address.OpenAI") as mock_OpenAI:
            mock_openai_instance = mock_OpenAI.return_value
            mock_openai_instance.beta.chat.completions.parse.side_effect = (
                mock_openai_address_response,
                mock_openai_coord_response,
            )
            address = Address("Madison Square Garden")
            assert address.longitude == -73.993438
            assert address.latitude == 40.750504
            assert mock_cfa.call_count == 2
            assert mock_cfa.call_args_list[0][0][0] == ["Madison Square Garden"]
            assert mock_cfa.call_args_list[1][0][0] == [
                "Madison Square Garden, 4 Pennsylvania Plaza, New York, NY 10001, USA."
            ]
            assert mock_openai_instance.beta.chat.completions.parse.call_count == 2
            args_list = mock_openai_instance.beta.chat.completions.parse.call_args_list
            assert args_list[0][1] == {
                "messages": [
                    {
                        "role": "developer",
                        "content": "You are an expert on geographical locations",
                    },
                    {
                        "role": "user",
                        "content": (
                            "What is the mailing address of this location: Madison "
                            "Square Garden\nAnswer precisely with just the address."
                        ),
                    },
                ],
                "model": address.MODEL,
            }
            assert args_list[1][1] == {
                "messages": [
                    {
                        "role": "developer",
                        "content": "You are an expert on geographical locations",
                    },
                    {
                        "role": "user",
                        "content": (
                            "What is the longitude, latitude of this location: "
                            "Madison Square Garden"
                        ),
                    },
                ],
                "model": address.MODEL,
                "response_format": GeographicLocation,
            }


def test_address_coordinate_override() -> None:
    with patch("within.address.OpenAI") as mock_OpenAI:
        mock_openai_instance = mock_OpenAI.return_value
        address = Address("Madison Square Garden", (3.3, 15.5))
        assert address.longitude == 15.5
        assert address.latitude == 3.3
        assert mock_openai_instance.beta.chat.completions.parse.call_count == 0

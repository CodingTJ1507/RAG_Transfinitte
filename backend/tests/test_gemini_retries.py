from unittest.mock import MagicMock, patch
import pytest
import httpx
from google.genai import errors

from app.config import settings
from app.models.schemas import InvestigationRequest
from app.services.gemini import call_with_retries


def test_429_then_success_returns_result():
    call = MagicMock(side_effect=[errors.ClientError(429, "Resource exhausted"), "success_value"])
    with patch("time.sleep") as mock_sleep:
        result = call_with_retries(call)
    assert result == "success_value"
    assert call.call_count == 2
    mock_sleep.assert_called_once_with(1.0)


def test_400_is_not_retried():
    call = MagicMock(side_effect=errors.ClientError(400, "Bad Request"))
    with patch("time.sleep") as mock_sleep:
        with pytest.raises(errors.ClientError) as exc_info:
            call_with_retries(call)
    assert exc_info.value.code == 400
    assert call.call_count == 1
    mock_sleep.assert_not_called()


def test_429_exhausts_retries_and_respects_budget():
    call = MagicMock(side_effect=errors.ClientError(429, "Rate limit"))
    slept_durations = []

    simulated_time = [100.0]

    def fake_monotonic():
        return simulated_time[0]

    def fake_sleep(d):
        slept_durations.append(d)
        simulated_time[0] += d

    with patch("time.monotonic", side_effect=fake_monotonic), patch("time.sleep", side_effect=fake_sleep):
        with pytest.raises(errors.ClientError):
            call_with_retries(call)

    assert call.call_count == settings.GEMINI_MAX_RETRIES + 1
    assert len(slept_durations) == settings.GEMINI_MAX_RETRIES
    assert sum(slept_durations) <= settings.GEMINI_RETRY_BUDGET_SECONDS


def test_429_stops_when_budget_exceeded():
    call = MagicMock(side_effect=errors.ClientError(429, "Rate limit"))
    simulated_time = [100.0]

    def fake_monotonic():
        return simulated_time[0]

    def fake_sleep(d):
        simulated_time[0] += settings.GEMINI_RETRY_BUDGET_SECONDS + 5

    with patch("time.monotonic", side_effect=fake_monotonic), patch("time.sleep", side_effect=fake_sleep):
        with pytest.raises(errors.ClientError):
            call_with_retries(call)

    assert call.call_count == 2


def test_value_error_with_503_in_text_is_not_retried():
    call = MagicMock(side_effect=ValueError("503 Service Unavailable fake message"))
    with patch("time.sleep") as mock_sleep:
        with pytest.raises(ValueError) as exc_info:
            call_with_retries(call)
    assert "503" in str(exc_info.value)
    assert call.call_count == 1
    mock_sleep.assert_not_called()


def test_httpx_timeout_is_retried():
    call = MagicMock(side_effect=[httpx.ReadTimeout("read timeout"), "recovered"])
    with patch("time.sleep") as mock_sleep:
        result = call_with_retries(call)
    assert result == "recovered"
    assert call.call_count == 2
    mock_sleep.assert_called_once_with(1.0)


def test_investigation_request_whitespace_only_rejected():
    with pytest.raises(ValueError, match="whitespace"):
        InvestigationRequest(query="   \t\n  ")


def test_describe_image_asks_for_a_list_of_lines():
    from google.genai import types

    from app.services.gemini import describe_image

    client = MagicMock()
    client.models.generate_content.return_value = MagicMock(text='{"description": "d", "visible_text": ["a"]}')
    with patch("app.services.gemini.get_gemini_client", return_value=client):
        assert describe_image(b"png", "image/png") == {"description": "d", "visible_text": ["a"]}
    schema = client.models.generate_content.call_args.kwargs["config"].response_schema
    assert schema.properties["visible_text"].type == types.Type.ARRAY

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for the translator ToolboxClient — endpoints, retry policy and errors inherited from django_utils."""

import json
from decimal import Decimal
from unittest.mock import patch

import httpx
import pytest
import respx
from django_utils.toolbox import ToolboxClient as BaseToolboxClient

from django_utils_translator.clients.errors import (
    ToolboxAuthError,
    ToolboxBudgetExceededError,
    ToolboxConnectionError,
    ToolboxNotConfiguredError,
    ToolboxNotFoundError,
    ToolboxRateLimitError,
    ToolboxServerError,
    ToolboxValidationError,
)
from django_utils_translator.clients.toolbox import _DEFAULT_PROVIDER, ToolboxClient

BASE_URL = "https://toolbox.test.internal"
CHANNEL = "test-channel"
TRANSLATOR_PREFIX = f"{BASE_URL}/api/ai-translator/v2/admin/{CHANNEL}"


@pytest.fixture()
def mock_httpx():
    with respx.mock:
        yield


# --- Init validation ---


class TestClientInit:
    def test_rejects_empty_base_url(self, settings):
        settings.AI_TOOLBOX_BASE_URL = ""
        with pytest.raises(ToolboxNotConfiguredError):
            ToolboxClient(CHANNEL)

    def test_rejects_empty_api_key(self, settings):
        settings.AI_TOOLBOX_API_KEY = ""
        with pytest.raises(ToolboxNotConfiguredError):
            ToolboxClient(CHANNEL)

    def test_subclasses_shared_client(self):
        assert issubclass(ToolboxClient, BaseToolboxClient)

    def test_rejects_invalid_channel_idx(self):
        with pytest.raises(ValueError, match="Invalid channel_idx"):
            ToolboxClient("../../admin")

    def test_rejects_channel_with_slashes(self):
        with pytest.raises(ValueError, match="Invalid channel_idx"):
            ToolboxClient("foo/bar")

    def test_accepts_valid_channel_idx(self):
        client = ToolboxClient("my-channel_123")
        assert client._channel_idx == "my-channel_123"
        client.close()


# --- Context manager ---


class TestContextManager:
    def test_enter_returns_self(self):
        with ToolboxClient(CHANNEL) as client:
            assert isinstance(client, ToolboxClient)

    def test_close_called_on_exit(self):
        client = ToolboxClient(CHANNEL)
        with patch.object(client, "close") as mock_close:
            with client:
                pass
            mock_close.assert_called_once()


# --- Successful requests ---


class TestEstimateSingleBatch:
    def test_returns_estimate(self, mock_httpx):
        expected = {"per_language": [{"language": "DE", "total_chars": 100}], "total_cost_usd": "0.50"}
        respx.post(f"{TRANSLATOR_PREFIX}/estimate/").mock(return_value=httpx.Response(200, json=expected))

        with ToolboxClient(CHANNEL) as client:
            result = client.estimate([{"text": "hello"}], ["DE"])

        assert result == expected

    def test_uses_default_provider(self, mock_httpx):
        respx.post(f"{TRANSLATOR_PREFIX}/estimate/").mock(return_value=httpx.Response(200, json={}))

        with ToolboxClient(CHANNEL) as client:
            client.estimate([{"text": "hello"}], ["DE"])

        body = json.loads(respx.calls.last.request.content)
        assert body["provider"] == _DEFAULT_PROVIDER


class TestEstimateChunkedBatching:
    def test_aggregates_two_batches(self, mock_httpx):
        chunk1 = {
            "per_language": [
                {"language": "DE", "total_chars": 100, "estimated_cost_usd": "0.20"},
                {"language": "FR", "total_chars": 80, "estimated_cost_usd": "0.16"},
            ],
            "total_cost_usd": "0.36",
        }
        chunk2 = {
            "per_language": [
                {"language": "DE", "total_chars": 50, "estimated_cost_usd": "0.10"},
                {"language": "FR", "total_chars": 40, "estimated_cost_usd": "0.08"},
            ],
            "total_cost_usd": "0.18",
        }
        route = respx.post(f"{TRANSLATOR_PREFIX}/estimate/")
        route.side_effect = [httpx.Response(200, json=chunk1), httpx.Response(200, json=chunk2)]

        # 51 items triggers chunking (batch size = 50).
        items = [{"text": f"item-{i}"} for i in range(51)]

        with ToolboxClient(CHANNEL) as client:
            result = client.estimate(items, ["DE", "FR"])

        assert len(result["per_language"]) == 2

        de = next(lang for lang in result["per_language"] if lang["language"] == "DE")
        fr = next(lang for lang in result["per_language"] if lang["language"] == "FR")
        assert de["total_chars"] == 150
        assert fr["total_chars"] == 120
        assert Decimal(de["estimated_cost_usd"]) == Decimal("0.30")
        assert Decimal(fr["estimated_cost_usd"]) == Decimal("0.24")
        assert Decimal(result["total_cost_usd"]) == Decimal("0.54")


class TestCreateJob:
    def test_creates_job(self, mock_httpx):
        expected = {"job_id": "abc-123", "status": "pending"}
        respx.post(f"{TRANSLATOR_PREFIX}/jobs/").mock(return_value=httpx.Response(202, json=expected))

        with ToolboxClient(CHANNEL) as client:
            result = client.create_job([{"text": "hello"}], "DE")

        assert result == expected

    def test_includes_optional_fields(self, mock_httpx):
        respx.post(f"{TRANSLATOR_PREFIX}/jobs/").mock(return_value=httpx.Response(202, json={}))

        with ToolboxClient(CHANNEL) as client:
            client.create_job(
                [{"text": "hello"}],
                "DE",
                source_language="en",
                formality="more",
                context="E-commerce",
                metadata={"k": "v"},
            )

        body = json.loads(respx.calls.last.request.content)
        assert body["source_language"] == "en"
        assert body["formality"] == "more"
        assert body["context"] == "E-commerce"
        assert body["metadata"] == {"k": "v"}


class TestGetJob:
    def test_returns_job(self, mock_httpx):
        expected = {"job_id": "abc-123", "status": "completed"}
        respx.get(f"{TRANSLATOR_PREFIX}/jobs/abc-123/").mock(return_value=httpx.Response(200, json=expected))

        with ToolboxClient(CHANNEL) as client:
            result = client.get_job("abc-123")

        assert result == expected


class TestListJobs:
    def test_returns_job_list(self, mock_httpx):
        expected = {"results": [], "count": 0}
        respx.get(f"{TRANSLATOR_PREFIX}/jobs/").mock(return_value=httpx.Response(200, json=expected))

        with ToolboxClient(CHANNEL) as client:
            result = client.list_jobs()

        assert result == expected


# --- Error mapping ---


class TestRaiseForStatus:
    def test_401_raises_auth_error(self, mock_httpx):
        respx.get(f"{TRANSLATOR_PREFIX}/jobs/").mock(return_value=httpx.Response(401, json={"message": "Unauthorized"}))

        with ToolboxClient(CHANNEL) as client:
            with pytest.raises(ToolboxAuthError):
                client.list_jobs()

    def test_402_raises_budget_error(self, mock_httpx):
        respx.get(f"{TRANSLATOR_PREFIX}/jobs/").mock(return_value=httpx.Response(402, json={"message": "Over budget"}))

        with ToolboxClient(CHANNEL) as client:
            with pytest.raises(ToolboxBudgetExceededError):
                client.list_jobs()

    def test_404_raises_not_found(self, mock_httpx):
        respx.get(f"{TRANSLATOR_PREFIX}/jobs/missing/").mock(
            return_value=httpx.Response(404, json={"message": "Not found"})
        )

        with ToolboxClient(CHANNEL) as client:
            with pytest.raises(ToolboxNotFoundError):
                client.get_job("missing")

    def test_429_raises_rate_limit_with_retry_after(self, mock_httpx):
        respx.get(f"{TRANSLATOR_PREFIX}/jobs/").mock(
            return_value=httpx.Response(429, headers={"Retry-After": "30"}, json={"message": "Rate limited"})
        )

        with ToolboxClient(CHANNEL, max_retries=1) as client:
            with pytest.raises(ToolboxRateLimitError) as exc_info:
                client.list_jobs()

        assert exc_info.value.retry_after == 30.0

    def test_400_raises_validation_error(self, mock_httpx):
        body = {"error": "VALIDATION_ERROR", "message": "Invalid input", "field_errors": {"items": ["required"]}}
        respx.post(f"{TRANSLATOR_PREFIX}/estimate/").mock(return_value=httpx.Response(400, json=body))

        with ToolboxClient(CHANNEL) as client:
            with pytest.raises(ToolboxValidationError) as exc_info:
                client.estimate([{"text": "x"}], ["DE"])

        assert exc_info.value.field_errors == {"items": ["required"]}

    def test_500_raises_server_error(self, mock_httpx):
        respx.get(f"{TRANSLATOR_PREFIX}/jobs/").mock(
            return_value=httpx.Response(500, json={"message": "Internal error"})
        )

        with ToolboxClient(CHANNEL, max_retries=1) as client:
            with pytest.raises(ToolboxServerError) as exc_info:
                client.list_jobs()

        assert exc_info.value.status_code == 500


# --- Retry logic ---


class TestRetryBehavior:
    @patch("django_utils.toolbox.client.time.sleep")
    def test_retries_on_503_then_succeeds(self, mock_sleep, mock_httpx):
        route = respx.get(f"{TRANSLATOR_PREFIX}/jobs/")
        route.side_effect = [
            httpx.Response(503, json={"message": "Unavailable"}),
            httpx.Response(200, json={"results": []}),
        ]

        with ToolboxClient(CHANNEL) as client:
            result = client.list_jobs()

        assert result == {"results": []}
        mock_sleep.assert_called_once()

    @patch("django_utils.toolbox.client.time.sleep")
    def test_does_not_retry_on_401(self, mock_sleep, mock_httpx):
        respx.get(f"{TRANSLATOR_PREFIX}/jobs/").mock(return_value=httpx.Response(401, json={}))

        with ToolboxClient(CHANNEL) as client:
            with pytest.raises(ToolboxAuthError):
                client.list_jobs()

        mock_sleep.assert_not_called()

    @patch("django_utils.toolbox.client.time.sleep")
    def test_does_not_retry_on_400(self, mock_sleep, mock_httpx):
        respx.post(f"{TRANSLATOR_PREFIX}/estimate/").mock(return_value=httpx.Response(400, json={"message": "Bad"}))

        with ToolboxClient(CHANNEL) as client:
            with pytest.raises(ToolboxValidationError):
                client.estimate([{"text": "x"}], ["DE"])

        mock_sleep.assert_not_called()

    @patch("django_utils.toolbox.client.time.sleep")
    def test_exponential_backoff_delay(self, mock_sleep, mock_httpx):
        respx.get(f"{TRANSLATOR_PREFIX}/jobs/").mock(return_value=httpx.Response(503, json={"message": "Down"}))

        with ToolboxClient(CHANNEL, max_retries=3) as client:
            with pytest.raises(ToolboxServerError):
                client.list_jobs()

        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays[0] == pytest.approx(2.0)
        assert delays[1] == pytest.approx(4.0)

    @patch("django_utils.toolbox.client.time.sleep")
    def test_uses_retry_after_on_429(self, mock_sleep, mock_httpx):
        route = respx.get(f"{TRANSLATOR_PREFIX}/jobs/")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "10"}, json={"message": "Rate limited"}),
            httpx.Response(200, json={"results": []}),
        ]

        with ToolboxClient(CHANNEL) as client:
            client.list_jobs()

        mock_sleep.assert_called_once_with(10.0)


# --- Connection errors ---


class TestConnectionErrors:
    @patch("django_utils.toolbox.client.time.sleep")
    def test_network_failure_raises_connection_error(self, mock_sleep, mock_httpx):
        respx.get(f"{TRANSLATOR_PREFIX}/jobs/").mock(side_effect=httpx.ConnectError("DNS failed"))

        with ToolboxClient(CHANNEL, max_retries=1) as client:
            with pytest.raises(ToolboxConnectionError) as exc_info:
                client.list_jobs()

        assert "ConnectError" in exc_info.value.message

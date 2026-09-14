# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""2.1.0 compat: the 2.0.x error API, wire format and retry policy of translator callers."""

from unittest.mock import patch

import httpx
import pytest
import respx
from django_utils.toolbox import errors as shared

from django_utils_translator.clients.errors import (
    ToolboxAuthError,
    ToolboxBudgetExceededError,
    ToolboxConnectionError,
    ToolboxNotConfiguredError,
    ToolboxNotFoundError,
    ToolboxRateLimitError,
    ToolboxTimeoutError,
    ToolboxValidationError,
)
from django_utils_translator.clients.toolbox import ToolboxClient
from django_utils_translator.views import handle_toolbox_error

CHANNEL = "test-channel"
JOBS_URL = f"https://toolbox.test.internal/api/ai-translator/v2/admin/{CHANNEL}/jobs/"


@pytest.fixture()
def mock_httpx():
    with respx.mock:
        yield


def test_legacy_error_constructors_still_work():
    errors = [
        ToolboxAuthError(),
        ToolboxNotFoundError("gone"),
        ToolboxBudgetExceededError("hit"),
        ToolboxRateLimitError(retry_after=5.0),
        ToolboxValidationError("bad", details=[{"field": "items"}]),
        ToolboxConnectionError("DNS"),
    ]

    assert [exc.status_code for exc in errors] == [401, 404, 402, 429, 400, 0]
    assert isinstance(errors[0], shared.ToolboxAuthError)
    assert isinstance(errors[5], shared.ToolboxConnectionError)


def test_validation_error_details_attribute(mock_httpx):
    body = {"error": "VALIDATION_ERROR", "message": "Invalid", "field_errors": {"items": ["required"]}}
    respx.post(JOBS_URL).mock(return_value=httpx.Response(400, json=body))

    with ToolboxClient(CHANNEL) as client, pytest.raises(ToolboxValidationError) as exc_info:
        client.create_job([{"key": "k", "text": "x"}], "DE")

    assert exc_info.value.details == [{"field": "items", "issue": "required"}]
    assert exc_info.value.field_errors == {"items": ["required"]}


@pytest.mark.parametrize("name", ["AI_TOOLBOX_BASE_URL", "AI_TOOLBOX_API_KEY"])
def test_missing_config_is_value_error(settings, name):
    setattr(settings, name, "")

    with pytest.raises(ValueError) as exc_info:
        ToolboxClient(CHANNEL)

    assert isinstance(exc_info.value, ToolboxNotConfiguredError)
    assert isinstance(exc_info.value, shared.ToolboxNotConfiguredError)


@pytest.mark.parametrize(
    ("status_code", "code", "legacy_class"),
    [
        (401, "", ToolboxAuthError),
        (402, "BUDGET_EXCEEDED", ToolboxBudgetExceededError),
        (404, "", ToolboxNotFoundError),
    ],
)
def test_client_raises_legacy_classes(mock_httpx, status_code, code, legacy_class):
    respx.get(JOBS_URL).mock(return_value=httpx.Response(status_code, json={"error": code}))

    with ToolboxClient(CHANNEL) as client, pytest.raises(legacy_class):
        client.list_jobs()


@pytest.mark.parametrize("failure", [httpx.ReadTimeout("slow"), httpx.Response(503, json={"error": "X"})])
def test_create_job_not_retried_after_read_timeout(mock_httpx, failure):
    route = respx.post(JOBS_URL).mock(side_effect=[failure, httpx.Response(202, json={"job_id": "j"})])

    with patch("django_utils.toolbox.client.time.sleep"), ToolboxClient(CHANNEL) as client:
        with pytest.raises((ToolboxTimeoutError, shared.ToolboxServerError)):
            client.create_job([{"key": "k", "text": "x"}], "DE")

    assert route.call_count == 1


@pytest.mark.parametrize(
    ("exc", "http_status", "code"),
    [
        (
            shared.ToolboxValidationError(400, "Invalid", "VALIDATION_ERROR", {"items": ["required"]}),
            400,
            "VALIDATION_ERROR",
        ),
        (shared.ToolboxTimeoutError(504, "timed out", "UPSTREAM_TIMEOUT"), 502, "PROVIDER_ERROR"),
        (shared.ToolboxRateLimitError(503, "limited", "UPSTREAM_RATE_LIMITED"), 502, "PROVIDER_ERROR"),
    ],
)
def test_translator_error_wire_format_unchanged(exc, http_status, code):
    response = handle_toolbox_error(exc)

    assert response.status_code == http_status
    assert response.data["error"] == code
    if http_status == 400:
        assert response.data["details"] == []
        assert response.data["field_errors"] == {"items": ["required"]}


@pytest.mark.parametrize("retry_after", [-5.0, float("nan"), float("inf"), 1e30])
def test_handle_error_with_invalid_retry_after_does_not_crash(retry_after):
    response = handle_toolbox_error(ToolboxRateLimitError(retry_after=retry_after))

    assert response.status_code == 429
    assert "Retry-After" not in response

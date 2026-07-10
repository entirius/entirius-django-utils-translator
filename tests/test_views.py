# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for handle_toolbox_error DRF response mapper."""

from django_utils_translator.clients.errors import (
    ToolboxAuthError,
    ToolboxBudgetExceededError,
    ToolboxError,
    ToolboxNotFoundError,
    ToolboxRateLimitError,
    ToolboxServerError,
    ToolboxValidationError,
)
from django_utils_translator.views import handle_toolbox_error


class TestHandleToolboxErrorBudget:
    def test_returns_402(self):
        exc = ToolboxBudgetExceededError("Budget hit")
        response = handle_toolbox_error(exc)
        assert response.status_code == 402
        assert response.data["error"] == "BUDGET_EXCEEDED"
        assert response.data["message"] == "Budget hit"


class TestHandleToolboxErrorNotFound:
    def test_returns_404(self):
        exc = ToolboxNotFoundError("Job not found")
        response = handle_toolbox_error(exc)
        assert response.status_code == 404
        assert response.data["error"] == "NOT_FOUND"


class TestHandleToolboxErrorValidation:
    def test_returns_400_with_details(self):
        details = [{"field": "items", "issue": "REQUIRED"}]
        exc = ToolboxValidationError(message="Validation failed", details=details)
        response = handle_toolbox_error(exc)
        assert response.status_code == 400
        assert response.data["error"] == "VALIDATION_ERROR"
        assert response.data["details"] == details


class TestHandleToolboxErrorRateLimit:
    def test_returns_429_with_retry_header(self):
        exc = ToolboxRateLimitError(retry_after=30.0)
        response = handle_toolbox_error(exc)
        assert response.status_code == 429
        assert response.data["error"] == "RATE_LIMIT_EXCEEDED"
        assert response["Retry-After"] == "30"

    def test_returns_429_without_retry_header(self):
        exc = ToolboxRateLimitError()
        response = handle_toolbox_error(exc)
        assert response.status_code == 429
        assert "Retry-After" not in response


class TestHandleToolboxErrorGenericFallback:
    def test_server_error_returns_502_with_debug_id(self):
        exc = ToolboxServerError(503, "Service Unavailable")
        response = handle_toolbox_error(exc)
        assert response.status_code == 502
        assert response.data["error"] == "PROVIDER_ERROR"
        assert "debug_id" in response.data
        # Must NOT leak upstream message.
        assert "Service Unavailable" not in response.data["message"]

    def test_auth_error_returns_502_no_config_leak(self):
        exc = ToolboxAuthError()
        response = handle_toolbox_error(exc)
        assert response.status_code == 502
        assert "API_KEY" not in response.data["message"]
        assert "debug_id" in response.data

    def test_generic_toolbox_error_returns_502(self):
        exc = ToolboxError(418, "I'm a teapot")
        response = handle_toolbox_error(exc)
        assert response.status_code == 502
        assert response.data["error"] == "PROVIDER_ERROR"
        assert "teapot" not in response.data["message"]

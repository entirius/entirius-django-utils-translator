# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for the toolbox exception hierarchy."""

from django_utils_translator.clients.errors import (
    ToolboxAuthError,
    ToolboxBudgetExceededError,
    ToolboxConnectionError,
    ToolboxError,
    ToolboxNotFoundError,
    ToolboxRateLimitError,
    ToolboxServerError,
    ToolboxValidationError,
)


class TestToolboxError:
    def test_base_error_attributes(self):
        exc = ToolboxError(500, "Server error")
        assert exc.status_code == 500
        assert exc.message == "Server error"
        assert "500" in str(exc)

    def test_base_error_is_exception(self):
        assert issubclass(ToolboxError, Exception)


class TestToolboxAuthError:
    def test_defaults(self):
        exc = ToolboxAuthError()
        assert exc.status_code == 401
        assert "Authentication failed" in exc.message

    def test_is_toolbox_error(self):
        assert issubclass(ToolboxAuthError, ToolboxError)


class TestToolboxNotFoundError:
    def test_default_message(self):
        exc = ToolboxNotFoundError()
        assert exc.status_code == 404
        assert exc.message == "Resource not found"

    def test_custom_message(self):
        exc = ToolboxNotFoundError("Job abc123 not found")
        assert exc.message == "Job abc123 not found"
        assert exc.status_code == 404


class TestToolboxValidationError:
    def test_with_details(self):
        details = [{"field": "items", "issue": "REQUIRED"}]
        exc = ToolboxValidationError(message="Validation failed", details=details)
        assert exc.status_code == 400
        assert exc.message == "Validation failed"
        assert exc.details == details

    def test_defaults_empty_details(self):
        exc = ToolboxValidationError(message="Bad input")
        assert exc.details == []


class TestToolboxBudgetExceededError:
    def test_default_message(self):
        exc = ToolboxBudgetExceededError()
        assert exc.status_code == 402
        assert "budget" in exc.message.lower()

    def test_custom_message(self):
        exc = ToolboxBudgetExceededError("Limit reached: $50.00")
        assert exc.message == "Limit reached: $50.00"


class TestToolboxRateLimitError:
    def test_without_retry_after(self):
        exc = ToolboxRateLimitError()
        assert exc.status_code == 429
        assert exc.retry_after is None
        assert "Rate limit" in exc.message

    def test_with_retry_after(self):
        exc = ToolboxRateLimitError(retry_after=30.0)
        assert exc.retry_after == 30.0
        assert "30.0s" in exc.message


class TestToolboxServerError:
    def test_preserves_status_code(self):
        exc = ToolboxServerError(503, "Service Unavailable")
        assert exc.status_code == 503
        assert exc.message == "Service Unavailable"

    def test_inherits_from_base(self):
        exc = ToolboxServerError(500, "Internal")
        assert isinstance(exc, ToolboxError)


class TestToolboxConnectionError:
    def test_cause_in_message(self):
        exc = ToolboxConnectionError("ConnectTimeout")
        assert exc.status_code == 0
        assert "ConnectTimeout" in exc.message

    def test_is_toolbox_error(self):
        assert issubclass(ToolboxConnectionError, ToolboxError)

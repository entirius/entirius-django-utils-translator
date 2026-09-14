# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Shared DRF view helpers for translation modules — the 2.0.x wire format.

New consumers opt into the shared mapping with ``django_utils.toolbox.views.handle_toolbox_error``.
"""

import logging
import uuid

from django_utils.toolbox import errors as base
from django_utils.toolbox import views as base_views
from django_utils.toolbox.errors import parse_retry_after
from rest_framework import status
from rest_framework.response import Response

from django_utils_translator.clients import ToolboxError

logger = logging.getLogger("process")


def handle_toolbox_error(exc: ToolboxError) -> Response:
    """Map ToolboxError to appropriate DRF Response. Used by all translator ViewSets."""
    if isinstance(exc, base.ToolboxNotConfiguredError):
        return base_views.handle_toolbox_error(exc)
    if isinstance(exc, base.ToolboxBudgetExceededError):
        return Response({"error": "BUDGET_EXCEEDED", "message": exc.message}, status=status.HTTP_402_PAYMENT_REQUIRED)
    if isinstance(exc, base.ToolboxNotFoundError):
        return Response({"error": "NOT_FOUND", "message": exc.message}, status=status.HTTP_404_NOT_FOUND)
    if isinstance(exc, base.ToolboxValidationError):
        return _validation_error(exc)
    if isinstance(exc, base.ToolboxRateLimitError) and exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return _rate_limit_error(exc)
    # Auth errors, provider errors, server errors, timeouts, upstream rate limits — generic 502, no detail leak.
    error_id = uuid.uuid4().hex[:8]
    logger.error(
        "Toolbox error [%s] (type=%s, status=%d, code=%s)", error_id, type(exc).__name__, exc.status_code, exc.code
    )
    return Response(
        {"error": "PROVIDER_ERROR", "message": "Translation service error.", "debug_id": error_id},
        status=status.HTTP_502_BAD_GATEWAY,
    )


def _validation_error(exc: base.ToolboxValidationError) -> Response:
    body = {
        "error": "VALIDATION_ERROR",
        "message": exc.message,
        "details": getattr(exc, "details", []),
        "field_errors": exc.field_errors,
    }
    return Response(body, status=status.HTTP_400_BAD_REQUEST)


def _rate_limit_error(exc: base.ToolboxRateLimitError) -> Response:
    headers = {}
    retry_after = parse_retry_after(exc.retry_after)
    if retry_after is not None:
        headers["Retry-After"] = str(int(retry_after))
    return Response(
        {"error": "RATE_LIMIT_EXCEEDED", "message": exc.message},
        status=status.HTTP_429_TOO_MANY_REQUESTS,
        headers=headers,
    )


__all__ = ["handle_toolbox_error"]

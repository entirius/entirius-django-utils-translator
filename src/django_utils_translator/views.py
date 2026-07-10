# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Shared DRF view helpers for translation modules."""

import logging
import uuid

from rest_framework import status
from rest_framework.response import Response

from django_utils_translator.clients import (
    ToolboxBudgetExceededError,
    ToolboxError,
    ToolboxNotFoundError,
    ToolboxRateLimitError,
    ToolboxValidationError,
)

logger = logging.getLogger("process")


def handle_toolbox_error(exc: ToolboxError) -> Response:
    """Map ToolboxError to appropriate DRF Response. Used by all translator ViewSets."""
    if isinstance(exc, ToolboxBudgetExceededError):
        return Response({"error": "BUDGET_EXCEEDED", "message": exc.message}, status=status.HTTP_402_PAYMENT_REQUIRED)
    if isinstance(exc, ToolboxNotFoundError):
        return Response({"error": "NOT_FOUND", "message": exc.message}, status=status.HTTP_404_NOT_FOUND)
    if isinstance(exc, ToolboxValidationError):
        return Response(
            {"error": "VALIDATION_ERROR", "message": exc.message, "details": exc.details},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(exc, ToolboxRateLimitError):
        headers = {}
        if exc.retry_after is not None:
            headers["Retry-After"] = str(int(exc.retry_after))
        return Response(
            {"error": "RATE_LIMIT_EXCEEDED", "message": exc.message},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
            headers=headers,
        )
    # Auth errors, provider errors, server errors — generic 502, no detail leak.
    error_id = uuid.uuid4().hex[:8]
    logger.error(
        "Toolbox error [%s] (type=%s, status=%d): %s", error_id, type(exc).__name__, exc.status_code, exc.message
    )
    return Response(
        {"error": "PROVIDER_ERROR", "message": "Translation service error.", "debug_id": error_id},
        status=status.HTTP_502_BAD_GATEWAY,
    )

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Exception hierarchy for the AI toolbox HTTP client.

The 2.0.x names keep their 2.0.x constructors as thin subclasses of ``django_utils.toolbox.errors``, so code
catching either the translator class or the shared class keeps working.
"""

from django_utils.toolbox import errors as base
from django_utils.toolbox.errors import (
    ToolboxError,
    ToolboxModelNotAllowedError,
    ToolboxTimeoutError,
)

__all__ = [
    "ToolboxError",
    "ToolboxNotConfiguredError",
    "ToolboxAuthError",
    "ToolboxModelNotAllowedError",
    "ToolboxNotFoundError",
    "ToolboxValidationError",
    "ToolboxBudgetExceededError",
    "ToolboxRateLimitError",
    "ToolboxTimeoutError",
    "ToolboxServerError",
    "ToolboxConnectionError",
    "to_legacy_error",
]


class ToolboxNotConfiguredError(base.ToolboxNotConfiguredError, ValueError):
    """Missing toolbox settings — also a ``ValueError``, as the 2.0.x client raised."""


class ToolboxAuthError(base.ToolboxAuthError):
    """API key rejected (401/403)."""

    def __init__(self) -> None:
        super().__init__(401, "Authentication failed. Check AI_TOOLBOX_API_KEY.")


class ToolboxNotFoundError(base.ToolboxNotFoundError):
    """Resource not found (404)."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(404, detail)


class ToolboxValidationError(base.ToolboxValidationError):
    """Toolbox returned 400 with structured error details."""

    def __init__(self, message: str, details: list[dict] | None = None) -> None:
        self.details = details or []
        super().__init__(400, message)


class ToolboxBudgetExceededError(base.ToolboxBudgetExceededError):
    """Monthly budget exceeded (402)."""

    def __init__(self, message: str = "Monthly budget exceeded") -> None:
        super().__init__(402, message)


class ToolboxRateLimitError(base.ToolboxRateLimitError):
    """Rate limit exceeded (429)."""

    def __init__(self, retry_after: float | None = None) -> None:
        msg = "Rate limit exceeded"
        if retry_after is not None:
            msg += f". Retry after {retry_after}s"
        super().__init__(429, msg, retry_after=retry_after)


class ToolboxServerError(base.ToolboxServerError):
    """Toolbox returned 5xx."""


class ToolboxConnectionError(base.ToolboxConnectionError):
    """Network-level failure (DNS, timeout, connection refused)."""

    def __init__(self, cause: str) -> None:
        super().__init__(0, f"Connection failed: {cause}")


_LEGACY_CLASSES: dict[type[ToolboxError], type[ToolboxError]] = {
    base.ToolboxNotConfiguredError: ToolboxNotConfiguredError,
    base.ToolboxAuthError: ToolboxAuthError,
    base.ToolboxNotFoundError: ToolboxNotFoundError,
    base.ToolboxValidationError: ToolboxValidationError,
    base.ToolboxBudgetExceededError: ToolboxBudgetExceededError,
    base.ToolboxRateLimitError: ToolboxRateLimitError,
    base.ToolboxServerError: ToolboxServerError,
    base.ToolboxConnectionError: ToolboxConnectionError,
}


def to_legacy_error(exc: ToolboxError) -> ToolboxError:
    """Re-type a shared error as its translator subclass, keeping every attribute (no constructor call)."""
    legacy_class = _LEGACY_CLASSES.get(type(exc))
    if legacy_class is None:
        return exc
    legacy = legacy_class.__new__(legacy_class, *exc.args)
    legacy.__dict__.update(exc.__dict__)
    if legacy_class is ToolboxValidationError:
        legacy.details = [
            {"field": field, "issue": issue} for field, issues in exc.field_errors.items() for issue in issues
        ]
    return legacy

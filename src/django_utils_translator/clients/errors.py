# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Exception hierarchy for AI toolbox HTTP client."""


class ToolboxError(Exception):
    """Base exception for all toolbox client errors."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"Toolbox HTTP {status_code}: {message}")


class ToolboxAuthError(ToolboxError):
    """API key rejected (401/403)."""

    def __init__(self) -> None:
        super().__init__(401, "Authentication failed. Check AI_TOOLBOX_API_KEY.")


class ToolboxNotFoundError(ToolboxError):
    """Resource not found (404)."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(404, detail)


class ToolboxValidationError(ToolboxError):
    """Toolbox returned 400 with structured error details."""

    def __init__(self, message: str, details: list[dict] | None = None) -> None:
        self.details = details or []
        super().__init__(400, message)


class ToolboxBudgetExceededError(ToolboxError):
    """Monthly budget exceeded (402)."""

    def __init__(self, message: str = "Monthly budget exceeded") -> None:
        super().__init__(402, message)


class ToolboxRateLimitError(ToolboxError):
    """Rate limit exceeded (429)."""

    def __init__(self, retry_after: float | None = None) -> None:
        self.retry_after = retry_after
        msg = "Rate limit exceeded"
        if retry_after is not None:
            msg += f". Retry after {retry_after}s"
        super().__init__(429, msg)


class ToolboxServerError(ToolboxError):
    """Toolbox returned 5xx."""


class ToolboxConnectionError(ToolboxError):
    """Network-level failure (DNS, timeout, connection refused)."""

    def __init__(self, cause: str) -> None:
        super().__init__(0, f"Connection failed: {cause}")

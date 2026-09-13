# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Exception hierarchy for the AI toolbox HTTP client — re-exported from ``django_utils.toolbox.errors``."""

from django_utils.toolbox.errors import (
    ToolboxAuthError,
    ToolboxBudgetExceededError,
    ToolboxConnectionError,
    ToolboxError,
    ToolboxModelNotAllowedError,
    ToolboxNotConfiguredError,
    ToolboxNotFoundError,
    ToolboxRateLimitError,
    ToolboxServerError,
    ToolboxTimeoutError,
    ToolboxValidationError,
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
]

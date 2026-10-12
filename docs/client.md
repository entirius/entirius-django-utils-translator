---
title: Toolbox client
description: The translator ToolboxClient — methods, retries, estimate batching — and the error hierarchy.
---

## ToolboxClient

Subclass of `django_utils.toolbox.ToolboxClient` on `_url("ai-translator", …)`. Context-manager protocol.

- Exponential backoff retry on 408/429/500/502/503/504 (`AI_TOOLBOX_MAX_RETRIES` total attempts);
  `create_job()` is paid — retried only on connection refusal or 429 with a valid `Retry-After`
- Automatic estimate batching (50 items per request, aggregates costs)
- Methods: `estimate()`, `create_job()`, `get_job()`, `get_job_results()`, `list_jobs()`; the base adds
  `complete()` and `list_models()`
- `ToolboxClient(channel_idx=None, *, max_retries=None)` — empty base URL / key / channel raises
  `ToolboxNotConfiguredError` (also a `ValueError`); shared errors are re-typed to the 2.0.x subclasses

## Error Hierarchy

2.0.x constructors are a public contract (pim-translator pins `>=2.0.0`): `ToolboxAuthError()`,
`ToolboxNotFoundError(detail)`, `ToolboxBudgetExceededError(msg)`, `ToolboxRateLimitError(retry_after=)`,
`ToolboxValidationError(message, details=)`, `ToolboxConnectionError(cause)`. Each subclasses its
`django_utils.toolbox.errors` counterpart; `to_legacy_error()` re-types shared errors without calling the
constructor. `details` is derived from the toolbox `field_errors`. `handle_toolbox_error` keeps the 2.0.x wire
format — never swap in the shared mapping here. Two states take the shared 503 body: not configured
(`AI_TOOLBOX_NOT_CONFIGURED`) and switched off (`AI_TOOLBOX_ENABLED = False` → `ToolboxDisabledError`, which the
client raises un-retyped → `AI_TOOLBOX_DISABLED`).

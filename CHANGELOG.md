# Changelog

## 2.1.0 — unreleased

- `ToolboxClient` now subclasses `django_utils.toolbox.ToolboxClient` (`entirius-django-utils>=2.1.0`) and adds
  only the translator endpoints (`estimate`, `create_job`, `get_job`, `get_job_results`, `list_jobs`);
  transport and retry policy are unchanged.
- `clients.errors`, `views.handle_toolbox_error` and `settings.AI_TOOLBOX_*` are re-exports of the shared
  toolbox code; every public import path stays. Settings are read lazily (`override_settings` works).
- The 2.0.x error API stays: every `clients.errors` name keeps its 2.0.x constructor and attributes
  (`ToolboxValidationError.details` included) as a subclass of the shared class, and the client raises these
  subclasses, so code catching either keeps working. Validation errors additionally carry `field_errors`.
  Missing configuration raises `ToolboxNotConfiguredError`, which is also a `ValueError`.
- `views.handle_toolbox_error` keeps the 2.0.x wire format (400 `details`, plus `field_errors`; 504 and 503
  `UPSTREAM_RATE_LIMITED` → 502 `PROVIDER_ERROR`; 429 `Retry-After` only when valid). The shared mapping is
  opt-in via `django_utils.toolbox.views.handle_toolbox_error`.
- `create_job()` is no longer re-sent after a timeout, a dropped connection or a 5xx (duplicate paid jobs).
- Retry warnings log under `django_utils.toolbox.client` instead of `process`.

## 2.0.0

- Initial public release.

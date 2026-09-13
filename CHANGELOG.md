# Changelog

## 2.1.0 — unreleased

- `ToolboxClient` now subclasses `django_utils.toolbox.ToolboxClient` (`entirius-django-utils>=2.1.0`) and adds
  only the translator endpoints (`estimate`, `create_job`, `get_job`, `get_job_results`, `list_jobs`);
  transport and retry policy are unchanged.
- `clients.errors`, `views.handle_toolbox_error` and `settings.AI_TOOLBOX_*` are re-exports of the shared
  toolbox code; every public import path stays. Settings are read lazily (`override_settings` works).
- Error constructors follow the shared shape `(status_code, message, code="", field_errors=None)`;
  validation errors expose `field_errors` instead of `details`. Missing configuration raises
  `ToolboxNotConfiguredError` instead of `ValueError`. The generic 502 message is "AI service error.".
- Retry warnings log under `django_utils.toolbox.client` instead of `process`.

## 2.0.0

- Initial public release.

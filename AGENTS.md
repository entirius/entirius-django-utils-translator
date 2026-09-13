# AGENTS.md

Shared translation infrastructure for PIM and ContentDB translators — distribution
`entirius-django-utils-translator`, Django app `django_utils_translator`. Provides the HTTP client
for the remote AI toolbox, a unified error hierarchy, base Pydantic request/response schemas, HTML
sanitization, and DRF error mapping. No Django models, no migrations, no API endpoints — pure
library code consumed by domain-specific translator modules.

Since 2.1.0 the transport, error hierarchy, settings and `handle_toolbox_error` live in
`entirius-django-utils` (`django_utils.toolbox`); this package subclasses the client with the translator
endpoints and re-exports the rest under its historical import paths.

**Tech:** Python >=3.11, Django >=5.0, DRF, httpx, Pydantic v2, nh3, entirius-django-utils >=2.1.0

## Commands

| Command | Meaning |
|---|---|
| `make install` | sync dependencies (uv, incl. extras) |
| `make check` | lint + format-check (ruff) |
| `make fix` | auto-fix lint + format |
| `make test` | test suite (pytest + pytest-django) |

## Conventions

- English only: code, docs, commits, branches, PRs.
- MPL-2.0: every non-trivial source file carries the license header (pre-commit inserts it).
- Toolchain: uv + ruff + hatchling + pytest; all config in `pyproject.toml`; `uv.lock` committed.
- Git flow: `master` (production) + `develop` (integration); changes land via PR; semver tag on `master`.
- Never rename the package / Django app_label `django_utils_translator` — it is a schema contract.
- Migrations are part of the public contract — never edit an already released migration.
- Default: do not commit — git is the user's call.

## Architecture

```
src/django_utils_translator/
├── clients/
│   ├── errors.py           # re-export of django_utils.toolbox.errors (ToolboxError base)
│   └── toolbox.py          # ToolboxClient(django_utils.toolbox.ToolboxClient) — translator endpoints + batching
├── schemas/
│   ├── requests.py         # BaseTranslateRequest (target_languages, provider, dry_run, etc.)
│   └── responses.py        # LanguageCostEstimate, BulkTranslateJobResponse, BulkTranslateEstimateResponse
├── sanitize.py             # sanitize() — nh3 HTML cleaning for translated text
├── settings.py             # AI_TOOLBOX_* (lazy re-export from django_utils), LANGUAGE_CODE_MAP
├── views.py                # re-export of django_utils.toolbox.views.handle_toolbox_error
└── apps.py                 # Django AppConfig
```

## Key Components

### ToolboxClient

Subclass of `django_utils.toolbox.ToolboxClient` on `_url("ai-translator", …)`. Context-manager protocol.

- Exponential backoff retry on 408/429/500/502/503/504 (`AI_TOOLBOX_MAX_RETRIES` total attempts)
- Automatic estimate batching (50 items per request, aggregates costs)
- Methods: `estimate()`, `create_job()`, `get_job()`, `get_job_results()`, `list_jobs()`; the base adds
  `complete()` and `list_models()`
- `ToolboxClient(channel_idx=None, *, max_retries=None)` — empty base URL / key / channel raises
  `ToolboxNotConfiguredError`

### Error Hierarchy

Defined in `django_utils.toolbox.errors` — full mapping table in the `entirius-django-utils` AGENTS.md.
All errors take `(status_code, message, code="", field_errors=None)`; validation errors carry
`field_errors` (the toolbox body key — never `details`).

### Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `AI_TOOLBOX_*` | see `django_utils.toolbox.settings` | read lazily from Django settings on access |
| `AI_TRANSLATOR_LANGUAGE_CODE_MAP` | 20 entries | ISO2 to provider code mapping (e.g. `gb` to `EN-GB`) |

## Testing

No database required — tests use `respx` to mock httpx responses. Run via `make test`.

## Gotchas

- httpx logging is suppressed (`WARNING`) by the base client; retry warnings log under `django_utils.toolbox.client`.
- Known gap: `[tool.uv.sources]` points `entirius-django-utils` at `../entirius-django-utils` until utils 2.1.0
  is on PyPI — GitHub CI (`uv sync --frozen`) cannot resolve it; the release step replaces it with the floor.
- `_ESTIMATE_BATCH_SIZE = 50` — toolbox `/estimate/` endpoint rejects more than 50 items. Client
  auto-chunks and aggregates.
- `map_to_provider_code()` falls back to `lang_code.upper()` for unmapped codes. Override via
  `AI_TRANSLATOR_LANGUAGE_CODE_MAP` in settings.
- This package has no Django models and no migrations. It is a dependency of
  `entirius-django-pim-translator` and the ContentDB translator.

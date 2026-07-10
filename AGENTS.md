# AGENTS.md

Shared translation infrastructure for PIM and ContentDB translators — distribution
`entirius-django-utils-translator`, Django app `django_utils_translator`. Provides the HTTP client
for the remote AI toolbox, a unified error hierarchy, base Pydantic request/response schemas, HTML
sanitization, and DRF error mapping. No Django models, no migrations, no API endpoints — pure
library code consumed by domain-specific translator modules.

**Tech:** Python >=3.11, Django >=5.0, DRF, httpx, Pydantic v2, nh3

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
│   ├── errors.py           # 8-class exception hierarchy (ToolboxError base)
│   └── toolbox.py          # ToolboxClient — sync httpx client with retry + batching
├── schemas/
│   ├── requests.py         # BaseTranslateRequest (target_languages, provider, dry_run, etc.)
│   └── responses.py        # LanguageCostEstimate, BulkTranslateJobResponse, BulkTranslateEstimateResponse
├── sanitize.py             # sanitize() — nh3 HTML cleaning for translated text
├── settings.py             # AI_TOOLBOX_BASE_URL, API_KEY, TIMEOUT, MAX_RETRIES, LANGUAGE_CODE_MAP
├── views.py                # handle_toolbox_error() — ToolboxError → DRF Response mapper
└── apps.py                 # Django AppConfig
```

## Key Components

### ToolboxClient

Synchronous httpx client targeting the AI toolbox REST API. Context-manager protocol.

- Exponential backoff retry on 408/429/500/502/503/504
- Automatic estimate batching (50 items per request, aggregates costs)
- Methods: `estimate()`, `create_job()`, `get_job()`, `get_job_results()`, `list_jobs()`
- Reads `AI_TOOLBOX_BASE_URL` and `AI_TOOLBOX_API_KEY` from Django settings — fails loud if missing

### Error Hierarchy

| Exception | HTTP | When |
|-----------|------|------|
| `ToolboxError` | any | Base class |
| `ToolboxAuthError` | 401/403 | Bad API key |
| `ToolboxNotFoundError` | 404 | Resource missing |
| `ToolboxValidationError` | 400 | Structured details from toolbox |
| `ToolboxBudgetExceededError` | 402 | Monthly budget cap hit |
| `ToolboxRateLimitError` | 429 | Rate limit (with optional `retry_after`) |
| `ToolboxServerError` | 5xx | Toolbox internal error |
| `ToolboxConnectionError` | 0 | Network failure (DNS, timeout) |

### Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `AI_TOOLBOX_BASE_URL` | `""` | Toolbox service URL (required) |
| `AI_TOOLBOX_API_KEY` | `""` | API key for X-API-Key header (required) |
| `AI_TOOLBOX_TIMEOUT` | `60.0` | Request timeout in seconds |
| `AI_TOOLBOX_MAX_RETRIES` | `3` | Max retry attempts |
| `AI_TRANSLATOR_LANGUAGE_CODE_MAP` | 20 entries | ISO2 to provider code mapping (e.g. `gb` to `EN-GB`) |

## Testing

No database required — tests use `respx` to mock httpx responses. Run via `make test`.

## Gotchas

- httpx debug logging is suppressed (`WARNING` level) to prevent API key leaks in `X-API-Key` header logs.
- `_ESTIMATE_BATCH_SIZE = 50` — toolbox `/estimate/` endpoint rejects more than 50 items. Client
  auto-chunks and aggregates.
- `map_to_provider_code()` falls back to `lang_code.upper()` for unmapped codes. Override via
  `AI_TRANSLATOR_LANGUAGE_CODE_MAP` in settings.
- This package has no Django models and no migrations. It is a dependency of
  `entirius-django-pim-translator` and the ContentDB translator.

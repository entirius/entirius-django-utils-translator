# AGENTS.md

entirius-django-utils-translator (Django app `django_utils_translator`) — shared translation infrastructure for
the PIM and ContentDB translators of Entirius. Provides the HTTP client for the remote AI toolbox, a unified
error hierarchy, base Pydantic request/response schemas, HTML sanitization, and DRF error mapping. No Django
models, no migrations, no API endpoints — pure library code consumed by domain-specific translator modules.

## Commands

| Command | Meaning |
|---|---|
| `make install` | sync dependencies (uv, incl. extras) |
| `make check` | lint + format-check (ruff) |
| `make fix` | auto-fix lint + format |
| `make test` | test suite (pytest + pytest-django) |

No database: the tests mock httpx responses with `respx`.

## Conventions

- English only: code, docs, commits, branches, PRs.
- MPL-2.0: every non-trivial source file carries the license header (pre-commit inserts it).
- Toolchain: uv + ruff + hatchling + pytest; all config in `pyproject.toml`; `uv.lock` committed.
- Git flow: `master` (production) + `develop` (integration); changes land via PR; semver tag on `master`.
- Never rename the package / Django app_label `django_utils_translator` — it is a schema contract.
- Migrations are part of the public contract — never edit an already released migration.
- Default: do not commit — git is the user's call.
- No AI attribution in commits or PR descriptions.

## Architecture

```
src/django_utils_translator/
├── clients/
│   ├── errors.py           # 2.0.x error classes as subclasses of django_utils.toolbox.errors
│   └── toolbox.py          # ToolboxClient(django_utils.toolbox.ToolboxClient) — translator endpoints + batching
├── schemas/
│   ├── requests.py         # BaseTranslateRequest (target_languages, provider, dry_run, etc.)
│   └── responses.py        # LanguageCostEstimate, BulkTranslateJobResponse, BulkTranslateEstimateResponse
├── sanitize.py             # sanitize() — nh3 HTML cleaning for translated text
├── settings.py             # AI_TOOLBOX_* (lazy re-export from django_utils), LANGUAGE_CODE_MAP
├── views.py                # handle_toolbox_error — 2.0.x wire format
└── apps.py                 # Django AppConfig
```

The transport, error hierarchy, settings and `handle_toolbox_error` live in `entirius-django-utils`
(`django_utils.toolbox`); this package subclasses the client with the translator endpoints and keeps its earlier
error API and wire format as compat layers over it.

| Topic | Where |
|---|---|
| `ToolboxClient` methods, retries, batching; the error hierarchy and its constructors | `docs/client.md` |
| The `AI_TOOLBOX_*` settings | `django_utils.toolbox` — `docs/toolbox-client.md` of `entirius-django-utils` |
| What changed and why | `CHANGELOG.md` |

## Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `AI_TOOLBOX_*` | see `django_utils.toolbox.settings` | read lazily from Django settings on access |
| `AI_TRANSLATOR_LANGUAGE_CODE_MAP` | built-in map | ISO2 to provider code mapping (e.g. `gb` to `EN-GB`); read once at import, not lazily |

## Gotchas

- httpx logging is suppressed (`WARNING`) by the base client; retry warnings log under `django_utils.toolbox.client`.
- `_ESTIMATE_BATCH_SIZE = 50` — toolbox `/estimate/` endpoint rejects more than 50 items. Client
  auto-chunks and aggregates.
- `map_to_provider_code()` falls back to `lang_code.upper()` for unmapped codes. Override via
  `AI_TRANSLATOR_LANGUAGE_CODE_MAP` in settings.
- `AI_TOOLBOX_ENABLED = False` (the switch of `entirius-django-utils`): `ToolboxClient()` raises
  `ToolboxDisabledError`, not re-typed, and `handle_toolbox_error` answers 503 `AI_TOOLBOX_DISABLED`.
- This package has no Django models and no migrations. It is a dependency of
  `entirius-django-pim-translator` and the ContentDB translator.

# Django Utils Translator

Shared translation infrastructure for Volkanos translator modules: HTTP client for the remote AI
toolbox, unified error hierarchy, base Pydantic request/response schemas, HTML sanitization, and
DRF error mapping. Pure library code — no models, no migrations, no endpoints.

## Quick Start

Requires Python 3.11+.

```bash
make install                     # uv sync, incl. extras
make test                        # pytest (respx-mocked httpx, no database)
```

### Other commands

```bash
make check    # ruff check + format-check
make fix      # auto-fix lint + format
```

## Usage

Add `django_utils_translator` to `INSTALLED_APPS` and set `AI_TOOLBOX_BASE_URL` +
`AI_TOOLBOX_API_KEY` (+ `AI_TOOLBOX_CHANNEL` for the default channel) in settings. The client is a
subclass of `django_utils.toolbox.ToolboxClient` from `entirius-django-utils`.

```python
from django_utils_translator.clients import ToolboxClient

with ToolboxClient() as client:
    estimate = client.estimate(items)
```

## Details

See `AGENTS.md` for architecture, error hierarchy, and settings reference.

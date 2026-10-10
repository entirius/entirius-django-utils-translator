# entirius-django-utils-translator

Shared translation building blocks for the modules of Entirius, the open-source modular ecommerce platform.
The package holds the HTTP client for the translation endpoints of an AI toolbox service, its error classes,
base request and response schemas and HTML sanitising. It has no models, no migrations and no endpoints.

[![PyPI](https://img.shields.io/pypi/v/entirius-django-utils-translator.svg)](https://pypi.org/project/entirius-django-utils-translator/)
[![Python](https://img.shields.io/pypi/pyversions/entirius-django-utils-translator.svg)](https://pypi.org/project/entirius-django-utils-translator/)
[![License: MPL-2.0](https://img.shields.io/badge/license-MPL--2.0-blue.svg)](https://github.com/entirius/entirius-django-utils-translator/blob/develop/LICENSE)

## What it does

- A `ToolboxClient` for the translation endpoints: cost estimates, jobs, job status and results.
- Retries with backoff on transient failures, and batches large estimate requests.
- Typed errors and a DRF mapping (`handle_toolbox_error`) shared by the translator modules.
- Base Pydantic request and response schemas for translate and bulk-translate calls.
- HTML sanitising of translated text and a mapping from language codes to provider codes.

## Installation

```shell
uv add entirius-django-utils-translator
pip install entirius-django-utils-translator
```

```python
INSTALLED_APPS = [
    # ...
    "django_utils",
    "django_utils_translator",
]
```

The client needs a reachable AI toolbox service, configured through `AI_TOOLBOX_BASE_URL`,
`AI_TOOLBOX_API_KEY` and `AI_TOOLBOX_CHANNEL` of `entirius-django-utils`. The toolbox itself is not part of this
package. Settings reference: https://github.com/entirius/entirius-django-utils/blob/develop/docs/toolbox-client.md

`AI_TRANSLATOR_LANGUAGE_CODE_MAP` optionally replaces the built-in map from language codes to provider codes.

## Quick start

```python
from django_utils_translator.clients import ToolboxClient

items = [{"key": "product.1.name", "text": "Garden chair"}]

with ToolboxClient() as client:
    estimate = client.estimate(items, target_languages=["pl"])
```

The client is a subclass of `django_utils.toolbox.ToolboxClient` from `entirius-django-utils`.

## Requirements

- Python 3.11 or newer, Django 5.0 or newer.
- A reachable AI toolbox service (`AI_TOOLBOX_*` settings); no database.
- Entirius packages pulled in: `entirius-django-utils`.

## Documentation

- Module docs: https://github.com/entirius/entirius-django-utils-translator/tree/develop/docs
- Entirius documentation: https://docs.entirius.com/
- Changelog: https://github.com/entirius/entirius-django-utils-translator/blob/develop/CHANGELOG.md

## Part of Entirius

The translator modules of the Entirius backend service (Volkanos) build on this package.

- Backend service: https://github.com/entirius/entirius-service-volkanos
- Docker harness: https://github.com/entirius/entirius-zeno
- Sibling modules: https://github.com/entirius/entirius-django-pim-translator,
  https://github.com/entirius/entirius-django-contentdb-translator, https://github.com/entirius/entirius-django-utils

## Development

```shell
make install     # sync dependencies (uv, incl. extras)
make check       # lint + format check (ruff)
make test        # test suite (pytest; httpx mocked with respx, no database)
```

Development and agent instructions: https://github.com/entirius/entirius-django-utils-translator/blob/develop/AGENTS.md

## License

Mozilla Public License 2.0 (MPL-2.0) — see https://github.com/entirius/entirius-django-utils-translator/blob/develop/LICENSE.

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Every import path used by entirius-django-pim-translator and entirius-django-contentdb-translator resolves."""

import importlib

import pytest

CONSUMER_IMPORTS = [
    ("django_utils_translator.clients", "ToolboxClient"),
    ("django_utils_translator.clients", "ToolboxError"),
    ("django_utils_translator.clients", "ToolboxAuthError"),
    ("django_utils_translator.clients", "ToolboxBudgetExceededError"),
    ("django_utils_translator.clients", "ToolboxConnectionError"),
    ("django_utils_translator.clients", "ToolboxNotFoundError"),
    ("django_utils_translator.clients", "ToolboxRateLimitError"),
    ("django_utils_translator.clients", "ToolboxServerError"),
    ("django_utils_translator.clients", "ToolboxValidationError"),
    ("django_utils_translator.views", "handle_toolbox_error"),
    ("django_utils_translator.sanitize", "sanitize"),
    ("django_utils_translator.schemas.requests", "BaseTranslateRequest"),
    ("django_utils_translator.schemas.responses", "BulkTranslateJobResponse"),
    ("django_utils_translator.schemas.responses", "BulkTranslateEstimateResponse"),
    ("django_utils_translator.schemas.responses", "LanguageCostEstimate"),
    ("django_utils_translator.settings", "AI_TOOLBOX_API_KEY"),
    ("django_utils_translator.settings", "AI_TOOLBOX_BASE_URL"),
    ("django_utils_translator.settings", "AI_TOOLBOX_MAX_RETRIES"),
    ("django_utils_translator.settings", "AI_TOOLBOX_TIMEOUT"),
    ("django_utils_translator.settings", "LANGUAGE_CODE_MAP"),
    ("django_utils_translator.settings", "map_to_provider_code"),
]


@pytest.mark.parametrize(("module", "name"), CONSUMER_IMPORTS)
def test_consumer_import_path_resolves(module, name):
    assert getattr(importlib.import_module(module), name) is not None


def test_settings_are_read_lazily(settings):
    from django_utils_translator import settings as translator_settings

    settings.AI_TOOLBOX_BASE_URL = "https://changed.test.internal"

    assert translator_settings.AI_TOOLBOX_BASE_URL == "https://changed.test.internal"


def test_consumer_call_shape_single_attempt(settings):
    from django_utils_translator.clients import ToolboxClient

    with ToolboxClient("europe", max_retries=1) as client:
        assert client._max_retries == 1

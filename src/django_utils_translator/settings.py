# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Shared settings for AI translation modules.

``AI_TOOLBOX_*`` are re-exported lazily from ``django_utils.toolbox.settings`` (documented there).
"""

from typing import Any

from django.conf import settings
from django_utils.toolbox import settings as toolbox_settings


def __getattr__(name: str) -> Any:
    return getattr(toolbox_settings, name)


# Language code → provider language code (DeepL format).
# Override in Django settings as AI_TRANSLATOR_LANGUAGE_CODE_MAP.
LANGUAGE_CODE_MAP: dict[str, str] = getattr(
    settings,
    "AI_TRANSLATOR_LANGUAGE_CODE_MAP",
    {
        "gb": "EN-GB",
        "us": "EN-US",
        "en": "EN",
        "de": "DE",
        "fr": "FR",
        "pl": "PL",
        "es": "ES",
        "it": "IT",
        "nl": "NL",
        "cs": "CS",
        "da": "DA",
        "fi": "FI",
        "hu": "HU",
        "ja": "JA",
        "ko": "KO",
        "nb": "NB",
        "pt": "PT-PT",
        "ro": "RO",
        "sk": "SK",
        "sv": "SV",
        "zh": "ZH",
    },
)


def map_to_provider_code(lang_code: str) -> str:
    """Map internal language code to provider language code."""
    return LANGUAGE_CODE_MAP.get(lang_code, lang_code.upper())

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Shared settings for AI translation modules.

Required in service settings_local.py:
    AI_TOOLBOX_BASE_URL = "https://ai-toolbox.internal:8000"
    AI_TOOLBOX_API_KEY = "ent_live_AbCdEf..."
"""

from django.conf import settings

AI_TOOLBOX_BASE_URL: str = getattr(settings, "AI_TOOLBOX_BASE_URL", "")
AI_TOOLBOX_API_KEY: str = getattr(settings, "AI_TOOLBOX_API_KEY", "")
AI_TOOLBOX_TIMEOUT: float = getattr(settings, "AI_TOOLBOX_TIMEOUT", 60.0)
AI_TOOLBOX_MAX_RETRIES: int = getattr(settings, "AI_TOOLBOX_MAX_RETRIES", 3)

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

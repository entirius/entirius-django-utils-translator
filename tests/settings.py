# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Standalone Django settings for django-utils-translator tests. No database required."""

SECRET_KEY = "test-secret-key-for-utils-translator"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "django_utils_translator",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

# Toolbox client settings for tests.
AI_TOOLBOX_BASE_URL = "https://toolbox.test.internal"
AI_TOOLBOX_API_KEY = "dummy"
AI_TOOLBOX_TIMEOUT = 5.0
AI_TOOLBOX_MAX_RETRIES = 3

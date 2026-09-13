# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The translator's error hierarchy is the shared one from django_utils.toolbox."""

import django_utils.toolbox.errors as shared_errors
import pytest

from django_utils_translator.clients import errors


@pytest.mark.parametrize("name", errors.__all__)
def test_error_is_reexported_from_django_utils(name):
    assert getattr(errors, name) is getattr(shared_errors, name)


def test_every_error_is_a_toolbox_error():
    for name in errors.__all__:
        assert issubclass(getattr(errors, name), errors.ToolboxError)


def test_base_error_attributes():
    exc = errors.ToolboxError(500, "Server error", code="INTERNAL_ERROR", field_errors={"x": ["bad"]})

    assert (exc.status_code, exc.message, exc.code, exc.field_errors) == (
        500,
        "Server error",
        "INTERNAL_ERROR",
        {"x": ["bad"]},
    )
    assert "500" in str(exc)


def test_rate_limit_keeps_retry_after():
    exc = errors.ToolboxRateLimitError(429, "Rate limited", retry_after=30.0)

    assert exc.retry_after == 30.0

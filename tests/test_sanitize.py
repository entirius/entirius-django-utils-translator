# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for HTML sanitization."""

from django_utils_translator.sanitize import sanitize


class TestSanitize:
    def test_strips_script_tags(self):
        result = sanitize('<p>Hello</p><script>alert("xss")</script>')
        assert "<script>" not in result
        assert "Hello" in result

    def test_strips_event_handlers(self):
        result = sanitize('<img onerror="alert(1)" src="x">')
        assert "onerror" not in result

    def test_preserves_safe_html(self):
        html = "<b>bold</b> and <i>italic</i>"
        result = sanitize(html)
        assert "<b>bold</b>" in result
        assert "<i>italic</i>" in result

    def test_plain_text_passthrough(self):
        text = "Plain text with no HTML"
        assert sanitize(text) == text

    def test_empty_string(self):
        assert sanitize("") == ""

    def test_strips_javascript_url(self):
        result = sanitize('<a href="javascript:alert(1)">click</a>')
        assert "javascript:" not in result

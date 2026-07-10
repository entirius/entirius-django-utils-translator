# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Text sanitization for translated content."""

import nh3


def sanitize(text: str) -> str:
    """Sanitize translated text to prevent stored XSS."""
    return nh3.clean(text)

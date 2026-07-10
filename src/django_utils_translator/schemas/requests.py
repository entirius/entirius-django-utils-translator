# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Base Pydantic request schemas for translation modules."""

from pydantic import BaseModel, Field


class BaseTranslateRequest(BaseModel):
    """Common fields for all translation requests."""

    target_languages: list[str] = Field(
        min_length=1, description="Target language codes (e.g. de, fr, it)", examples=[["de", "fr"]]
    )
    source_language: str | None = Field(
        default=None, description="Source language code. Defaults to channel default.", examples=["en"]
    )
    provider: str | None = Field(default=None, description="Provider override (deepl or gemini).", examples=["deepl"])
    formality: str | None = Field(
        default=None, description="Formality level (more, less, default). Provider-dependent.", examples=["more"]
    )
    context: str | None = Field(
        default=None, description="Domain context for better translation quality.", examples=["E-commerce store"]
    )
    dry_run: bool = Field(
        default=False,
        description="When true, returns cost estimate without calling the provider.",
        examples=[False],
    )

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Base Pydantic response schemas for translation modules."""

from decimal import Decimal

from pydantic import BaseModel, Field


class LanguageCostEstimate(BaseModel):
    """Per-language cost breakdown — included in estimate responses."""

    language: str = Field(description="Language code", examples=["de"])
    items: int = Field(description="Number of text items for this language", examples=[6])
    chars: int = Field(description="Total characters for this language", examples=[1710])
    cost_usd: Decimal | None = Field(description="Estimated cost in USD", examples=["0.03420000"])


class BulkTranslateJobResponse(BaseModel):
    """Response 202 — translation job(s) created."""

    entity_type: str = Field(description="Entity type being translated", examples=["page"])
    job_ids: list[str] = Field(
        description="Translation job UUIDs (one per target language)",
        examples=[["a1b2c3d4-e5f6-7890-abcd-ef1234567890"]],
    )
    estimated_items: int = Field(description="Total items per language", examples=[187])
    estimated_cost_usd: Decimal | None = Field(description="Estimated total cost", examples=["0.90400"])
    status: str = Field(default="pending", description="Initial job status", examples=["pending"])
    target_languages: list[str] = Field(description="Target language codes", examples=[["de", "fr"]])


class BulkTranslateEstimateResponse(BaseModel):
    """Response 200 — bulk cost estimate (dry_run=True). No job created."""

    entity_type: str = Field(description="Entity type estimated", examples=["page"])
    estimated_items: int = Field(description="Total items that would be translated", examples=[187])
    total_chars: int = Field(description="Total characters across all languages", examples=[45200])
    estimated_cost_usd: Decimal | None = Field(description="Estimated total cost", examples=["0.90400"])
    target_languages: list[str] = Field(description="Target language codes", examples=[["de", "fr"]])
    per_language: list[LanguageCostEstimate] = Field(description="Per-language cost breakdown")

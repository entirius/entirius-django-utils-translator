# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Translator endpoints on top of the shared toolbox client (``django_utils.toolbox``).

Owns zero business logic. Transport, retry, errors and settings live in the base client.
The toolbox is the single source of truth for jobs, costs, usage, translations.
"""

from __future__ import annotations

from decimal import Decimal

from django_utils.toolbox import ToolboxClient as BaseToolboxClient

_DEFAULT_PROVIDER = "deepl"
_TRANSLATOR_TOOL = "ai-translator"


class ToolboxClient(BaseToolboxClient):
    """Synchronous HTTP client for the AI toolbox translator API.

    Usage::

        with ToolboxClient("europe") as client:
            result = client.estimate(items, ["DE", "FR"])
    """

    _ESTIMATE_BATCH_SIZE = 50  # Toolbox /estimate/ accepts max 50 items per request.

    # --- Translator endpoints ---

    def estimate(
        self,
        items: list[dict],
        target_languages: list[str],
        provider: str | None = None,
    ) -> dict:
        """POST /estimate/ — cost estimate without calling provider.

        Automatically chunks items into batches of 50 (toolbox limit) and
        aggregates per-language costs when the item list exceeds the limit.
        """
        if len(items) <= self._ESTIMATE_BATCH_SIZE:
            payload: dict = {
                "items": items,
                "target_languages": target_languages,
                "provider": provider or _DEFAULT_PROVIDER,
            }
            return self._post(self._translator_url("estimate/"), payload)

        return self._estimate_chunked(items, target_languages, provider)

    def _estimate_chunked(
        self,
        items: list[dict],
        target_languages: list[str],
        provider: str | None,
    ) -> dict:
        """Split items into batches of 50, call /estimate/ for each, aggregate costs."""
        per_lang_totals: dict[str, dict] = {}
        total_cost = Decimal("0")

        for offset in range(0, len(items), self._ESTIMATE_BATCH_SIZE):
            batch = items[offset : offset + self._ESTIMATE_BATCH_SIZE]
            payload: dict = {
                "items": batch,
                "target_languages": target_languages,
                "provider": provider or _DEFAULT_PROVIDER,
            }
            chunk_result = self._post(self._translator_url("estimate/"), payload)
            self._accumulate_chunk(per_lang_totals, chunk_result)
            chunk_total = chunk_result.get("total_cost_usd")
            if chunk_total is not None:
                total_cost += Decimal(str(chunk_total))

        per_language = [
            {
                "language": v["language"],
                "total_chars": v["total_chars"],
                "estimated_cost_usd": str(v["estimated_cost_usd"]),
            }
            for v in per_lang_totals.values()
        ]
        return {"per_language": per_language, "total_cost_usd": str(total_cost)}

    @staticmethod
    def _accumulate_chunk(totals: dict[str, dict], chunk_result: dict) -> None:
        """Merge one chunk's per-language costs into running totals, keyed by language code."""
        for lang_data in chunk_result.get("per_language", []):
            lang = lang_data.get("language", "")
            if lang not in totals:
                totals[lang] = {"language": lang, "total_chars": 0, "estimated_cost_usd": Decimal("0")}
            totals[lang]["total_chars"] += lang_data.get("total_chars", 0)
            cost = lang_data.get("estimated_cost_usd")
            if cost is not None:
                totals[lang]["estimated_cost_usd"] += Decimal(str(cost))

    def create_job(
        self,
        items: list[dict],
        target_language: str,
        source_language: str | None = None,
        provider: str | None = None,
        formality: str | None = None,
        context: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """POST /jobs/ — create async translation job. Returns 202."""
        payload: dict = {"items": items, "target_language": target_language, "provider": provider or _DEFAULT_PROVIDER}
        if source_language:
            payload["source_language"] = source_language
        if formality:
            payload["formality"] = formality
        if context:
            payload["context"] = context
        if metadata:
            payload["metadata"] = metadata
        return self._post(self._translator_url("jobs/"), payload)

    def get_job(self, job_id: str) -> dict:
        """GET /jobs/{id}/ — poll job status."""
        return self._get(self._translator_url(f"jobs/{job_id}/"))

    def get_job_results(self, job_id: str, page: int = 1, page_size: int = 100) -> dict:
        """GET /jobs/{id}/results/ — fetch completed job results (paginated)."""
        return self._get(self._translator_url(f"jobs/{job_id}/results/"), params={"page": page, "page_size": page_size})

    def list_jobs(self, status: str | None = None, page: int = 1) -> dict:
        """GET /jobs/ — list jobs for channel."""
        params: dict = {"page": page}
        if status:
            params["status"] = status
        return self._get(self._translator_url("jobs/"), params=params)

    # --- URL helpers ---

    def _translator_url(self, path: str) -> str:
        return self._url(_TRANSLATOR_TOOL, path)

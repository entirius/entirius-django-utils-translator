# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Thin HTTP client for the remote AI toolbox service.

Owns zero business logic. Sends requests, maps errors, returns parsed JSON.
The toolbox is the single source of truth for jobs, costs, usage, translations.
"""

from __future__ import annotations

import logging
import re
import time
from decimal import Decimal

import httpx

from django_utils_translator.settings import (
    AI_TOOLBOX_API_KEY,
    AI_TOOLBOX_BASE_URL,
    AI_TOOLBOX_MAX_RETRIES,
    AI_TOOLBOX_TIMEOUT,
)

from .errors import (
    ToolboxAuthError,
    ToolboxBudgetExceededError,
    ToolboxConnectionError,
    ToolboxError,
    ToolboxNotFoundError,
    ToolboxRateLimitError,
    ToolboxServerError,
    ToolboxValidationError,
)

logger = logging.getLogger("process")

# Suppress httpx debug logging — prevents API key leak in X-API-Key header.
logging.getLogger("httpx").setLevel(logging.WARNING)

_RETRYABLE_STATUSES: frozenset[int] = frozenset({408, 429, 500, 502, 503, 504})
_RETRY_BASE_DELAY = 2.0
_RETRY_MAX_DELAY = 60.0
_DEFAULT_PROVIDER = "deepl"
_CHANNEL_IDX_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


class ToolboxClient:
    """Synchronous HTTP client for the AI toolbox REST API.

    Usage::

        with ToolboxClient("europe") as client:
            result = client.estimate(items, ["DE", "FR"])
    """

    _ESTIMATE_BATCH_SIZE = 50  # Toolbox /estimate/ accepts max 50 items per request.

    def __init__(self, channel_idx: str, max_retries: int | None = None) -> None:
        if not AI_TOOLBOX_BASE_URL:
            raise ValueError("AI_TOOLBOX_BASE_URL is not configured in Django settings.")
        if not AI_TOOLBOX_API_KEY:
            raise ValueError("AI_TOOLBOX_API_KEY is not configured in Django settings.")
        if not _CHANNEL_IDX_PATTERN.match(channel_idx):
            raise ValueError(f"Invalid channel_idx: {channel_idx!r}")

        self._channel_idx = channel_idx
        self._max_retries = max_retries if max_retries is not None else AI_TOOLBOX_MAX_RETRIES
        self._base_url = AI_TOOLBOX_BASE_URL.rstrip("/")
        self._client = httpx.Client(
            headers={"X-API-Key": AI_TOOLBOX_API_KEY},
            timeout=AI_TOOLBOX_TIMEOUT,
        )

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
        return f"{self._base_url}/api/ai-translator/v2/admin/{self._channel_idx}/{path}"

    # --- Transport ---

    def _get(self, url: str, params: dict | None = None) -> dict:
        return self._request("GET", url, params=params)

    def _post(self, url: str, payload: dict) -> dict:
        return self._request("POST", url, json=payload)

    def _request(self, method: str, url: str, **kwargs) -> dict:
        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                response = self._client.request(method, url, **kwargs)
                self._raise_for_status(response)
                return response.json()
            except ToolboxError as exc:
                last_error = exc
                if not self._is_retryable(exc):
                    raise
                self._sleep_before_retry(attempt, exc)
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt >= self._max_retries - 1:
                    break
                self._sleep_before_retry(attempt, None)

        if isinstance(last_error, ToolboxError):
            raise last_error
        raise ToolboxConnectionError(type(last_error).__name__ if last_error else "unknown")

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_success:
            return

        status = response.status_code
        body = self._safe_json(response)
        message = body.get("message", response.text[:200])

        if status in (401, 403):
            raise ToolboxAuthError()
        if status == 402:
            raise ToolboxBudgetExceededError(message)
        if status == 404:
            raise ToolboxNotFoundError(message)
        if status == 429:
            retry_after = response.headers.get("Retry-After")
            raise ToolboxRateLimitError(float(retry_after) if retry_after else None)
        if status == 400:
            raise ToolboxValidationError(message=message, details=body.get("details", []))
        if status >= 500:
            raise ToolboxServerError(status, message)
        raise ToolboxError(status, message)

    def _is_retryable(self, error: ToolboxError) -> bool:
        if isinstance(
            error, (ToolboxAuthError, ToolboxValidationError, ToolboxNotFoundError, ToolboxBudgetExceededError)
        ):
            return False
        return error.status_code in _RETRYABLE_STATUSES

    def _sleep_before_retry(self, attempt: int, error: ToolboxError | None) -> None:
        if isinstance(error, ToolboxRateLimitError) and error.retry_after is not None:
            delay = min(error.retry_after, _RETRY_MAX_DELAY)
        else:
            delay = min(_RETRY_BASE_DELAY * (2**attempt), _RETRY_MAX_DELAY)
        logger.warning(
            "Toolbox request failed (attempt %d/%d), retrying in %.1fs", attempt + 1, self._max_retries, delay
        )
        time.sleep(delay)

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict:
        try:
            return response.json()
        except (ValueError, TypeError):
            return {}

    # --- Lifecycle ---

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ToolboxClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

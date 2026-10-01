import hashlib
from dataclasses import dataclass
from typing import Any, Optional

import requests

from db import get_source_state, upsert_source_state


STRATEGY_ORDER = (
    "api",
    "rss",
    "sitemap",
    "jsonld",
    "html",
    "browser",
    "search",
    "email",
)


@dataclass
class FetchResult:
    url: str
    status_code: int
    text: str
    changed: bool
    not_modified: bool
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    content_hash: Optional[str] = None


class StatefulHttpFetcher:
    """Conditional public HTTP fetcher with persistent ETag/hash state.

    It does not bypass authentication, CAPTCHA, rate limits, or access controls.
    """

    def __init__(
        self,
        *,
        source_name: str,
        client=None,
        session: Optional[requests.Session] = None,
        strategy: str = "html",
        timeout: int = 25,
    ):
        self.source_name = source_name
        self.client = client
        self.session = session or requests.Session()
        self.strategy = strategy
        self.timeout = timeout

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

    def fetch(self, url: str) -> FetchResult:
        state: dict[str, Any] | None = None
        headers: dict[str, str] = {}

        if self.client is not None:
            state = get_source_state(
                self.client,
                source_name=self.source_name,
                url=url,
                strategy=self.strategy,
            )
            if state:
                if state.get("etag"):
                    headers["If-None-Match"] = str(state["etag"])
                if state.get("last_modified"):
                    headers["If-Modified-Since"] = str(state["last_modified"])

        response = self.session.get(url, headers=headers, timeout=self.timeout)

        if response.status_code == 304:
            if self.client is not None:
                upsert_source_state(
                    self.client,
                    source_name=self.source_name,
                    url=url,
                    strategy=self.strategy,
                    etag=state.get("etag") if state else None,
                    last_modified=state.get("last_modified") if state else None,
                    content_hash=state.get("content_hash") if state else None,
                    last_http_status=304,
                    changed=False,
                    last_changed_at=state.get("last_changed_at") if state else None,
                )
            return FetchResult(
                url=url,
                status_code=304,
                text="",
                changed=False,
                not_modified=True,
                etag=state.get("etag") if state else None,
                last_modified=state.get("last_modified") if state else None,
                content_hash=state.get("content_hash") if state else None,
            )

        response.raise_for_status()
        text = response.text
        digest = self._hash(text)
        previous_hash = state.get("content_hash") if state else None
        changed = digest != previous_hash

        etag = response.headers.get("ETag")
        last_modified = response.headers.get("Last-Modified")

        if self.client is not None:
            upsert_source_state(
                self.client,
                source_name=self.source_name,
                url=url,
                strategy=self.strategy,
                etag=etag,
                last_modified=last_modified,
                content_hash=digest,
                last_http_status=response.status_code,
                changed=changed,
                last_changed_at=state.get("last_changed_at") if state else None,
            )

        return FetchResult(
            url=url,
            status_code=response.status_code,
            text=text,
            changed=changed,
            not_modified=False,
            etag=etag,
            last_modified=last_modified,
            content_hash=digest,
        )


class FallbackSource:
    """Runs public acquisition adapters in priority order until one succeeds."""

    def __init__(self, name: str, adapters: list[tuple[str, object]]):
        self.name = name
        order = {strategy: i for i, strategy in enumerate(STRATEGY_ORDER)}
        self.adapters = sorted(
            adapters,
            key=lambda pair: order.get(pair[0], len(order)),
        )
        self.active_strategy: Optional[str] = None

    def configure_runtime(self, client) -> None:
        for _, adapter in self.adapters:
            configure = getattr(adapter, "configure_runtime", None)
            if configure:
                configure(client)

    def fetch(self):
        errors: list[str] = []
        for strategy, adapter in self.adapters:
            try:
                jobs = list(adapter.fetch())
                self.active_strategy = strategy
                for job in jobs:
                    yield job
                return
            except Exception as exc:
                errors.append(f"{strategy}: {exc}")
        raise RuntimeError("; ".join(errors) or "No acquisition adapters configured")

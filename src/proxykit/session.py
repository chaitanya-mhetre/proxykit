from __future__ import annotations

import asyncio
import random
from collections.abc import Mapping
from typing import Any

import httpx

from proxykit.models import ProxySpec
from proxykit.rotator import ProxyRotator


class ScrapingSession:
    """Async scraping helper with proxy rotation, retries, and backoff."""

    def __init__(
        self,
        rotator: ProxyRotator,
        *,
        timeout: float = 15.0,
        max_retries: int = 3,
        backoff_base: float = 0.6,
        headers: Mapping[str, str] | None = None,
        rotate_on_status: set[int] | None = None,
    ) -> None:
        self.rotator = rotator
        self.timeout = timeout
        self.max_retries = max(1, max_retries)
        self.backoff_base = backoff_base
        self.headers = dict(headers or {"User-Agent": "ProxyKit-Scraper/1.0"})
        self.rotate_on_status = rotate_on_status or {403, 407, 429, 500, 502, 503, 504}

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            proxy = self.rotator.next()
            try:
                async with httpx.AsyncClient(
                    proxy=proxy.url,
                    timeout=self.timeout,
                    headers=self.headers,
                    follow_redirects=True,
                ) as client:
                    response = await client.request(method, url, **kwargs)
                    if response.status_code in self.rotate_on_status:
                        self.rotator.mark_bad(proxy)
                        raise httpx.HTTPStatusError(
                            f"rotating on status {response.status_code}",
                            request=response.request,
                            response=response,
                        )
                    return response
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                try:
                    self.rotator.mark_bad(proxy)
                except ValueError:
                    # No proxies left; fall through to raise below.
                    pass
                delay = self.backoff_base * (2**attempt) + random.uniform(0, 0.25)
                await asyncio.sleep(delay)

        raise RuntimeError(f"request failed after {self.max_retries} retries: {last_error}")

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    def get_sync(self, url: str, **kwargs: Any) -> httpx.Response:
        return asyncio.run(self.get(url, **kwargs))


def build_rotator_from_specs(proxies: list[ProxySpec], strategy: str = "round_robin") -> ProxyRotator:
    return ProxyRotator(proxies, strategy=strategy, alive_only=False)

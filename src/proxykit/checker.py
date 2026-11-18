from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Iterable, Sequence
from pathlib import Path

import httpx

from proxykit.anonymity import compute_score, score_anonymity
from proxykit.models import AnonymityLevel, ProxyResult, ProxySpec, ProxyType

DEFAULT_JUDGE_URL = "https://httpbin.org/get"
IP_LOOKUP_URL = "https://api.ipify.org?format=json"


class ProxyChecker:
    """Concurrent proxy validator with latency + anonymity scoring."""

    def __init__(
        self,
        *,
        timeout: float = 10.0,
        concurrency: int = 50,
        judge_url: str = DEFAULT_JUDGE_URL,
        user_agent: str = "ProxyKit/1.0 (+https://github.com/chaitanya-mhetre/proxykit)",
    ) -> None:
        self.timeout = timeout
        self.concurrency = max(1, concurrency)
        self.judge_url = judge_url
        self.user_agent = user_agent

    @staticmethod
    def load_proxies(
        source: str | Path | Sequence[str],
        *,
        default_type: ProxyType = ProxyType.HTTP,
    ) -> list[ProxySpec]:
        lines: list[str]
        if isinstance(source, (str, Path)) and Path(source).exists():
            lines = Path(source).read_text(encoding="utf-8").splitlines()
        elif isinstance(source, str):
            lines = source.splitlines()
        else:
            lines = list(source)

        proxies: list[ProxySpec] = []
        seen: set[str] = set()
        for line in lines:
            item = line.strip()
            if not item or item.startswith("#"):
                continue
            try:
                proxy = ProxySpec.parse(item, default_type=default_type)
            except ValueError:
                continue
            key = proxy.url
            if key in seen:
                continue
            seen.add(key)
            proxies.append(proxy)
        return proxies

    async def get_real_ip(self) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(IP_LOOKUP_URL)
                response.raise_for_status()
                return str(response.json().get("ip") or "")
        except Exception:
            return None

    async def check_one(self, proxy: ProxySpec, real_ip: str | None = None) -> ProxyResult:
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                proxy=proxy.url,
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            ) as client:
                response = await client.get(self.judge_url)
                latency_ms = (time.perf_counter() - started) * 1000.0
                response.raise_for_status()

                payload: dict = {}
                try:
                    payload = response.json()
                except json.JSONDecodeError:
                    payload = {}

                headers = payload.get("headers") if isinstance(payload.get("headers"), dict) else dict(response.headers)
                origin = payload.get("origin")
                exit_ip = None
                if isinstance(origin, str):
                    exit_ip = origin.split(",")[0].strip()

                anonymity, leaked = score_anonymity(headers, real_ip, exit_ip)
                score = compute_score(True, latency_ms, anonymity)
                return ProxyResult(
                    proxy=proxy,
                    alive=True,
                    latency_ms=round(latency_ms, 2),
                    anonymity=anonymity,
                    status_code=response.status_code,
                    exit_ip=exit_ip,
                    error=None,
                    score=score,
                    headers_leaked=leaked,
                )
        except Exception as exc:  # noqa: BLE001 - collect any proxy failure reason
            latency_ms = (time.perf_counter() - started) * 1000.0
            return ProxyResult(
                proxy=proxy,
                alive=False,
                latency_ms=round(latency_ms, 2),
                anonymity=AnonymityLevel.UNKNOWN,
                error=str(exc)[:240],
                score=0.0,
            )

    async def check_many(self, proxies: Iterable[ProxySpec]) -> list[ProxyResult]:
        items = list(proxies)
        if not items:
            return []

        real_ip = await self.get_real_ip()
        semaphore = asyncio.Semaphore(self.concurrency)

        async def _run(proxy: ProxySpec) -> ProxyResult:
            async with semaphore:
                return await self.check_one(proxy, real_ip=real_ip)

        results = await asyncio.gather(*[_run(proxy) for proxy in items])
        return sorted(results, key=lambda r: (-r.score, r.latency_ms or 999999))

    def check(self, proxies: Iterable[ProxySpec]) -> list[ProxyResult]:
        return asyncio.run(self.check_many(proxies))

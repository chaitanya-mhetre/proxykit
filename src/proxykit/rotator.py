from __future__ import annotations

import itertools
import random
from collections.abc import Sequence

from proxykit.models import ProxyResult, ProxySpec


class ProxyRotator:
    """Round-robin / random proxy rotation with optional health filtering."""

    def __init__(
        self,
        proxies: Sequence[ProxySpec] | Sequence[ProxyResult],
        *,
        strategy: str = "round_robin",
        alive_only: bool = True,
    ) -> None:
        self.strategy = strategy
        self._proxies = self._normalize(proxies, alive_only=alive_only)
        if not self._proxies:
            raise ValueError("ProxyRotator requires at least one proxy")
        self._cycle = itertools.cycle(self._proxies)

    @staticmethod
    def _normalize(
        proxies: Sequence[ProxySpec] | Sequence[ProxyResult],
        *,
        alive_only: bool,
    ) -> list[ProxySpec]:
        out: list[ProxySpec] = []
        for item in proxies:
            if isinstance(item, ProxyResult):
                if alive_only and not item.alive:
                    continue
                out.append(item.proxy)
            else:
                out.append(item)
        return out

    @property
    def proxies(self) -> list[ProxySpec]:
        return list(self._proxies)

    def next(self) -> ProxySpec:
        if self.strategy == "random":
            return random.choice(self._proxies)
        return next(self._cycle)

    def mark_bad(self, proxy: ProxySpec) -> None:
        self._proxies = [p for p in self._proxies if p.url != proxy.url]
        if not self._proxies:
            raise ValueError("No healthy proxies remaining")
        self._cycle = itertools.cycle(self._proxies)

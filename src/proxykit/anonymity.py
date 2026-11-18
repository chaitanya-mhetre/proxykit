from __future__ import annotations

from typing import Any

from proxykit.models import AnonymityLevel

# Headers that reveal the real client when a proxy is transparent.
LEAK_HEADERS = (
    "via",
    "x-forwarded-for",
    "forwarded",
    "x-real-ip",
    "client-ip",
    "true-client-ip",
    "x-proxy-id",
    "proxy-connection",
)


def score_anonymity(
    response_headers: dict[str, Any],
    real_ip: str | None,
    exit_ip: str | None,
) -> tuple[AnonymityLevel, list[str]]:
    """Classify proxy anonymity from echo/IP-check response headers.

    - elite: exit IP differs from real IP and no proxy leak headers
    - anonymous: exit IP differs but proxy-related headers are present
    - transparent: real IP appears in response headers / body fields
    """
    normalized = {str(k).lower(): str(v) for k, v in response_headers.items()}
    leaked = [name for name in LEAK_HEADERS if name in normalized]

    joined = " ".join(normalized.values())
    if real_ip and real_ip in joined:
        return AnonymityLevel.TRANSPARENT, leaked

    if exit_ip and real_ip and exit_ip == real_ip:
        return AnonymityLevel.TRANSPARENT, leaked

    if leaked:
        return AnonymityLevel.ANONYMOUS, leaked

    if exit_ip and real_ip and exit_ip != real_ip:
        return AnonymityLevel.ELITE, leaked

    return AnonymityLevel.UNKNOWN, leaked


def compute_score(alive: bool, latency_ms: float | None, anonymity: AnonymityLevel) -> float:
    """Return 0–100 quality score for ranking proxies."""
    if not alive or latency_ms is None:
        return 0.0

    # Faster proxies score higher; 0ms → 60, 5000ms → ~0
    latency_score = max(0.0, 60.0 - (latency_ms / 5000.0) * 60.0)
    anonymity_bonus = {
        AnonymityLevel.ELITE: 40.0,
        AnonymityLevel.ANONYMOUS: 25.0,
        AnonymityLevel.TRANSPARENT: 10.0,
        AnonymityLevel.UNKNOWN: 15.0,
    }[anonymity]
    return round(min(100.0, latency_score + anonymity_bonus), 2)

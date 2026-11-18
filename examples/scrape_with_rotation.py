"""Example: fetch a page through rotating proxies with retries."""

import asyncio
from pathlib import Path

from proxykit import ProxyChecker, ProxyRotator, ScrapingSession

SAMPLE = Path(__file__).resolve().parents[1] / "samples" / "proxies.txt"


async def main() -> None:
    proxies = ProxyChecker.load_proxies(SAMPLE)
    # For demos without live proxies, this will fail — replace samples/proxies.txt with real ones.
    rotator = ProxyRotator(proxies, alive_only=False, strategy="round_robin")
    session = ScrapingSession(rotator, max_retries=3, timeout=12)
    response = await session.get("https://httpbin.org/ip")
    print(response.status_code, response.text)


if __name__ == "__main__":
    asyncio.run(main())

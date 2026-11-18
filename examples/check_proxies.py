"""Example: validate a proxy list and print top scores."""

from pathlib import Path

from proxykit import ProxyChecker

SAMPLE = Path(__file__).resolve().parents[1] / "samples" / "proxies.txt"


def main() -> None:
    checker = ProxyChecker(timeout=8, concurrency=30)
    proxies = checker.load_proxies(SAMPLE)
    print(f"Loaded {len(proxies)} proxies from {SAMPLE.name}")
    results = checker.check(proxies)
    alive = [r for r in results if r.alive]
    print(f"Alive: {len(alive)} / {len(results)}")
    for item in results[:10]:
        print(
            f"{item.proxy} | alive={item.alive} | "
            f"latency={item.latency_ms}ms | anonymity={item.anonymity.value} | score={item.score}"
        )


if __name__ == "__main__":
    main()

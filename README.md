# ProxyKit

**Fast proxy validation, anonymity scoring, and scraping session rotation for Python.**

Built for scraper / anti-bot / proxy workflows: check large lists concurrently, rank by quality, then rotate healthy proxies with retries and backoff.

## Why ProxyKit?

| Feature | What you get |
|--------|---------------|
| Multi-protocol | HTTP, HTTPS, SOCKS4, SOCKS5 |
| Concurrent checks | Async validation with configurable concurrency |
| Anonymity scoring | Elite / Anonymous / Transparent detection |
| Quality score | 0–100 rank from latency + anonymity |
| Scraping sessions | Rotation, retries, status-based failover |
| CLI + library | Use as `proxykit` CLI or import in Python |
| Exports | JSON, CSV, alive-only proxy lists |

## Install

```bash
pip install -e .
# or
pip install -r requirements.txt
pip install -e .
```

Dev / tests:

```bash
pip install -e ".[dev]"
pytest -q
```

## Quick start (CLI)

```bash
# Validate a proxy list
proxykit check samples/proxies.txt --concurrency 40 --alive-only

# Export results
proxykit check samples/proxies.txt --json out.json --csv out.csv --alive alive.txt

# Fetch a URL through rotating proxies
proxykit fetch https://httpbin.org/ip -f alive.txt --strategy round_robin
```

## Quick start (Python)

```python
from proxykit import ProxyChecker, ProxyRotator, ScrapingSession

checker = ProxyChecker(timeout=10, concurrency=50)
proxies = checker.load_proxies("samples/proxies.txt")
results = checker.check(proxies)

alive = [r for r in results if r.alive]
for r in alive[:5]:
    print(r.proxy, r.latency_ms, r.anonymity.value, r.score)

rotator = ProxyRotator(alive, strategy="round_robin")
session = ScrapingSession(rotator, max_retries=3)
response = session.get_sync("https://httpbin.org/ip")
print(response.json())
```

## Proxy formats supported

```
host:port
user:pass@host:port
host:port:user:pass
http://host:port
socks5://user:pass@host:port
```

## Anonymity levels

- **elite** — exit IP differs from yours, no leak headers
- **anonymous** — exit IP differs, but proxy headers like `Via` / `X-Forwarded-For` appear
- **transparent** — your real IP is exposed

Scores combine anonymity quality with latency so you can sort usable proxies quickly.

## Project layout

```
src/proxykit/
  checker.py      # concurrent validation
  anonymity.py    # leak detection + scoring
  rotator.py      # round-robin / random rotation
  session.py      # scraping requests with retries
  exporters.py    # JSON / CSV / alive list
  cli.py          # Typer + Rich CLI
examples/         # runnable demos
tests/            # unit tests
```

## Limitations (honest)

- Sample proxies in `samples/proxies.txt` are localhost placeholders — replace with real proxies for live checks.
- Anonymity classification depends on the judge endpoint response shape (default: `httpbin.org/get`).
- This tool does **not** bypass CAPTCHAs, Cloudflare challenges, or site ToS. Use only on targets you are allowed to access.
- SOCKS support requires `httpx[socks]` (included in project dependencies).

## License

MIT © 2026 Chaitanya Mhetre

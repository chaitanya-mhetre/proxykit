from __future__ import annotations

import csv
import json
from pathlib import Path

from proxykit.models import ProxyResult


def export_json(results: list[ProxyResult], path: str | Path) -> None:
    payload = [item.to_dict() for item in results]
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_csv(results: list[ProxyResult], path: str | Path) -> None:
    fieldnames = [
        "host",
        "port",
        "type",
        "alive",
        "latency_ms",
        "anonymity",
        "score",
        "exit_ip",
        "status_code",
        "error",
    ]
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in results:
            writer.writerow(
                {
                    "host": item.proxy.host,
                    "port": item.proxy.port,
                    "type": item.proxy.proxy_type.value,
                    "alive": item.alive,
                    "latency_ms": item.latency_ms,
                    "anonymity": item.anonymity.value,
                    "score": item.score,
                    "exit_ip": item.exit_ip or "",
                    "status_code": item.status_code or "",
                    "error": item.error or "",
                }
            )


def export_alive_list(results: list[ProxyResult], path: str | Path) -> None:
    lines = [item.proxy.url for item in results if item.alive]
    Path(path).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

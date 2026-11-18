from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from urllib.parse import urlparse


class ProxyType(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class AnonymityLevel(str, Enum):
    ELITE = "elite"
    ANONYMOUS = "anonymous"
    TRANSPARENT = "transparent"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class ProxySpec:
    host: str
    port: int
    proxy_type: ProxyType = ProxyType.HTTP
    username: str | None = None
    password: str | None = None

    @classmethod
    def parse(cls, value: str, default_type: ProxyType = ProxyType.HTTP) -> ProxySpec:
        """Parse common proxy formats.

        Supported:
          - host:port
          - user:pass@host:port
          - http://host:port
          - socks5://user:pass@host:port
          - host:port:user:pass
        """
        raw = value.strip()
        if not raw or raw.startswith("#"):
            raise ValueError("empty proxy line")

        proxy_type = default_type
        username: str | None = None
        password: str | None = None

        if "://" in raw:
            parsed = urlparse(raw)
            scheme = (parsed.scheme or "http").lower()
            if scheme not in {t.value for t in ProxyType}:
                raise ValueError(f"unsupported scheme: {scheme}")
            proxy_type = ProxyType(scheme)
            host = parsed.hostname
            port = parsed.port
            username = parsed.username
            password = parsed.password
            if not host or not port:
                raise ValueError(f"invalid proxy url: {raw}")
            return cls(host=host, port=int(port), proxy_type=proxy_type, username=username, password=password)

        # user:pass@host:port
        if "@" in raw:
            creds, endpoint = raw.rsplit("@", 1)
            if ":" not in creds or ":" not in endpoint:
                raise ValueError(f"invalid proxy: {raw}")
            username, password = creds.split(":", 1)
            host, port_s = endpoint.rsplit(":", 1)
            return cls(
                host=host,
                port=int(port_s),
                proxy_type=proxy_type,
                username=username,
                password=password,
            )

        parts = raw.split(":")
        if len(parts) == 2:
            host, port_s = parts
            return cls(host=host, port=int(port_s), proxy_type=proxy_type)
        if len(parts) == 4:
            host, port_s, username, password = parts
            return cls(
                host=host,
                port=int(port_s),
                proxy_type=proxy_type,
                username=username,
                password=password,
            )
        raise ValueError(f"unrecognized proxy format: {raw}")

    @property
    def url(self) -> str:
        auth = ""
        if self.username is not None:
            password = self.password or ""
            auth = f"{self.username}:{password}@"
        return f"{self.proxy_type.value}://{auth}{self.host}:{self.port}"

    def __str__(self) -> str:
        return f"{self.proxy_type.value}://{self.host}:{self.port}"


@dataclass(slots=True)
class ProxyResult:
    proxy: ProxySpec
    alive: bool
    latency_ms: float | None = None
    anonymity: AnonymityLevel = AnonymityLevel.UNKNOWN
    status_code: int | None = None
    exit_ip: str | None = None
    country: str | None = None
    error: str | None = None
    score: float = 0.0
    headers_leaked: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["proxy"] = {
            "host": self.proxy.host,
            "port": self.proxy.port,
            "type": self.proxy.proxy_type.value,
            "url": self.proxy.url,
        }
        data["anonymity"] = self.anonymity.value
        return data

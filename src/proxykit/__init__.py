"""ProxyKit — proxy validation, anonymity scoring, and scraping rotation."""

from proxykit.checker import ProxyChecker
from proxykit.models import AnonymityLevel, ProxyResult, ProxySpec, ProxyType
from proxykit.rotator import ProxyRotator
from proxykit.session import ScrapingSession

__all__ = [
    "AnonymityLevel",
    "ProxyChecker",
    "ProxyResult",
    "ProxyRotator",
    "ProxySpec",
    "ProxyType",
    "ScrapingSession",
]

__version__ = "1.0.0"

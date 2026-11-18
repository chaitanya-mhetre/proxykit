import pytest

from proxykit.models import ProxyResult, ProxySpec, AnonymityLevel
from proxykit.rotator import ProxyRotator


def test_round_robin():
    proxies = [ProxySpec.parse("1.1.1.1:8000"), ProxySpec.parse("2.2.2.2:8000")]
    rotator = ProxyRotator(proxies, strategy="round_robin")
    assert rotator.next().host == "1.1.1.1"
    assert rotator.next().host == "2.2.2.2"
    assert rotator.next().host == "1.1.1.1"


def test_filters_dead_results():
    alive = ProxyResult(proxy=ProxySpec.parse("1.1.1.1:8000"), alive=True, anonymity=AnonymityLevel.ELITE, score=90)
    dead = ProxyResult(proxy=ProxySpec.parse("2.2.2.2:8000"), alive=False, score=0)
    rotator = ProxyRotator([alive, dead], alive_only=True)
    assert len(rotator.proxies) == 1


def test_mark_bad_removes_proxy():
    proxies = [ProxySpec.parse("1.1.1.1:8000"), ProxySpec.parse("2.2.2.2:8000")]
    rotator = ProxyRotator(proxies)
    rotator.mark_bad(proxies[0])
    assert all(p.host != "1.1.1.1" for p in rotator.proxies)


def test_mark_bad_last_proxy_raises():
    proxy = ProxySpec.parse("1.1.1.1:8000")
    rotator = ProxyRotator([proxy])
    with pytest.raises(ValueError):
        rotator.mark_bad(proxy)

import pytest

from proxykit.models import ProxySpec, ProxyType


def test_parse_host_port():
    proxy = ProxySpec.parse("1.2.3.4:8080")
    assert proxy.host == "1.2.3.4"
    assert proxy.port == 8080
    assert proxy.proxy_type == ProxyType.HTTP


def test_parse_user_pass_host_port():
    proxy = ProxySpec.parse("user:secret@9.9.9.9:3128")
    assert proxy.username == "user"
    assert proxy.password == "secret"
    assert proxy.url == "http://user:secret@9.9.9.9:3128"


def test_parse_scheme_url():
    proxy = ProxySpec.parse("socks5://alice:pw@10.0.0.1:1080")
    assert proxy.proxy_type == ProxyType.SOCKS5
    assert proxy.host == "10.0.0.1"
    assert proxy.port == 1080


def test_parse_colon_four():
    proxy = ProxySpec.parse("1.1.1.1:8000:bob:hunter2")
    assert proxy.username == "bob"
    assert proxy.password == "hunter2"


def test_invalid_format():
    with pytest.raises(ValueError):
        ProxySpec.parse("not-a-proxy")

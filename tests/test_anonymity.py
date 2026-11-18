from proxykit.anonymity import compute_score, score_anonymity
from proxykit.models import AnonymityLevel


def test_elite_proxy():
    level, leaked = score_anonymity({"content-type": "application/json"}, "1.1.1.1", "8.8.8.8")
    assert level == AnonymityLevel.ELITE
    assert leaked == []


def test_anonymous_proxy():
    level, leaked = score_anonymity({"via": "1.1 proxy"}, "1.1.1.1", "8.8.8.8")
    assert level == AnonymityLevel.ANONYMOUS
    assert "via" in leaked


def test_transparent_proxy():
    level, leaked = score_anonymity({"x-forwarded-for": "1.1.1.1"}, "1.1.1.1", "8.8.8.8")
    assert level == AnonymityLevel.TRANSPARENT
    assert "x-forwarded-for" in leaked


def test_score_ranking():
    elite = compute_score(True, 200, AnonymityLevel.ELITE)
    slow = compute_score(True, 4000, AnonymityLevel.ELITE)
    dead = compute_score(False, None, AnonymityLevel.UNKNOWN)
    assert elite > slow
    assert dead == 0.0

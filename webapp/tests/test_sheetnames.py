"""`GET /api/names` - name suggestions for the character sheet's NPCs (feature 213).

The picking rules are tested on `l7r.sheetnames` directly with hand-built pools, so every
caste case is explicit; the HTTP contract (auth, parameters, JSON) is tested on the CherryPy
handler, with the refresh and the used-name set patched so nothing reaches the network.
"""

from __future__ import annotations

import http.cookies
import json
import threading
from pathlib import Path

import cherrypy
import pytest

from l7r import app as app_module
from l7r import sheetnames
from l7r.app import Root
from l7r.names import GeneratedName, load_names
from l7r.pool import load_relics


def _entry(name: str, *, peasant: bool = False, samurai: bool = False) -> GeneratedName:
    return GeneratedName(name, 'male', 1, f'{name} - test', peasant, '', samurai)


POOL = {
    'male': (
        _entry('Hiroshi'),
        _entry('Toshiro'),
        _entry('Goro', peasant=True),
        _entry('Kiyomasa'),
        _entry('Sen', peasant=True, samurai=True),
    ),
    'female': (_entry('Akiko'),),
}


# ---------------------------------------------------------------------------
# picking (l7r.sheetnames.suggest_names)
# ---------------------------------------------------------------------------


def test_peasant_batch_draws_only_peasant_names() -> None:
    picks = sheetnames.suggest_names(5, peasant=True, pool=POOL, used=frozenset())
    assert sorted(picks) == ['Goro', 'Sen']  # exhausted after two: fewer, no error


def test_samurai_batch_draws_only_samurai_eligible_names() -> None:
    picks = sheetnames.suggest_names(10, peasant=False, pool=POOL, used=frozenset())
    # Goro (peasant-only) is never reached, even once the eligible names run out:
    # no whole-pool fallback (spec FR-004).
    assert sorted(picks) == ['Hiroshi', 'Kiyomasa', 'Sen', 'Toshiro']


def test_names_are_male_only() -> None:
    picks = sheetnames.suggest_names(30, peasant=False, pool=POOL, used=frozenset())
    assert 'Akiko' not in picks


def test_used_and_too_similar_names_are_excluded() -> None:
    # Hiroshi is used; Toshir is one edit from Toshiro, so Toshiro is too similar.
    picks = sheetnames.suggest_names(
        10, peasant=False, pool=POOL, used=frozenset({'Hiroshi', 'Toshir'})
    )
    assert sorted(picks) == ['Kiyomasa', 'Sen']


def test_batch_is_set_distinct_and_honors_avoid() -> None:
    # Set conflict: same first letter. Avoiding "Hana" rules out Hiroshi; the batch
    # itself never holds two names that conflict.
    picks = sheetnames.suggest_names(10, peasant=False, pool=POOL, used=frozenset(), avoid=['Hana'])
    assert 'Hiroshi' not in picks
    assert len({p[0] for p in picks}) == len(picks)


def test_count_zero_is_empty() -> None:
    assert sheetnames.suggest_names(0, peasant=True, pool=POOL, used=frozenset()) == []


def test_parse_avoid() -> None:
    assert sheetnames.parse_avoid(None) == []
    assert sheetnames.parse_avoid(' Goro , ,Hiroshi,') == ['Goro', 'Hiroshi']
    assert sheetnames.parse_avoid(['A,B', ' C ']) == ['A', 'B', 'C']


def test_parse_count() -> None:
    assert sheetnames.parse_count(None) == 1
    assert sheetnames.parse_count('4') == 4
    assert sheetnames.parse_count('0') == 1
    assert sheetnames.parse_count('-3') == 1
    assert sheetnames.parse_count('500') == 30
    with pytest.raises(ValueError, match='invalid literal'):
        sheetnames.parse_count('four')


def test_parse_peasant() -> None:
    assert sheetnames.parse_peasant(None) is False
    assert sheetnames.parse_peasant('true') is True
    assert sheetnames.parse_peasant('TRUE') is True
    assert sheetnames.parse_peasant('false') is False
    with pytest.raises(ValueError, match='peasant must be'):
        sheetnames.parse_peasant('yes')


def test_token_matches() -> None:
    assert sheetnames.token_matches('Bearer s3cret', 's3cret') is True
    assert sheetnames.token_matches('bearer s3cret', 's3cret') is True
    assert sheetnames.token_matches('Bearer wrong', 's3cret') is False
    assert sheetnames.token_matches('s3cret', 's3cret') is False  # no scheme
    assert sheetnames.token_matches('Basic s3cret', 's3cret') is False
    assert sheetnames.token_matches('', 's3cret') is False
    assert sheetnames.token_matches('Bearer café', 's3cret') is False  # non-ASCII is safe


# ---------------------------------------------------------------------------
# freshness (l7r.sheetnames.refresh_used_names)
# ---------------------------------------------------------------------------


def test_refresh_calls_the_cache_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    from chargen import opcache

    calls: list[float] = []

    def refresh(max_age: float) -> bool:
        calls.append(max_age)
        return True

    monkeypatch.setattr(opcache, 'refresh_if_stale', refresh)
    assert sheetnames.refresh_used_names() is True
    assert calls == [sheetnames.MAX_AGE]


def test_refresh_failure_never_raises(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    from chargen import opcache

    def boom(max_age: float) -> bool:
        raise OSError('Obsidian Portal is down')

    monkeypatch.setattr(opcache, 'refresh_if_stale', boom)
    assert sheetnames.refresh_used_names() is False
    assert 'Obsidian Portal is down' in caplog.text


def test_refresh_is_serialized_by_the_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    from chargen import opcache

    inside = threading.Event()
    release = threading.Event()
    active = 0
    peak = 0
    guard = threading.Lock()

    def slow(max_age: float) -> bool:
        nonlocal active, peak
        with guard:
            active += 1
            peak = max(peak, active)
        inside.set()
        release.wait(5)
        with guard:
            active -= 1
        return False

    monkeypatch.setattr(opcache, 'refresh_if_stale', slow)
    threads = [threading.Thread(target=sheetnames.refresh_used_names) for _ in range(3)]
    for t in threads:
        t.start()
    inside.wait(5)
    release.set()
    for t in threads:
        t.join(5)
    assert peak == 1


# ---------------------------------------------------------------------------
# the HTTP contract (Root.api.names)
# ---------------------------------------------------------------------------


@pytest.fixture
def api_root(sample_pool_dir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Root:
    from chargen import namepool, opcache

    refreshes: list[bool] = []

    def refresh() -> bool:
        refreshes.append(True)
        return True

    monkeypatch.setattr(sheetnames, 'refresh_used_names', refresh)
    monkeypatch.setattr(opcache, 'used_given_names', lambda: frozenset({'Hiroshi'}))
    monkeypatch.setattr(namepool, 'pool_dir', lambda: tmp_path)
    monkeypatch.setattr(namepool, 'load_pool', lambda directory: POOL)
    cherrypy.request.headers = {}
    cherrypy.response.headers = {}
    cherrypy.response.cookie = http.cookies.SimpleCookie()
    cherrypy.response.status = 200
    root = Root(relics=load_relics(sample_pool_dir), names=[], names_token=lambda: 's3cret')
    root.refreshes = refreshes  # type: ignore[attr-defined]
    return root


def _call(root: Root, auth: str | None = 'Bearer s3cret', **params: str) -> tuple[int, dict]:  # type: ignore[type-arg]
    cherrypy.request.headers = {} if auth is None else {'Authorization': auth}
    body = root.api.names(**params)
    status = int(str(cherrypy.response.status).split()[0])
    assert cherrypy.response.headers['Content-Type'] == 'application/json'
    return status, json.loads(body)


def test_api_names_returns_samurai_names_by_default(api_root: Root) -> None:
    status, payload = _call(api_root, count='10')
    assert status == 200
    assert sorted(payload['names']) == ['Kiyomasa', 'Sen', 'Toshiro']  # Hiroshi is used
    assert api_root.refreshes == [True]  # type: ignore[attr-defined]


def test_api_names_peasant_pool(api_root: Root) -> None:
    status, payload = _call(api_root, count='3', peasant='true', avoid='Sato, ,')
    assert status == 200
    assert payload['names'] == ['Goro']  # Sen is avoided (same first letter as Sato)


def test_api_names_default_count_is_one(api_root: Root) -> None:
    status, payload = _call(api_root)
    assert status == 200
    assert len(payload['names']) == 1


def test_api_names_401_without_or_with_wrong_bearer(api_root: Root) -> None:
    for auth in (None, 'Bearer nope', 's3cret', 'Basic s3cret'):
        status, payload = _call(api_root, auth=auth)
        assert status == 401
        assert 'names' not in payload
        assert payload['error']
    assert cherrypy.response.headers['WWW-Authenticate'] == 'Bearer'
    assert api_root.refreshes == []  # type: ignore[attr-defined]


def test_api_names_ignores_a_query_string_token(api_root: Root) -> None:
    status, payload = _call(api_root, auth=None, token='s3cret', names_token='s3cret')
    assert status == 401


def test_api_names_503_when_no_token_is_configured(
    api_root: Root, monkeypatch: pytest.MonkeyPatch
) -> None:
    for configured in ('', '   '):
        monkeypatch.setattr(api_root.api, '_token', lambda configured=configured: configured)
        status, payload = _call(api_root)
        assert status == 503
        assert 'names' not in payload
        assert payload['error']


def test_api_names_400_on_bad_parameters(api_root: Root) -> None:
    for params in ({'count': 'four'}, {'peasant': 'maybe'}):
        status, payload = _call(api_root, **params)
        assert status == 400
        assert 'names' not in payload
        assert payload['error']
    assert api_root.refreshes == []  # type: ignore[attr-defined]


def test_names_token_reads_the_secrets_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(app_module, '_HERE', tmp_path / 'l7r')
    assert app_module._names_token() == ''
    (tmp_path / 'development-secrets.ini').write_text(
        '[character_sheet]\nroll_query_token = outbound\nnames_token =  inbound \n',
        encoding='utf-8',
    )
    assert app_module._names_token() == 'inbound'


def test_default_root_reads_the_token_at_request_time(
    sample_pool_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(app_module, '_names_token', lambda: 'later')
    root = Root(relics=load_relics(sample_pool_dir), names=load_names(sample_pool_dir))
    assert root.api._token() == 'later'

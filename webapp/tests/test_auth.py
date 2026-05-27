"""Tests for l7r.auth — pure logic only (signing, parsing, config loading)."""

from __future__ import annotations

import time
from typing import Any

import pytest

from l7r.auth import (
    DISCORD_AUTHORIZE_URL,
    AuthConfig,
    CurrentUser,
    RealDiscordClient,
    Whitelist,
    WhitelistEntry,
    authenticate_request,
    build_authorize_url,
    default_redirect_uri,
    load_auth_config,
    make_session_cookie,
    new_state,
    parse_session_cookie,
    parse_whitelist_section,
    to_jsonable,
)

# ---------------------------------------------------------------------------
# Whitelist
# ---------------------------------------------------------------------------


def test_whitelist_is_allowed_true_for_known_id() -> None:
    wl = Whitelist(entries=(WhitelistEntry(discord_id='123', name='A'),))
    assert wl.is_allowed('123') is True


def test_whitelist_is_allowed_false_for_unknown_id() -> None:
    wl = Whitelist(entries=(WhitelistEntry(discord_id='123', name='A'),))
    assert wl.is_allowed('999') is False


def test_whitelist_name_for_returns_name() -> None:
    wl = Whitelist(entries=(WhitelistEntry(discord_id='123', name='Alice'),))
    assert wl.name_for('123') == 'Alice'


def test_whitelist_name_for_returns_none_for_unknown() -> None:
    wl = Whitelist(entries=(WhitelistEntry(discord_id='123', name='Alice'),))
    assert wl.name_for('999') is None


def test_whitelist_is_immutable() -> None:
    wl = Whitelist(entries=(WhitelistEntry(discord_id='1', name='A'),))
    with pytest.raises((AttributeError, TypeError)):
        wl.entries = ()  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Whitelist parsing
# ---------------------------------------------------------------------------


def test_parse_whitelist_section_handles_quoted_names() -> None:
    raw = {'282617191147241474': '"Chris R."', '143899133680418818': "'Phil'"}
    wl = parse_whitelist_section(raw)
    assert wl.is_allowed('282617191147241474')
    assert wl.name_for('282617191147241474') == 'Chris R.'
    assert wl.name_for('143899133680418818') == 'Phil'


def test_parse_whitelist_section_skips_non_numeric_keys() -> None:
    raw = {'not_a_id': 'Bob', '123': 'Alice'}
    wl = parse_whitelist_section(raw)
    assert wl.is_allowed('123')
    assert not wl.is_allowed('not_a_id')
    assert len(wl.entries) == 1


def test_parse_whitelist_section_skips_empty_names() -> None:
    raw = {'123': '', '456': '   ', '789': 'Real'}
    wl = parse_whitelist_section(raw)
    assert len(wl.entries) == 1
    assert wl.name_for('789') == 'Real'


# ---------------------------------------------------------------------------
# Session cookies
# ---------------------------------------------------------------------------


def test_make_and_parse_session_cookie_round_trip() -> None:
    cookie = make_session_cookie('123', 'top-secret', ttl_seconds=3600, now=1000)
    parsed = parse_session_cookie(cookie, 'top-secret', now=1500)
    assert parsed == '123'


def test_parse_session_cookie_rejects_wrong_secret() -> None:
    cookie = make_session_cookie('123', 'good-secret', now=1000)
    assert parse_session_cookie(cookie, 'bad-secret', now=1500) is None


def test_parse_session_cookie_rejects_expired() -> None:
    cookie = make_session_cookie('123', 'secret', ttl_seconds=10, now=1000)
    # 100 seconds later: expired (10s TTL).
    assert parse_session_cookie(cookie, 'secret', now=1100) is None


def test_parse_session_cookie_rejects_tampered_payload() -> None:
    cookie = make_session_cookie('123', 'secret', now=1000)
    tampered = '999.' + cookie.split('.', 1)[1]  # change id, keep sig
    assert parse_session_cookie(tampered, 'secret', now=1500) is None


def test_parse_session_cookie_rejects_empty() -> None:
    assert parse_session_cookie('', 'secret') is None


def test_parse_session_cookie_rejects_malformed_missing_sig() -> None:
    assert parse_session_cookie('just-one-part', 'secret') is None


def test_parse_session_cookie_rejects_payload_without_dot() -> None:
    # No inner dot in the payload portion → no expiry → invalid.
    assert parse_session_cookie('payload-with-no-dot.somesig', 'secret') is None


def test_parse_session_cookie_rejects_valid_signature_but_no_inner_dot() -> None:
    # A payload with no dot but signed correctly: len(inner) != 2 branch.
    from l7r.auth import _sign

    payload = 'no-inner-dot'
    sig = _sign(payload, 'secret')
    assert parse_session_cookie(f'{payload}.{sig}', 'secret') is None


def test_parse_session_cookie_rejects_empty_discord_id_in_future() -> None:
    # Empty id but future expiry + valid sig → hits the explicit empty-id check.
    from l7r.auth import _sign

    payload = f'.{int(time.time()) + 3600}'
    sig = _sign(payload, 'secret')
    assert parse_session_cookie(f'{payload}.{sig}', 'secret') is None


def test_parse_session_cookie_rejects_non_integer_expiry() -> None:
    # Hand-construct a payload with a non-integer expiry that still signs cleanly.
    from l7r.auth import _sign

    payload = '123.notanumber'
    sig = _sign(payload, 'secret')
    assert parse_session_cookie(f'{payload}.{sig}', 'secret') is None


def test_parse_session_cookie_rejects_empty_discord_id() -> None:
    from l7r.auth import _sign

    payload = '.1234567890'
    sig = _sign(payload, 'secret')
    assert parse_session_cookie(f'{payload}.{sig}', 'secret') is None


def test_make_session_cookie_uses_current_time_by_default() -> None:
    before = int(time.time())
    cookie = make_session_cookie('123', 'secret', ttl_seconds=60)
    after = int(time.time())
    # The expiry should be in [before+60, after+60].
    payload = cookie.rsplit('.', 1)[0]
    _, expiry_str = payload.split('.', 1)
    expiry = int(expiry_str)
    assert before + 60 <= expiry <= after + 60


def test_parse_session_cookie_uses_current_time_by_default() -> None:
    cookie = make_session_cookie('123', 'secret', ttl_seconds=3600)
    # Without overriding `now`, this should succeed for a fresh cookie.
    assert parse_session_cookie(cookie, 'secret') == '123'


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def test_load_auth_config_full() -> None:
    secrets_data = {
        'discord': {'client_id': '"abc"', 'client_secret': "'shh'"},
        'auth': {'session_secret': 'super-secret'},
        'discord_whitelist': {'123': 'Alice', '456': 'Bob'},
    }
    cfg = load_auth_config(secrets_data)
    assert cfg.discord_client_id == 'abc'
    assert cfg.discord_client_secret == 'shh'
    assert cfg.session_secret == 'super-secret'
    assert cfg.is_configured is True
    assert cfg.whitelist.is_allowed('123')
    assert cfg.whitelist.is_allowed('456')


def test_load_auth_config_is_not_configured_when_empty() -> None:
    cfg = load_auth_config({})
    assert cfg.is_configured is False


def test_load_auth_config_is_not_configured_when_partial() -> None:
    cfg = load_auth_config({'discord': {'client_id': 'abc'}})
    assert cfg.is_configured is False  # missing client_secret + session_secret


def test_load_auth_config_handles_none_section_values() -> None:
    cfg = load_auth_config(
        {
            'discord': None,
            'auth': None,
            'discord_whitelist': None,
        }
    )
    assert cfg.is_configured is False
    assert cfg.whitelist.entries == ()


def test_default_redirect_uri_localhost(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('FLY_APP_NAME', raising=False)
    assert default_redirect_uri() == 'http://127.0.0.1:8080/auth/callback'


def test_default_redirect_uri_fly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('FLY_APP_NAME', 'l7r-gm-assistant')
    assert default_redirect_uri() == 'https://l7r-gm-assistant.fly.dev/auth/callback'


# ---------------------------------------------------------------------------
# URL building
# ---------------------------------------------------------------------------


def test_build_authorize_url_includes_required_params() -> None:
    url = build_authorize_url(
        client_id='1234',
        redirect_uri='http://example.com/cb',
        state='abcd',
    )
    assert url.startswith(DISCORD_AUTHORIZE_URL)
    assert 'client_id=1234' in url
    assert 'scope=identify' in url
    assert 'state=abcd' in url
    assert 'response_type=code' in url
    assert 'redirect_uri=http%3A%2F%2Fexample.com%2Fcb' in url


def test_new_state_is_unique() -> None:
    s1, s2 = new_state(), new_state()
    assert s1 != s2
    assert len(s1) > 20


# ---------------------------------------------------------------------------
# authenticate_request
# ---------------------------------------------------------------------------


def _config_with_whitelist(*entries: tuple[str, str]) -> AuthConfig:
    return AuthConfig(
        discord_client_id='cid',
        discord_client_secret='csec',
        session_secret='secret',
        whitelist=Whitelist(
            entries=tuple(WhitelistEntry(discord_id=i, name=n) for i, n in entries)
        ),
        redirect_uri='http://127.0.0.1:8080/auth/callback',
    )


def test_authenticate_request_happy_path() -> None:
    cfg = _config_with_whitelist(('123', 'Alice'))
    cookie = make_session_cookie('123', 'secret')
    user = authenticate_request(cookie, cfg)
    assert user == CurrentUser(discord_id='123', name='Alice')


def test_authenticate_request_returns_none_when_not_configured() -> None:
    cfg = AuthConfig(
        discord_client_id='',
        discord_client_secret='',
        session_secret='',
        whitelist=Whitelist(entries=()),
        redirect_uri='',
    )
    assert authenticate_request('whatever', cfg) is None


def test_authenticate_request_returns_none_when_cookie_missing() -> None:
    cfg = _config_with_whitelist(('123', 'Alice'))
    assert authenticate_request(None, cfg) is None
    assert authenticate_request('', cfg) is None


def test_authenticate_request_returns_none_when_signature_bad() -> None:
    cfg = _config_with_whitelist(('123', 'Alice'))
    bad_cookie = make_session_cookie('123', 'WRONG-SECRET')
    assert authenticate_request(bad_cookie, cfg) is None


def test_authenticate_request_returns_none_when_user_removed_from_whitelist() -> None:
    cfg = _config_with_whitelist(('123', 'Alice'))
    cookie = make_session_cookie('999', 'secret')  # 999 is not on whitelist
    assert authenticate_request(cookie, cfg) is None


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------


def test_to_jsonable_anonymous() -> None:
    assert to_jsonable(None) == 'anonymous'


def test_to_jsonable_for_user() -> None:
    s = to_jsonable(CurrentUser(discord_id='123', name='Alice'))
    assert '"id": "123"' in s
    assert '"name": "Alice"' in s


def test_real_discord_client_is_constructible() -> None:
    # Smoke: real client constructs without arguments. We don't exercise the
    # HTTP calls here — those are tested via the boundary in auth_routes tests.
    client = RealDiscordClient(timeout=1.0)
    assert client is not None


def test_current_user_is_immutable() -> None:
    user = CurrentUser(discord_id='1', name='A')
    with pytest.raises((AttributeError, TypeError)):
        user.discord_id = '2'  # type: ignore[misc]


def test_authconfig_is_immutable() -> None:
    cfg = _config_with_whitelist(('1', 'A'))
    with pytest.raises((AttributeError, TypeError)):
        cfg.session_secret = 'x'  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RealDiscordClient — uses requests but tested with a session-style fixture
# (verifies the request shape end-to-end via a urllib-level monkeypatch).
# ---------------------------------------------------------------------------


def test_real_discord_client_exchange_code_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    """The real client posts the right form to the right URL."""
    import requests as _requests

    captured: dict[str, Any] = {}

    class FakeResp:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {'access_token': 'tok'}

    def fake_post(url: str, **kwargs: Any) -> FakeResp:
        captured['url'] = url
        captured['data'] = kwargs.get('data')
        return FakeResp()

    monkeypatch.setattr(_requests, 'post', fake_post)
    client = RealDiscordClient(timeout=1.0)
    result = client.exchange_code(
        code='thecode', redirect_uri='http://r/cb', client_id='cid', client_secret='csec'
    )
    assert result == {'access_token': 'tok'}
    assert captured['url'] == 'https://discord.com/api/oauth2/token'
    assert captured['data']['code'] == 'thecode'
    assert captured['data']['redirect_uri'] == 'http://r/cb'
    assert captured['data']['client_id'] == 'cid'
    assert captured['data']['client_secret'] == 'csec'
    assert captured['data']['grant_type'] == 'authorization_code'


def test_real_discord_client_get_user_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    import requests as _requests

    captured: dict[str, Any] = {}

    class FakeResp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {'id': '123', 'global_name': 'Alice'}

    def fake_get(url: str, **kwargs: Any) -> FakeResp:
        captured['url'] = url
        captured['headers'] = kwargs.get('headers')
        return FakeResp()

    monkeypatch.setattr(_requests, 'get', fake_get)
    client = RealDiscordClient(timeout=1.0)
    result = client.get_user('tok-xyz')
    assert result['id'] == '123'
    assert captured['url'] == 'https://discord.com/api/users/@me'
    assert captured['headers']['Authorization'] == 'Bearer tok-xyz'

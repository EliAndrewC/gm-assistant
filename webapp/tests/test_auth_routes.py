"""Tests for l7r.auth_routes — CherryPy auth controller + gating tool."""

from __future__ import annotations

from typing import Any

import cherrypy
import pytest
from requests import HTTPError

from l7r.auth import (
    SESSION_COOKIE_NAME,
    STATE_COOKIE_NAME,
    AuthConfig,
    Whitelist,
    WhitelistEntry,
    make_session_cookie,
)
from l7r.auth_routes import (
    AuthRoot,
    _is_secure_request,
    _read_cookie,
    _set_cookie,
    current_user,
    install_auth_tool,
)
from l7r.jinja_env import build_environment

# ---------------------------------------------------------------------------
# CherryPy request fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cp_request() -> Any:
    """Wire up enough of CherryPy's request/response state for handlers to run."""
    import http.cookies

    cherrypy.request.path_info = '/'
    cherrypy.request.scheme = 'http'
    cherrypy.request.cookie = http.cookies.SimpleCookie()
    cherrypy.request.headers = {}
    cherrypy.response.cookie = http.cookies.SimpleCookie()
    cherrypy.response.status = 200
    if hasattr(cherrypy.request, 'l7r_user'):
        delattr(cherrypy.request, 'l7r_user')
    yield
    if hasattr(cherrypy.request, 'l7r_user'):
        delattr(cherrypy.request, 'l7r_user')


def _make_config(
    configured: bool = True,
    whitelist: tuple[tuple[str, str], ...] = (('123', 'Alice'),),
    gm_whitelist: tuple[tuple[str, str], ...] = (),
) -> AuthConfig:
    return AuthConfig(
        discord_client_id='cid' if configured else '',
        discord_client_secret='csec' if configured else '',
        session_secret='secret' if configured else '',
        player_whitelist=Whitelist(
            entries=tuple(WhitelistEntry(discord_id=i, name=n) for i, n in whitelist)
        ),
        gm_whitelist=Whitelist(
            entries=tuple(WhitelistEntry(discord_id=i, name=n) for i, n in gm_whitelist)
        ),
        redirect_uri='http://127.0.0.1:8080/auth/callback',
    )


# ---------------------------------------------------------------------------
# Fake DiscordClient
# ---------------------------------------------------------------------------


class FakeDiscordClient:
    """Stand-in DiscordClient that returns scripted responses.

    Constitution Principle X.5: external boundaries tested via saved fixtures.
    This fake plays a captured Discord response shape from the real API docs:
    https://discord.com/developers/docs/topics/oauth2 and
    https://discord.com/developers/docs/resources/user
    """

    def __init__(
        self,
        token_response: dict[str, Any] | Exception | None = None,
        user_response: dict[str, Any] | Exception | None = None,
    ) -> None:
        self.token_response = token_response or {
            'access_token': 'fake-token',
            'token_type': 'Bearer',
            'expires_in': 604800,
            'refresh_token': 'fake-refresh',
            'scope': 'identify',
        }
        self.user_response = user_response or {
            'id': '123',
            'username': 'alice',
            'discriminator': '0',
            'global_name': 'Alice',
            'avatar': 'abc',
        }

    def exchange_code(
        self, code: str, redirect_uri: str, client_id: str, client_secret: str
    ) -> dict[str, Any]:
        if isinstance(self.token_response, Exception):
            raise self.token_response
        return self.token_response

    def get_user(self, access_token: str) -> dict[str, Any]:
        if isinstance(self.user_response, Exception):
            raise self.user_response
        return self.user_response


# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------


def test_set_cookie_sets_path_and_max_age(cp_request: Any) -> None:
    _set_cookie('mycookie', 'value123', max_age=100)
    morsel = cherrypy.response.cookie['mycookie']
    assert morsel.value == 'value123'
    assert morsel['path'] == '/'
    assert morsel['max-age'] == 100
    assert morsel['httponly']
    assert morsel['samesite'].lower() == 'lax'


def test_set_cookie_includes_secure_when_forwarded_https(cp_request: Any) -> None:
    cherrypy.request.headers = {'X-Forwarded-Proto': 'https'}
    _set_cookie('mycookie', 'v', max_age=10)
    assert cherrypy.response.cookie['mycookie']['secure']


def test_set_cookie_omits_secure_on_plain_http(cp_request: Any) -> None:
    _set_cookie('mycookie', 'v', max_age=10)
    assert not cherrypy.response.cookie['mycookie']['secure']


def test_read_cookie_missing(cp_request: Any) -> None:
    assert _read_cookie('absent') is None


def test_read_cookie_present(cp_request: Any) -> None:
    cherrypy.request.cookie['present'] = 'hello'
    assert _read_cookie('present') == 'hello'


def test_read_cookie_returns_none_when_empty(cp_request: Any) -> None:
    cherrypy.request.cookie['empty'] = ''
    assert _read_cookie('empty') is None


def test_is_secure_request_detects_https_scheme(cp_request: Any) -> None:
    cherrypy.request.scheme = 'https'
    assert _is_secure_request() is True


def test_is_secure_request_false_for_plain_http(cp_request: Any) -> None:
    cherrypy.request.scheme = 'http'
    assert _is_secure_request() is False


# ---------------------------------------------------------------------------
# install_auth_tool
# ---------------------------------------------------------------------------


def test_install_auth_tool_creates_global_tool() -> None:
    cfg = _make_config()
    install_auth_tool(cfg)
    assert hasattr(cherrypy.tools, 'l7r_auth')


def test_auth_tool_returns_503_when_not_configured(cp_request: Any) -> None:
    cfg = _make_config(configured=False)
    install_auth_tool(cfg)
    cherrypy.request.path_info = '/'
    with pytest.raises(cherrypy.HTTPError) as exc:
        cherrypy.tools.l7r_auth.callable()
    assert exc.value.status == 503


def test_auth_tool_redirects_to_login_when_no_session(cp_request: Any) -> None:
    cfg = _make_config()
    install_auth_tool(cfg)
    cherrypy.request.path_info = '/'
    with pytest.raises(cherrypy.HTTPRedirect) as exc:
        cherrypy.tools.l7r_auth.callable()
    assert '/auth/login' in exc.value.urls[0]


def test_auth_tool_sets_request_user_for_valid_session(cp_request: Any) -> None:
    cfg = _make_config()
    install_auth_tool(cfg)
    cherrypy.request.path_info = '/'
    cherrypy.request.cookie[SESSION_COOKIE_NAME] = make_session_cookie('123', 'secret')
    cherrypy.tools.l7r_auth.callable()
    user = current_user()
    assert user is not None
    assert user.discord_id == '123'
    assert user.name == 'Alice'
    # Default role is 'player' since this user is on player_whitelist only.
    assert user.role == 'player'


# ---------------------------------------------------------------------------
# Role-aware gating (min_role)
# ---------------------------------------------------------------------------


def test_auth_tool_defaults_to_player_min_role(cp_request: Any) -> None:
    # Regression: a mount that forgets to set min_role must fail closed.
    # The tool's default min_role is 'player', so an anonymous request
    # should still be redirected to login.
    cfg = _make_config()
    install_auth_tool(cfg)
    cherrypy.request.path_info = '/'
    with pytest.raises(cherrypy.HTTPRedirect):
        cherrypy.tools.l7r_auth.callable()  # no min_role kwarg


def test_auth_tool_anonymous_min_role_allows_logged_out(cp_request: Any) -> None:
    cfg = _make_config()
    install_auth_tool(cfg)
    cherrypy.request.path_info = '/'
    # No session cookie. Must not raise.
    cherrypy.tools.l7r_auth.callable(min_role='anonymous')
    assert current_user() is None


def test_auth_tool_anonymous_min_role_attaches_user_when_logged_in(cp_request: Any) -> None:
    # Anonymous-allowed routes still attach current_user when a valid
    # session cookie is present — the nav needs this to render the user pill.
    cfg = _make_config()
    install_auth_tool(cfg)
    cherrypy.request.path_info = '/'
    cherrypy.request.cookie[SESSION_COOKIE_NAME] = make_session_cookie('123', 'secret')
    cherrypy.tools.l7r_auth.callable(min_role='anonymous')
    user = current_user()
    assert user is not None
    assert user.role == 'player'


def test_auth_tool_anonymous_min_role_503_skipped_when_not_configured(
    cp_request: Any,
) -> None:
    # A public catalog shouldn't 503 just because Discord OAuth isn't
    # configured for this deployment.
    cfg = _make_config(configured=False)
    install_auth_tool(cfg)
    cherrypy.request.path_info = '/'
    cherrypy.tools.l7r_auth.callable(min_role='anonymous')  # must not raise


def test_auth_tool_gm_min_role_blocks_player(cp_request: Any) -> None:
    cfg = _make_config()
    install_auth_tool(cfg)
    cherrypy.request.path_info = '/archive/save'
    cherrypy.request.cookie[SESSION_COOKIE_NAME] = make_session_cookie('123', 'secret')
    with pytest.raises(cherrypy.HTTPError) as exc:
        cherrypy.tools.l7r_auth.callable(min_role='gm')
    assert exc.value.status == 403


def test_auth_tool_gm_min_role_allows_gm(cp_request: Any) -> None:
    cfg = _make_config(gm_whitelist=(('123', 'Alice'),))
    install_auth_tool(cfg)
    cherrypy.request.path_info = '/archive/save'
    cherrypy.request.cookie[SESSION_COOKIE_NAME] = make_session_cookie('123', 'secret')
    cherrypy.tools.l7r_auth.callable(min_role='gm')  # must not raise
    user = current_user()
    assert user is not None
    assert user.role == 'gm'


def test_auth_tool_gm_min_role_redirects_anonymous_to_login(cp_request: Any) -> None:
    # A logged-out user hitting a GM route gets sent to login (where they
    # might still be denied, but the redirect is the right first step).
    cfg = _make_config()
    install_auth_tool(cfg)
    cherrypy.request.path_info = '/archive/save'
    with pytest.raises(cherrypy.HTTPRedirect):
        cherrypy.tools.l7r_auth.callable(min_role='gm')


# ---------------------------------------------------------------------------
# AuthRoot — full flow
# ---------------------------------------------------------------------------


@pytest.fixture
def env() -> Any:
    return build_environment()


def test_login_redirects_when_already_authenticated(cp_request: Any, env: Any) -> None:
    cfg = _make_config()
    root = AuthRoot(config=cfg, env=env, discord_client=FakeDiscordClient())
    cherrypy.request.cookie[SESSION_COOKIE_NAME] = make_session_cookie('123', 'secret')
    with pytest.raises(cherrypy.HTTPRedirect) as exc:
        root.login()
    assert exc.value.urls[0].endswith('/')


def test_login_renders_page_when_unauthenticated(cp_request: Any, env: Any) -> None:
    cfg = _make_config()
    root = AuthRoot(config=cfg, env=env, discord_client=FakeDiscordClient())
    html = root.login().decode('utf-8')
    assert 'Continue with Discord' in html


def test_login_renders_misconfigured_page_when_no_config(cp_request: Any, env: Any) -> None:
    cfg = _make_config(configured=False)
    root = AuthRoot(config=cfg, env=env, discord_client=FakeDiscordClient())
    html = root.login().decode('utf-8')
    assert cherrypy.response.status == 503
    assert "isn't set up" in html or 'configured' in html.lower()


def test_start_redirects_to_discord_and_sets_state(cp_request: Any, env: Any) -> None:
    cfg = _make_config()
    root = AuthRoot(config=cfg, env=env, discord_client=FakeDiscordClient())
    with pytest.raises(cherrypy.HTTPRedirect) as exc:
        root.start()
    url = exc.value.urls[0]
    assert url.startswith('https://discord.com/api/oauth2/authorize')
    assert 'scope=identify' in url
    # State cookie was set on the response.
    assert STATE_COOKIE_NAME in cherrypy.response.cookie


def test_start_503_when_not_configured(cp_request: Any, env: Any) -> None:
    cfg = _make_config(configured=False)
    root = AuthRoot(config=cfg, env=env, discord_client=FakeDiscordClient())
    with pytest.raises(cherrypy.HTTPError) as exc:
        root.start()
    assert exc.value.status == 503


def test_callback_503_when_not_configured(cp_request: Any, env: Any) -> None:
    cfg = _make_config(configured=False)
    root = AuthRoot(config=cfg, env=env, discord_client=FakeDiscordClient())
    with pytest.raises(cherrypy.HTTPError) as exc:
        root.callback(code='c', state='s')
    assert exc.value.status == 503


def test_callback_succeeds_and_sets_session(cp_request: Any, env: Any) -> None:
    cfg = _make_config()
    root = AuthRoot(config=cfg, env=env, discord_client=FakeDiscordClient())
    cherrypy.request.cookie[STATE_COOKIE_NAME] = 'xyz-state'
    with pytest.raises(cherrypy.HTTPRedirect) as exc:
        root.callback(code='goodcode', state='xyz-state')
    assert exc.value.urls[0].endswith('/')
    assert SESSION_COOKIE_NAME in cherrypy.response.cookie
    cookie_val = cherrypy.response.cookie[SESSION_COOKIE_NAME].value
    assert cookie_val.startswith('123.')  # discord_id from FakeDiscordClient


def test_callback_renders_access_denied_for_non_whitelisted(cp_request: Any, env: Any) -> None:
    cfg = _make_config(whitelist=(('555', 'Other'),))  # 123 not on whitelist
    root = AuthRoot(config=cfg, env=env, discord_client=FakeDiscordClient())
    cherrypy.request.cookie[STATE_COOKIE_NAME] = 'xyz'
    html = root.callback(code='c', state='xyz').decode('utf-8')
    assert cherrypy.response.status == 403
    assert 'Not on the guest list' in html
    assert 'Alice' in html  # display_name from fake user
    assert SESSION_COOKIE_NAME not in cherrypy.response.cookie


def test_callback_400_when_state_mismatched(cp_request: Any, env: Any) -> None:
    cfg = _make_config()
    root = AuthRoot(config=cfg, env=env, discord_client=FakeDiscordClient())
    cherrypy.request.cookie[STATE_COOKIE_NAME] = 'a'
    html = root.callback(code='c', state='b').decode('utf-8')
    assert cherrypy.response.status == 400
    assert 'tampered' in html or 'expired' in html


def test_callback_400_when_no_state_cookie(cp_request: Any, env: Any) -> None:
    cfg = _make_config()
    root = AuthRoot(config=cfg, env=env, discord_client=FakeDiscordClient())
    html = root.callback(code='c', state='b').decode('utf-8')
    assert cherrypy.response.status == 400
    assert 'tampered' in html or 'expired' in html


def test_callback_400_when_no_code(cp_request: Any, env: Any) -> None:
    cfg = _make_config()
    root = AuthRoot(config=cfg, env=env, discord_client=FakeDiscordClient())
    cherrypy.request.cookie[STATE_COOKIE_NAME] = 'x'
    root.callback(code=None, state='x')
    assert cherrypy.response.status == 400


def test_callback_502_when_token_exchange_fails(cp_request: Any, env: Any) -> None:
    cfg = _make_config()
    client = FakeDiscordClient(token_response=HTTPError('500 server error'))
    root = AuthRoot(config=cfg, env=env, discord_client=client)
    cherrypy.request.cookie[STATE_COOKIE_NAME] = 'x'
    html = root.callback(code='c', state='x').decode('utf-8')
    assert cherrypy.response.status == 502
    assert 'Could not reach Discord' in html


def test_callback_502_when_token_response_missing_access_token(cp_request: Any, env: Any) -> None:
    cfg = _make_config()
    client = FakeDiscordClient(token_response={'error': 'invalid_grant'})
    root = AuthRoot(config=cfg, env=env, discord_client=client)
    cherrypy.request.cookie[STATE_COOKIE_NAME] = 'x'
    html = root.callback(code='c', state='x').decode('utf-8')
    assert cherrypy.response.status == 502
    assert 'unexpected response' in html.lower()


def test_callback_502_when_get_user_fails(cp_request: Any, env: Any) -> None:
    cfg = _make_config()
    client = FakeDiscordClient(user_response=HTTPError('boom'))
    root = AuthRoot(config=cfg, env=env, discord_client=client)
    cherrypy.request.cookie[STATE_COOKIE_NAME] = 'x'
    html = root.callback(code='c', state='x').decode('utf-8')
    assert cherrypy.response.status == 502
    assert 'Discord identity' in html


def test_callback_502_when_user_has_no_id(cp_request: Any, env: Any) -> None:
    cfg = _make_config()
    client = FakeDiscordClient(user_response={'username': 'noid'})
    root = AuthRoot(config=cfg, env=env, discord_client=client)
    cherrypy.request.cookie[STATE_COOKIE_NAME] = 'x'
    html = root.callback(code='c', state='x').decode('utf-8')
    assert cherrypy.response.status == 502
    assert 'account id' in html


def test_callback_falls_back_to_username_when_global_name_missing(
    cp_request: Any, env: Any
) -> None:
    cfg = _make_config(whitelist=(('999', 'Other'),))  # 123 not on whitelist
    client = FakeDiscordClient(user_response={'id': '123', 'username': 'thenamewithout'})
    root = AuthRoot(config=cfg, env=env, discord_client=client)
    cherrypy.request.cookie[STATE_COOKIE_NAME] = 'x'
    html = root.callback(code='c', state='x').decode('utf-8')
    assert 'thenamewithout' in html


def test_callback_falls_back_to_unknown_when_no_name_at_all(cp_request: Any, env: Any) -> None:
    cfg = _make_config(whitelist=(('999', 'Other'),))
    client = FakeDiscordClient(user_response={'id': '123'})
    root = AuthRoot(config=cfg, env=env, discord_client=client)
    cherrypy.request.cookie[STATE_COOKIE_NAME] = 'x'
    html = root.callback(code='c', state='x').decode('utf-8')
    assert '(unknown)' in html


def test_logout_clears_session_and_redirects(cp_request: Any, env: Any) -> None:
    cfg = _make_config()
    root = AuthRoot(config=cfg, env=env, discord_client=FakeDiscordClient())
    cherrypy.request.cookie[SESSION_COOKIE_NAME] = make_session_cookie('123', 'secret')
    with pytest.raises(cherrypy.HTTPRedirect) as exc:
        root.logout()
    assert '/auth/login' in exc.value.urls[0]
    # The response cookie has the session cookie reset to empty/expired.
    assert cherrypy.response.cookie[SESSION_COOKIE_NAME].value == ''


def test_auth_root_default_discord_client_is_real(env: Any) -> None:
    cfg = _make_config()
    root = AuthRoot(config=cfg, env=env)
    # Internal: just check the type isn't None.
    assert root._discord is not None


def test_current_user_returns_none_without_request_attr(cp_request: Any) -> None:
    assert current_user() is None

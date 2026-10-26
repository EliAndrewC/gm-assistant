"""CherryPy routes for the auth flow and the gating tool.

Kept separate from `l7r.auth` so that auth core logic (signing, parsing,
config loading) is testable without importing cherrypy.
"""

from __future__ import annotations

import base64
import logging
from typing import Any
from urllib.parse import quote

import cherrypy
from jinja2 import Environment
from requests import HTTPError, RequestException

from l7r.auth import (
    DEFAULT_SESSION_TTL_SECONDS,
    SESSION_COOKIE_NAME,
    STATE_COOKIE_NAME,
    STATE_TTL_SECONDS,
    AuthConfig,
    CurrentUser,
    DiscordClient,
    RealDiscordClient,
    Role,
    authenticate_request,
    build_authorize_url,
    make_session_cookie,
    new_state,
    role_for,
    role_meets,
)
from l7r.sections import SECTIONS

logger = logging.getLogger(__name__)


def _is_secure_request() -> bool:
    """True if the original client request was HTTPS.

    On Fly, the proxy terminates TLS and forwards as HTTP. The original scheme
    is in X-Forwarded-Proto.
    """
    forwarded = cherrypy.request.headers.get('X-Forwarded-Proto')
    if forwarded:
        return bool(forwarded.lower() == 'https')
    return bool(cherrypy.request.scheme == 'https')


def _set_cookie(name: str, value: str, max_age: int, http_only: bool = True) -> None:
    """Set a cookie on the current response with sensible security defaults."""
    cookie = cherrypy.response.cookie
    cookie[name] = value
    cookie[name]['path'] = '/'
    cookie[name]['max-age'] = max_age
    if http_only:
        cookie[name]['httponly'] = True
    if _is_secure_request():
        cookie[name]['secure'] = True
    # SameSite=Lax - required for the OAuth redirect back to us with the session
    # cookie present. Strict would drop the cookie on the redirect from Discord.
    cookie[name]['SameSite'] = 'Lax'


def _clear_cookie(name: str) -> None:
    cookie = cherrypy.response.cookie
    cookie[name] = ''
    cookie[name]['path'] = '/'
    cookie[name]['max-age'] = 0


def _read_cookie(name: str) -> str | None:
    morsel = cherrypy.request.cookie.get(name)
    if morsel is None:
        return None
    value = morsel.value
    return value if value else None


# Where to send someone after they sign in (GM 2026-10-26: signing in from the shrine builder
# should come back to the shrine builder). It rides from /auth/login?next=... through /auth/start
# in a short-lived cookie, because Discord's redirect back to /auth/callback carries only our own
# state. Only a local path is accepted, so the link cannot send anyone to another site.
NEXT_COOKIE_NAME = 'l7r_next'
# Browsers drop a cookie over 4 KB; base64 grows the path by a third, so 2,900 characters fit.
NEXT_CAP = 2900


def safe_next(value: object) -> str:
    """`value` if it is a local path on this site, else '/'. Not `//host` (protocol-relative),
    not a backslash (browsers read `/\\host` as `//host`), not a scheme, not the sign-in pages.
    A path too long to carry keeps its page and drops its query."""
    if not isinstance(value, str) or not value.startswith('/'):
        return '/'
    if value.startswith('//') or '\\' in value or any(ord(c) < 32 for c in value):
        return '/'
    if value == '/auth' or value.startswith(('/auth/', '/auth?')):
        return '/'
    if len(value) > NEXT_CAP:
        return value.split('?', 1)[0].split('#', 1)[0][:NEXT_CAP]
    return value


def _pack(path: str) -> str:
    return base64.urlsafe_b64encode(path.encode()).decode('ascii')


def _unpack(packed: str | None) -> str:
    try:
        return base64.urlsafe_b64decode((packed or '').encode('ascii')).decode()
    except ValueError, UnicodeError:
        return '/'


def here() -> str:
    """The current request's path and query string."""
    request = cherrypy.request
    query = str(request.query_string or '')
    return str(request.path_info) + (f'?{query}' if query else '')


def login_url(next_path: str | None = None) -> str:
    """The sign-in link that comes back to `next_path` (default: the current page)."""
    return '/auth/login?next=' + quote(safe_next(next_path or here()), safe='')


def install_auth_tool(config: AuthConfig) -> None:
    """Register the global `tools.l7r_auth` CherryPy tool.

    Apps that want auth gating set `'tools.l7r_auth.on': True` in their
    config. The default `min_role` is `'player'` - a route that opts into
    the tool without specifying min_role still requires a logged-in
    whitelisted user, so a forgotten mount config fails closed, not open.

    Per-mount min_role examples:
        '/':         'anonymous'  → never blocks; attaches user if present
        '/chargen':  'player'     → must be a logged-in whitelisted player
        '/archive':  'gm'         → must be in [gm_whitelist]
    """

    def check(min_role: Role = 'player') -> None:
        if not config.is_configured:
            # Anonymous-only routes shouldn't 503 the catalog just because
            # Discord OAuth isn't configured for this deployment.
            if min_role == 'anonymous':
                return
            raise cherrypy.HTTPError(503, 'authentication not configured')
        user = authenticate_request(_read_cookie(SESSION_COOKIE_NAME), config)
        # Attach the user (or absence thereof) so handlers and templates
        # can render auth-aware UI on anonymous routes too.
        if user is not None:
            cherrypy.request.l7r_user = user
        if min_role == 'anonymous':
            return
        if user is None:
            raise cherrypy.HTTPRedirect(login_url())
        if not role_meets(user.role, min_role):
            # Logged in, but not at the required level. Login won't help -
            # 403, rendered through the app's error_page.403 handler.
            raise cherrypy.HTTPError(403, 'forbidden')

    cherrypy.tools.l7r_auth = cherrypy.Tool('before_handler', check, priority=70)


def current_user() -> CurrentUser | None:
    """Return the authenticated user on this request, if any."""
    return getattr(cherrypy.request, 'l7r_user', None)


class AuthRoot:
    """CherryPy controller mounted at /auth."""

    def __init__(
        self,
        config: AuthConfig,
        env: Environment,
        discord_client: DiscordClient | None = None,
    ) -> None:
        self._config = config
        self._env = env
        self._discord = discord_client if discord_client is not None else RealDiscordClient()

    # GET /auth/login
    @cherrypy.expose
    def login(self, next: str | None = None, **_kwargs: Any) -> bytes:  # noqa: A002 - the query key
        if not self._config.is_configured:
            cherrypy.response.status = 503
            return self._render(
                'auth_misconfigured.html',
                detail='Discord auth is not configured. See development-secrets.ini.',
            )
        # If already signed in, send them where they were going.
        user = authenticate_request(_read_cookie(SESSION_COOKIE_NAME), self._config)
        if user is not None:
            raise cherrypy.HTTPRedirect(safe_next(next))
        return self._render('login.html', next_path=quote(safe_next(next), safe=''))

    # GET /auth/start - generates state, redirects to Discord
    @cherrypy.expose
    def start(self, next: str | None = None, **_kwargs: Any) -> None:  # noqa: A002 - the query key
        if not self._config.is_configured:
            raise cherrypy.HTTPError(503, 'authentication not configured')
        state = new_state()
        _set_cookie(STATE_COOKIE_NAME, state, max_age=STATE_TTL_SECONDS)
        _set_cookie(NEXT_COOKIE_NAME, _pack(safe_next(next)), max_age=STATE_TTL_SECONDS)
        url = build_authorize_url(
            client_id=self._config.discord_client_id,
            redirect_uri=self._config.redirect_uri,
            state=state,
        )
        raise cherrypy.HTTPRedirect(url)

    # GET /auth/callback?code=...&state=...
    @cherrypy.expose
    def callback(self, code: str | None = None, state: str | None = None, **_kwargs: Any) -> bytes:
        if not self._config.is_configured:
            raise cherrypy.HTTPError(503, 'authentication not configured')
        expected_state = _read_cookie(STATE_COOKIE_NAME)
        _clear_cookie(STATE_COOKIE_NAME)
        if not code or not state or not expected_state or state != expected_state:
            cherrypy.response.status = 400
            return self._render(
                'auth_error.html',
                detail='Login flow expired or was tampered with. Please try again.',
            )
        try:
            token_response = self._discord.exchange_code(
                code=code,
                redirect_uri=self._config.redirect_uri,
                client_id=self._config.discord_client_id,
                client_secret=self._config.discord_client_secret,
            )
        except (HTTPError, RequestException) as exc:
            logger.warning('discord token exchange failed: %s', exc)
            cherrypy.response.status = 502
            return self._render(
                'auth_error.html',
                detail='Could not reach Discord to verify the login. Please try again.',
            )
        access_token = token_response.get('access_token')
        if not isinstance(access_token, str) or not access_token:
            cherrypy.response.status = 502
            return self._render(
                'auth_error.html',
                detail='Discord returned an unexpected response. Please try again.',
            )
        try:
            user_data = self._discord.get_user(access_token)
        except (HTTPError, RequestException) as exc:
            logger.warning('discord get_user failed: %s', exc)
            cherrypy.response.status = 502
            return self._render(
                'auth_error.html',
                detail='Could not load your Discord identity. Please try again.',
            )
        discord_id = str(user_data.get('id', '') or '')
        if not discord_id:
            cherrypy.response.status = 502
            return self._render('auth_error.html', detail='Discord did not return an account id.')
        if role_for(discord_id, self._config) is None:
            display = user_data.get('global_name') or user_data.get('username') or '(unknown)'
            logger.info('access denied for discord id %s (%s)', discord_id, display)
            cherrypy.response.status = 403
            return self._render('access_denied.html', display_name=display)
        # Success - issue session.
        session_cookie = make_session_cookie(discord_id, self._config.session_secret)
        _set_cookie(SESSION_COOKIE_NAME, session_cookie, max_age=DEFAULT_SESSION_TTL_SECONDS)
        logger.info('login success: %s', discord_id)
        target = safe_next(_unpack(_read_cookie(NEXT_COOKIE_NAME)))
        _clear_cookie(NEXT_COOKIE_NAME)
        raise cherrypy.HTTPRedirect(target)

    # GET /auth/logout
    @cherrypy.expose
    def logout(self) -> None:
        _clear_cookie(SESSION_COOKIE_NAME)
        raise cherrypy.HTTPRedirect('/auth/login')

    # ---- internals ----

    def _render(self, template_name: str, **context: Any) -> bytes:
        template = self._env.get_template(template_name)
        rendered = template.render(
            SECTIONS=SECTIONS,
            current_user=current_user(),
            **context,
        )
        return rendered.encode('utf-8')

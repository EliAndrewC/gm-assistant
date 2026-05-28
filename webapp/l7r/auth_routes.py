"""CherryPy routes for the auth flow and the gating tool.

Kept separate from `l7r.auth` so that auth core logic (signing, parsing,
config loading) is testable without importing cherrypy.
"""

from __future__ import annotations

import logging
from typing import Any

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


# Routes that bypass auth. Order matters: anything under these prefixes is public.
PUBLIC_PREFIXES: tuple[str, ...] = (
    '/auth/',
    '/static/',
    '/favicon.ico',
    '/terms',
    '/privacy',
)


def _is_public_path(path: str) -> bool:
    return any(path == p.rstrip('/') or path.startswith(p) for p in PUBLIC_PREFIXES)


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
    # SameSite=Lax — required for the OAuth redirect back to us with the session
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


def install_auth_tool(config: AuthConfig) -> None:
    """Register the global `tools.l7r_auth` CherryPy tool.

    Apps that want auth gating set `'tools.l7r_auth.on': True` in their
    config. The default `min_role` is `'player'` — a route that opts into
    the tool without specifying min_role still requires a logged-in
    whitelisted user, so a forgotten mount config fails closed, not open.

    Per-mount min_role examples:
        '/':         'anonymous'  → never blocks; attaches user if present
        '/chargen':  'player'     → must be a logged-in whitelisted player
        '/archive':  'gm'         → must be in [gm_whitelist]
    """

    def check(min_role: Role = 'player') -> None:
        path = cherrypy.request.path_info
        if _is_public_path(path):
            return
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
            raise cherrypy.HTTPRedirect('/auth/login')
        if not role_meets(user.role, min_role):
            # Logged in, but not at the required level. Login won't help —
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
    def login(self) -> bytes:
        if not self._config.is_configured:
            cherrypy.response.status = 503
            return self._render(
                'auth_misconfigured.html',
                detail='Discord auth is not configured. See development-secrets.ini.',
            )
        # If already signed in, send them home.
        user = authenticate_request(_read_cookie(SESSION_COOKIE_NAME), self._config)
        if user is not None:
            raise cherrypy.HTTPRedirect('/')
        return self._render('login.html')

    # GET /auth/start — generates state, redirects to Discord
    @cherrypy.expose
    def start(self) -> None:
        if not self._config.is_configured:
            raise cherrypy.HTTPError(503, 'authentication not configured')
        state = new_state()
        _set_cookie(STATE_COOKIE_NAME, state, max_age=STATE_TTL_SECONDS)
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
        # Success — issue session.
        session_cookie = make_session_cookie(discord_id, self._config.session_secret)
        _set_cookie(SESSION_COOKIE_NAME, session_cookie, max_age=DEFAULT_SESSION_TTL_SECONDS)
        logger.info('login success: %s', discord_id)
        raise cherrypy.HTTPRedirect('/')

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

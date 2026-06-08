"""Discord OAuth authentication + whitelist gating.

The flow:
    1. Unauthenticated request → 302 to /auth/login
    2. /auth/login renders a "Login with Discord" page
    3. /auth/start generates a CSRF state, sets it as a short-lived cookie, and
       redirects the user to Discord's authorize endpoint with scope=identify.
    4. Discord redirects back to /auth/callback?code=...&state=...
    5. We verify state, exchange the code for an access token, fetch the user's
       Discord ID, check it against the configured whitelist, and either:
         - issue a signed session cookie + redirect to /, or
         - render an access-denied page.

Sessions are stateless HMAC-SHA256-signed cookies of the form
`discord_id.expiry_unix.signature`. They survive Fly machine auto-stop because
they hold no server-side state.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import time
from dataclasses import dataclass
from typing import Any, Literal, Protocol
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

DISCORD_AUTHORIZE_URL = 'https://discord.com/api/oauth2/authorize'
DISCORD_TOKEN_URL = 'https://discord.com/api/oauth2/token'
DISCORD_ME_URL = 'https://discord.com/api/users/@me'
DISCORD_SCOPE = 'identify'

SESSION_COOKIE_NAME = 'l7r_session'
STATE_COOKIE_NAME = 'l7r_oauth_state'
DEFAULT_SESSION_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days
STATE_TTL_SECONDS = 10 * 60  # 10 minutes - for completing the OAuth round trip


# Role hierarchy used both as a gate config (`min_role` on the auth tool)
# and as the role stamped on an authenticated CurrentUser. 'anonymous' is
# only ever a min_role value - by convention, CurrentUser.role is always
# 'player' or 'gm' since the absence of a CurrentUser already conveys
# "anonymous". role_meets() encodes the ordering: gm ≥ player ≥ anonymous.
Role = Literal['anonymous', 'player', 'gm']

_ROLE_RANK: dict[Role, int] = {
    'anonymous': 0,
    'player': 1,
    'gm': 2,
}


def role_meets(actual: Role, required: Role) -> bool:
    """True if `actual` satisfies `required` under the role hierarchy."""
    return _ROLE_RANK[actual] >= _ROLE_RANK[required]


@dataclass(frozen=True, slots=True)
class WhitelistEntry:
    """One person allowed to log in: their Discord ID and display name."""

    discord_id: str
    name: str


@dataclass(frozen=True, slots=True)
class Whitelist:
    """The set of Discord IDs allowed to log in."""

    entries: tuple[WhitelistEntry, ...]

    def is_allowed(self, discord_id: str) -> bool:
        return any(e.discord_id == discord_id for e in self.entries)

    def name_for(self, discord_id: str) -> str | None:
        for e in self.entries:
            if e.discord_id == discord_id:
                return e.name
        return None


@dataclass(frozen=True, slots=True)
class CurrentUser:
    """The authenticated user, available to handlers and templates."""

    discord_id: str
    name: str
    role: Role


@dataclass(frozen=True, slots=True)
class AuthConfig:
    """Resolved auth configuration."""

    discord_client_id: str
    discord_client_secret: str
    session_secret: str
    # Discord IDs allowed to log in. Membership here grants the 'player'
    # role. The OAuth callback denies session issuance to anyone not on
    # this list, so a logged-in user is always at least a player.
    player_whitelist: Whitelist
    # Subset of player_whitelist (by convention) that gets the 'gm' role.
    # Membership in gm_whitelist alone - without also being on
    # player_whitelist - still resolves to 'gm', since gm ≥ player.
    gm_whitelist: Whitelist
    redirect_uri: str

    @property
    def is_configured(self) -> bool:
        return bool(self.discord_client_id and self.discord_client_secret and self.session_secret)


# ---------------------------------------------------------------------------
# Session signing
# ---------------------------------------------------------------------------


def make_session_cookie(
    discord_id: str,
    secret: str,
    ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
    now: int | None = None,
) -> str:
    """Return a signed session cookie for the given Discord ID.

    Format: `<discord_id>.<expiry_unix>.<hex_signature>`
    """
    issued_at = now if now is not None else int(time.time())
    expiry = issued_at + ttl_seconds
    payload = f'{discord_id}.{expiry}'
    sig = _sign(payload, secret)
    return f'{payload}.{sig}'


def parse_session_cookie(
    cookie: str,
    secret: str,
    now: int | None = None,
) -> str | None:
    """Verify a session cookie. Returns the Discord ID, or None if invalid/expired."""
    if not cookie:
        return None
    parts = cookie.rsplit('.', 1)
    if len(parts) != 2:
        return None
    payload, sig = parts
    expected_sig = _sign(payload, secret)
    if not hmac.compare_digest(sig, expected_sig):
        return None
    inner = payload.split('.')
    if len(inner) != 2:
        return None
    discord_id, expiry_str = inner
    try:
        expiry = int(expiry_str)
    except ValueError:
        return None
    current = now if now is not None else int(time.time())
    if expiry < current:
        return None
    if not discord_id:
        return None
    return discord_id


def _sign(payload: str, secret: str) -> str:
    return hmac.new(secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# Discord client (boundary - injectable for tests)
# ---------------------------------------------------------------------------


class DiscordClient(Protocol):
    """The narrow interface to Discord's OAuth and user endpoints."""

    def exchange_code(
        self, code: str, redirect_uri: str, client_id: str, client_secret: str
    ) -> dict[str, Any]: ...

    def get_user(self, access_token: str) -> dict[str, Any]: ...


class RealDiscordClient:
    """Default DiscordClient: real HTTP calls to discord.com."""

    def __init__(self, timeout: float = 10.0) -> None:
        self._timeout = timeout

    def exchange_code(
        self, code: str, redirect_uri: str, client_id: str, client_secret: str
    ) -> dict[str, Any]:
        resp = requests.post(
            DISCORD_TOKEN_URL,
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result

    def get_user(self, access_token: str) -> dict[str, Any]:
        resp = requests.get(
            DISCORD_ME_URL,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def parse_whitelist_section(raw: dict[str, str]) -> Whitelist:
    """Parse an INI section mapping `discord_id = name` into a Whitelist.

    Lines whose key is non-numeric or whose value is empty are skipped.
    """
    entries: list[WhitelistEntry] = []
    for key, value in raw.items():
        discord_id = key.strip()
        name = value.strip().strip('"').strip("'")
        if not discord_id or not name:
            continue
        if not discord_id.isdigit():
            continue
        entries.append(WhitelistEntry(discord_id=discord_id, name=name))
    return Whitelist(entries=tuple(entries))


def default_redirect_uri() -> str:
    """Compute the OAuth redirect URI from FLY_APP_NAME or localhost."""
    import os

    fly_name = os.environ.get('FLY_APP_NAME')
    if fly_name:
        return f'https://{fly_name}.fly.dev/auth/callback'
    return 'http://127.0.0.1:8080/auth/callback'


def load_auth_config(secrets_dict: dict[str, Any]) -> AuthConfig:
    """Build an AuthConfig from a parsed development-secrets.ini dict.

    Expected sections:
      [discord]            client_id, client_secret
      [auth]               session_secret
      [discord_whitelist]  <discord_id> = <display name>  (players)
      [gm_whitelist]       <discord_id> = <display name>  (GMs; optional)
    """
    discord = secrets_dict.get('discord', {}) or {}
    auth = secrets_dict.get('auth', {}) or {}
    player_whitelist_raw = secrets_dict.get('discord_whitelist', {}) or {}
    gm_whitelist_raw = secrets_dict.get('gm_whitelist', {}) or {}
    return AuthConfig(
        discord_client_id=str(discord.get('client_id', '') or '').strip().strip('"').strip("'"),
        discord_client_secret=str(discord.get('client_secret', '') or '')
        .strip()
        .strip('"')
        .strip("'"),
        session_secret=str(auth.get('session_secret', '') or '').strip().strip('"').strip("'"),
        player_whitelist=parse_whitelist_section(player_whitelist_raw),
        gm_whitelist=parse_whitelist_section(gm_whitelist_raw),
        redirect_uri=default_redirect_uri(),
    )


# ---------------------------------------------------------------------------
# OAuth URL building
# ---------------------------------------------------------------------------


def build_authorize_url(
    client_id: str,
    redirect_uri: str,
    state: str,
    scope: str = DISCORD_SCOPE,
) -> str:
    """Build the Discord OAuth authorize URL the user is redirected to."""
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': scope,
        'state': state,
        'prompt': 'none',  # don't re-prompt if the user already authorized
    }
    return f'{DISCORD_AUTHORIZE_URL}?{urlencode(params)}'


def new_state() -> str:
    """Generate a fresh OAuth CSRF state token."""
    return secrets.token_urlsafe(24)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def role_for(discord_id: str, config: AuthConfig) -> Role | None:
    """Resolve the role for a Discord ID, or None if they have no access.

    Returns 'gm' if on either or both whitelists with gm membership; 'player'
    if on the player whitelist only; None if on neither. GM membership
    promotes to 'gm' even without explicit player_whitelist membership, since
    gm ≥ player and a GM never needs less access than a player.
    """
    on_gm = config.gm_whitelist.is_allowed(discord_id)
    on_player = config.player_whitelist.is_allowed(discord_id)
    if on_gm:
        return 'gm'
    if on_player:
        return 'player'
    return None


def authenticate_request(cookie_value: str | None, config: AuthConfig) -> CurrentUser | None:
    """Given a raw cookie value, return the authenticated user or None."""
    if not cookie_value or not config.is_configured:
        return None
    discord_id = parse_session_cookie(cookie_value, config.session_secret)
    if discord_id is None:
        return None
    role = role_for(discord_id, config)
    if role is None:
        # User was on a whitelist when they signed in but has been removed since.
        return None
    # Prefer the player_whitelist's display name; fall back to gm_whitelist
    # for GM-only entries that aren't duplicated in player_whitelist.
    # role_for() above already confirmed the user is on at least one
    # whitelist, and parse_whitelist_section enforces non-empty names, so
    # at least one of these lookups must return a non-empty string.
    name = config.player_whitelist.name_for(discord_id) or config.gm_whitelist.name_for(discord_id)
    assert name is not None  # noqa: S101 - invariant guaranteed by role_for
    return CurrentUser(discord_id=discord_id, name=name, role=role)


def to_jsonable(user: CurrentUser | None) -> str:
    """Render a user for logging (no secrets)."""
    if user is None:
        return 'anonymous'
    return json.dumps({'id': user.discord_id, 'name': user.name, 'role': user.role})

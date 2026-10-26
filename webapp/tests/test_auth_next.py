"""Signing in comes back to the page it started from (GM 2026-10-26, from the shrine builder).

/auth/login?next=<path> -> /auth/start?next=<path> (kept in a short-lived cookie, because Discord's
redirect back carries only our own state) -> /auth/callback -> <path>. Only a local path is ever
followed, so a crafted sign-in link cannot send anyone to another site.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import cherrypy
import pytest

from l7r.auth import SESSION_COOKIE_NAME, STATE_COOKIE_NAME, make_session_cookie
from l7r.auth_routes import (
    NEXT_CAP,
    NEXT_COOKIE_NAME,
    AuthRoot,
    _pack,
    _unpack,
    install_auth_tool,
    login_url,
    safe_next,
)
from l7r.jinja_env import build_environment
from tests.test_auth_routes import FakeDiscordClient, _make_config, cp_request  # noqa: F401

SHRINE = '/shrines?shrine_name=The+Fox+Rest&sharing=headmound&sharing=temple#step-review'


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        (SHRINE, SHRINE),
        ('/', '/'),
        ('/money/koku', '/money/koku'),
        ('https://evil.example/', '/'),
        ('//evil.example/', '/'),
        ('/\\evil.example/', '/'),
        ('/x\r\nSet-Cookie: a=b', '/'),
        ('javascript:alert(1)', '/'),
        ('shrines', '/'),
        ('/auth/login', '/'),
        ('/auth?x=1', '/'),
        ('/auth', '/'),
        (None, '/'),
        (['/shrines'], '/'),
    ],
)
def test_safe_next(value: object, expected: str) -> None:
    assert safe_next(value) == expected


def test_a_path_too_long_to_carry_keeps_its_page() -> None:
    long = '/shrines?other_bell=' + 'x' * NEXT_CAP + '#step-review'
    assert safe_next(long) == '/shrines'
    assert len(_pack(safe_next('/shrines?' + 'x' * (NEXT_CAP - 9)))) < 4000  # fits a cookie


def test_pack_round_trips_and_garbage_goes_home() -> None:
    assert _unpack(_pack(SHRINE)) == SHRINE
    assert _unpack('%%%not base64') == '/'
    assert _unpack(None) == ''


def test_login_url_defaults_to_the_current_page(cp_request: Any) -> None:  # noqa: F811
    cherrypy.request.path_info = '/shrines'
    cherrypy.request.query_string = 'kind=kami&bell=suzu'
    assert login_url() == '/auth/login?next=%2Fshrines%3Fkind%3Dkami%26bell%3Dsuzu'
    assert login_url('https://evil.example/') == '/auth/login?next=%2F'


def test_the_round_trip(cp_request: Any) -> None:  # noqa: F811
    root = AuthRoot(
        config=_make_config(), env=build_environment(), discord_client=FakeDiscordClient()
    )
    page = root.login(next=SHRINE).decode()
    assert 'href="/auth/start?next=%2Fshrines%3Fshrine_name%3DThe%2BFox%2BRest' in page
    with pytest.raises(cherrypy.HTTPRedirect):
        root.start(next=SHRINE)
    packed = cherrypy.response.cookie[NEXT_COOKIE_NAME].value
    assert _unpack(packed) == SHRINE
    cherrypy.request.cookie[STATE_COOKIE_NAME] = 'st'
    cherrypy.request.cookie[NEXT_COOKIE_NAME] = packed
    with pytest.raises(cherrypy.HTTPRedirect) as done:
        root.callback(code='goodcode', state='st')
    assert done.value.urls[0].endswith(SHRINE)
    assert cherrypy.response.cookie[NEXT_COOKIE_NAME]['max-age'] == 0  # used once


def test_a_tampered_cookie_goes_home(cp_request: Any) -> None:  # noqa: F811
    root = AuthRoot(
        config=_make_config(), env=build_environment(), discord_client=FakeDiscordClient()
    )
    cherrypy.request.cookie[STATE_COOKIE_NAME] = 'st'
    cherrypy.request.cookie[NEXT_COOKIE_NAME] = _pack('//evil.example/')
    with pytest.raises(cherrypy.HTTPRedirect) as done:
        root.callback(code='goodcode', state='st')
    url = done.value.urls[0]
    assert 'evil' not in url
    assert urlsplit(url).path == '/'


def test_already_signed_in_goes_straight_back(cp_request: Any) -> None:  # noqa: F811
    root = AuthRoot(
        config=_make_config(), env=build_environment(), discord_client=FakeDiscordClient()
    )
    cherrypy.request.cookie[SESSION_COOKIE_NAME] = make_session_cookie('123', 'secret')
    with pytest.raises(cherrypy.HTTPRedirect) as done:
        root.login(next='/money/koku')
    assert done.value.urls[0].endswith('/money/koku')


def test_a_gated_page_sends_its_own_address_to_login(cp_request: Any) -> None:  # noqa: F811
    install_auth_tool(_make_config())
    cherrypy.request.path_info = '/chargen'
    cherrypy.request.query_string = 'caste=monk'
    with pytest.raises(cherrypy.HTTPRedirect) as done:
        cherrypy.tools.l7r_auth.callable()
    assert done.value.urls[0].endswith('/auth/login?next=%2Fchargen%3Fcaste%3Dmonk')


def test_the_nav_and_shrine_links_carry_the_page(cp_request: Any) -> None:  # noqa: F811
    from l7r.app import Root

    cherrypy.request.path_info = '/shrines'
    cherrypy.request.query_string = 'kind=kami'
    page = Root(relics=[]).shrines(kind='kami').decode()
    assert page.count('href="/auth/login?next=%2Fshrines%3Fkind%3Dkami" data-signin') == 2

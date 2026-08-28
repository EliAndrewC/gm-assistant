"""The Obsidian Portal consent census (l7r.opcrawl). Every page it parses is a saved fixture;
the HTTP boundary is exercised against a local server thread, never the real site."""

from __future__ import annotations

import http.server
import json
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest

from l7r.opcrawl import (
    OWN_CAMPAIGNS,
    Census,
    CensusRow,
    FrontPage,
    parse_exempt_slugs,
    parse_front_page,
    parse_robots,
    run_census,
    summarize,
)
from l7r.opcrawl.census import (
    HOST,
    HUMAN_CHECK_COOKIE,
    ConsentError,
    Throttle,
    _Site,
    load_policy,
    write_census,
)
from l7r.opcrawl.http import USER_AGENT, Response, http_get
from l7r.opcrawl.robots import RECORDED, RobotsPolicy

FIX = Path(__file__).parent / 'fixtures' / 'opcrawl'


def fixture(name: str) -> str:
    return (FIX / name).read_text()


class TestRobots:
    def test_recorded_policy_matches_the_saved_file(self) -> None:
        assert parse_robots(fixture('robots.txt')) == RECORDED

    def test_named_agent_group_wins_over_star(self) -> None:
        assert parse_robots(fixture('robots.txt'), 'GPTBot') == RobotsPolicy(None, (), ('/',))
        assert parse_robots(fixture('robots.txt'), 'Bingbot') == RECORDED

    @pytest.mark.parametrize(
        ('path', 'ok'),
        [
            ('/campaigns?game_system_id=62', True),
            ('/robots.txt', True),
            ('/pre-human-check?ch=x', False),
            ('/profile/eli', False),
            ('/oauth/authorize', False),
            ('/messages/1', False),
            ('/login?next=/', False),
            ('/login', True),
        ],
    )
    def test_longest_match(self, path: str, ok: bool) -> None:
        assert RECORDED.allows(path) is ok

    def test_tie_goes_to_allow_and_empty_file_allows_all(self) -> None:
        assert RobotsPolicy(None, ('/a',), ('/a',)).allows('/a/b')
        assert parse_robots('') == RobotsPolicy(None, (), ())
        assert parse_robots('').allows('/anything')

    def test_stacked_agents_share_a_group_and_comments_are_ignored(self) -> None:
        text = (
            'User-agent: a\nUser-agent: b\nDisallow: /x # why\nCrawl-delay: 5\n\n'
            'User-agent: c\nAllow:\n'
        )
        assert parse_robots(text, 'b') == RobotsPolicy(5.0, (), ('/x',))
        assert parse_robots(text, 'c') == RobotsPolicy(None, (), ())


class TestPages:
    def test_exempt_slugs(self) -> None:
        exempt = parse_exempt_slugs(fixture('gate.html'))
        assert set(OWN_CAMPAIGNS) <= exempt
        assert 'l5rsilkandsteel' in exempt
        assert 'legends-of-rokugan' not in exempt

    @pytest.mark.parametrize(
        'bad',
        [
            '<div></div>',
            "<div data-exempt-cses='{&quot;a&quot;:1}'>",
            "<div data-exempt-cses='[1]'>",
        ],
    )
    def test_exempt_list_shape_is_checked(self, bad: str) -> None:
        with pytest.raises(ValueError, match='data-exempt-cses'):
            parse_exempt_slugs(bad)

    def test_front_page(self) -> None:
        assert parse_front_page(fixture('front-hiddenway.html')) == FrontPage(
            'The Hidden Way', 'Legend of the Five Rings', 62, '2026-06-28T07:01:51-04:00'
        )
        assert parse_front_page(fixture('front-other.html')) == FrontPage(
            'Silk & Steel', 'Dungeons & Dragons 5e', 7, ''
        )

    def test_front_page_without_markers(self) -> None:
        assert parse_front_page('<html><title>Nope</title></html>') == FrontPage('', '', None, '')


class TestThrottle:
    def test_sleeps_only_the_remaining_delay(self) -> None:
        now = [100.0]
        slept: list[float] = []

        def sleep(s: float) -> None:
            slept.append(s)
            now[0] += s

        t = Throttle(20.0, clock=lambda: now[0], sleep=sleep)
        t.wait()  # first request: no wait
        now[0] += 5
        t.wait()  # 15 s remaining
        now[0] += 25
        t.wait()  # already past the delay
        assert slept == [15.0]


CHALLENGE = (
    '<html><head><title>Just a moment...</title></head><body>'
    '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script></body></html>'
)


class FakeSite:
    """Answers the URLs the census asks for from fixtures, recording the order and cookies."""

    def __init__(self, robots: str | None = None, gate: str | None = None) -> None:
        self.robots = fixture('robots.txt') if robots is None else robots
        self.gate = fixture('gate.html') if gate is None else gate
        self.urls: list[str] = []
        self.cookies: list[str | None] = []
        self.challenge_slug: str | None = None

    def __call__(self, url: str, cookie: str | None) -> Response:
        self.urls.append(url)
        self.cookies.append(cookie)
        if url == f'{HOST}/robots.txt':
            return Response(200, None, self.robots)
        if url == f'https://{OWN_CAMPAIGNS[0]}.obsidianportal.com/' and cookie is None:
            return Response(302, f'{HOST}/pre-human-check?ch=x&path=/', '')
        if url.startswith(f'{HOST}/pre-human-check'):
            return Response(200, None, self.gate)
        slug = url.removeprefix('https://').split('.')[0]
        if slug == self.challenge_slug:
            return Response(403, None, CHALLENGE)
        if slug == 'horai':
            return Response(404, None, 'gone')
        if slug in OWN_CAMPAIGNS or slug == 'l5rsilkandsteel':
            return Response(200, None, fixture('front-hiddenway.html'))
        return Response(200, None, fixture('front-other.html'))


def run(site: FakeSite, **kw: object) -> tuple[Census, list[float]]:
    slept: list[float] = []
    now = [0.0]

    def sleep(s: float) -> None:
        slept.append(s)
        now[0] += s

    census = run_census(site, clock=lambda: now[0], sleep=sleep, **kw)  # type: ignore[arg-type]
    return census, slept


class TestCensus:
    def test_full_run(self) -> None:
        site = FakeSite()
        messages: list[str] = []
        census, slept = run(site, progress=messages.append)
        assert census.crawl_delay == 20.0
        assert census.exempt_total == 9
        assert len(census.rows) == 9
        assert [r.slug for r in census.crawlable] == ['l5rsilkandsteel']
        by_slug = {r.slug: r for r in census.rows}
        assert by_slug['hiddenway'].own
        assert by_slug['hiddenway'].game_system_id == 62
        assert by_slug['horai'].http_status == 404
        assert by_slug['horai'].game_system == ''
        assert by_slug['shadowrun-throw-back'].game_system == 'Dungeons & Dragons 5e'
        assert messages[0] == 'exempt list: 9 campaigns site-wide'
        assert '9/9 waspbountyhunters: Legend of the Five Rings' in messages
        assert '4/9 horai: HTTP 404' in messages
        # robots, own root, gate hop, then one front page per exempt slug - every one throttled.
        assert len(site.urls) == 3 + 9
        assert slept == [20.0] * (2 + 9)
        assert site.cookies[:3] == [None, None, None]
        assert set(site.cookies[3:]) == {HUMAN_CHECK_COOKIE}

    def test_delay_option_raises_but_never_lowers(self) -> None:
        census, slept = run(FakeSite(), delay=61.0)
        assert census.crawl_delay == 61.0
        assert set(slept) == {61.0}
        census, _ = run(FakeSite(), delay=5.0)
        assert census.crawl_delay == 20.0

    def test_live_delay_raises_but_never_lowers_the_floor(self) -> None:
        census, _ = run(FakeSite(robots='User-agent: *\nCrawl-delay: 30\nAllow: /\n'))
        assert census.crawl_delay == 30.0
        census, _ = run(FakeSite(robots='User-agent: *\nCrawl-delay: 1\nAllow: /\n'))
        assert census.crawl_delay == 20.0

    def test_refuses_when_robots_changes_under_us(self) -> None:
        with pytest.raises(ConsentError, match='no longer allows /'):
            load_policy(FakeSite(robots='User-agent: *\nDisallow: /\n'))
        with pytest.raises(ConsentError, match='HTTP 404'):
            load_policy(lambda _url, _cookie: Response(404, None, ''))
        site = FakeSite()
        with pytest.raises(ConsentError, match='disallows /profile/x'):
            _Site(site, Throttle(0.0), RECORDED).get(f'{HOST}/profile/x')
        assert site.urls == []  # refused before any request was made

    def test_refuses_when_own_campaigns_leave_the_exempt_list(self) -> None:
        gate = "<div data-exempt-cses='[&quot;karmicinquisitors&quot;]'></div>"
        with pytest.raises(ConsentError, match='bureacracy'):
            run(FakeSite(gate=gate))

    def test_cloudflare_challenge_stops_the_run(self) -> None:
        site = FakeSite()
        site.challenge_slug = 'daidoji'
        with pytest.raises(ConsentError, match='Cloudflare challenge'):
            run(site)
        assert site.urls[-1] == 'https://daidoji.obsidianportal.com/'  # nothing after it

    def test_gate_non_200_is_an_error(self) -> None:
        site = FakeSite()

        def fetch(url: str, cookie: str | None) -> Response:
            if url.startswith(f'{HOST}/pre-human-check'):
                return Response(500, None, 'boom')
            return site(url, cookie)

        with pytest.raises(ConsentError, match='HTTP 500'):
            run_census(fetch, sleep=lambda _s: None)

    def test_write_and_summarize(self, tmp_path: Path) -> None:
        census, _ = run(FakeSite())
        path = write_census(census, tmp_path)
        assert path == tmp_path / 'census-62.json'
        data = json.loads(path.read_text())
        assert data['exempt_total'] == 9
        silk = next(r for r in data['rows'] if r['slug'] == 'l5rsilkandsteel')
        assert silk == {
            'slug': 'l5rsilkandsteel',
            'name': 'The Hidden Way',
            'url': 'https://l5rsilkandsteel.obsidianportal.com/',
            'game_system': 'Legend of the Five Rings',
            'game_system_id': 62,
            'updated': '2026-06-28T07:01:51-04:00',
            'http_status': 200,
            'own': False,
        }
        text = summarize(census, path)
        assert '9 campaigns site-wide have "allow bots" on, visited at one request per 20 s' in text
        assert "1 of them are other people's campaigns in game system 62" in text
        assert 'l5rsilkandsteel' in text
        assert 'hiddenway' not in text
        assert text.endswith(f'written to {path} (gitignored)')
        assert not summarize(census).endswith('(gitignored)')

    def test_row_dataclass(self) -> None:
        row = CensusRow('a', 'A', 'https://a.obsidianportal.com/', '', None, '', 200, False)
        assert Census(62, 20.0, 1, [row]).crawlable == []


class Handler(http.server.BaseHTTPRequestHandler):
    agents: list[str] = []
    cookies: list[str | None] = []

    def do_GET(self) -> None:
        Handler.agents.append(self.headers['User-Agent'])
        Handler.cookies.append(self.headers.get('Cookie'))
        if self.path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/target')
            self.end_headers()
        elif self.path == '/missing':
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'gone')
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write('ok é'.encode())

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture(scope='module')
def server() -> Iterator[str]:
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{httpd.server_port}'
    httpd.shutdown()


class TestHttp:
    def test_get_does_not_follow_redirects(self, server: str) -> None:
        assert http_get(f'{server}/redirect') == Response(302, '/target', '')
        assert http_get(f'{server}/target', cookie='human_check=') == Response(200, None, 'ok é')
        assert http_get(f'{server}/missing') == Response(404, None, 'gone')
        assert set(Handler.agents) == {USER_AGENT}
        assert Handler.cookies == [None, 'human_check=', None]

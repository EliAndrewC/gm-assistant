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
    parse_browse,
    parse_exempt_slugs,
    parse_robots,
    run_census,
    summarize,
)
from l7r.opcrawl.census import HOST, ConsentError, Throttle, load_policy, write_census
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

    def test_browse_tiles_and_pagination(self) -> None:
        tiles, total = parse_browse(fixture('browse-p1.html'))
        assert total == 2
        assert [t.slug for t in tiles] == [
            'karmicinquisitors',
            'l5rsilkandsteel',
            'legends-of-rokugan',
        ]
        silk = tiles[1]
        assert silk.name == 'Legend of the Five Rings: Silk & Steel'
        assert silk.visibility == 'public'
        assert silk.game_system == 'Legend of the Five Rings'
        assert silk.updated == '2024-01-02T03:04:05Z'
        assert silk.url == 'https://l5rsilkandsteel.obsidianportal.com/'
        assert tiles[2].name == 'Legends of Rokugan'

    def test_browse_without_pagination_is_one_page(self) -> None:
        tiles, total = parse_browse('<html></html>')
        assert (tiles, total) == ([], 1)

    def test_tile_without_details(self) -> None:
        page = (
            "<a class='campaign-thumb-and-info' href='https://x.obsidianportal.com/'>"
            "<h4 class='underlined name'>X</h4><small class='underlined name'>private</small></a>"
        )
        (tile,), _ = parse_browse(page)
        assert (tile.game_system, tile.updated, tile.visibility) == ('', '', 'private')


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


class FakeSite:
    """Answers the URLs the census asks for from fixtures, recording the order."""

    def __init__(self, robots: str | None = None, gate: str | None = None) -> None:
        self.robots = fixture('robots.txt') if robots is None else robots
        self.gate = fixture('gate.html') if gate is None else gate
        self.urls: list[str] = []

    def __call__(self, url: str) -> Response:
        self.urls.append(url)
        if url == f'{HOST}/robots.txt':
            return Response(200, None, self.robots)
        if url == f'https://{OWN_CAMPAIGNS[0]}.obsidianportal.com/':
            return Response(302, f'{HOST}/pre-human-check?ch=x&path=/', '')
        if url.startswith(f'{HOST}/pre-human-check'):
            return Response(200, None, self.gate)
        if url == f'{HOST}/campaigns?game_system_id=62&page=1':
            return Response(200, None, fixture('browse-p1.html'))
        if url == f'{HOST}/campaigns?game_system_id=62&page=2':
            return Response(200, None, fixture('browse-p2.html'))
        return Response(404, None, 'nope')


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
        assert census.pages == 2
        assert census.crawl_delay == 20.0
        assert census.exempt_total == 9
        assert [r.slug for r in census.rows] == [
            'karmicinquisitors',
            'l5rsilkandsteel',
            'legends-of-rokugan',
            'horai',
            'shadowed-autumn-leaves',
        ]
        assert [r.slug for r in census.crawlable] == ['l5rsilkandsteel', 'horai']
        own = census.rows[0]
        assert (own.own, own.exempt) == (True, True)
        assert messages[0] == 'exempt list: 9 campaigns site-wide'
        assert messages[-1] == 'page 2/2: 5 campaigns so far'
        # Every request after the first waited the full delay - the redirect hop included.
        assert len(site.urls) == 5
        assert slept == [20.0] * 4
        assert site.urls[1:3] == [
            'https://karmicinquisitors.obsidianportal.com/',
            f'{HOST}/pre-human-check?ch=x&path=/',
        ]

    def test_live_delay_raises_but_never_lowers_the_floor(self) -> None:
        _, slept = run(FakeSite(robots='User-agent: *\nCrawl-delay: 30\nAllow: /\n'))
        assert slept == [30.0] * 4
        census, slept = run(FakeSite(robots='User-agent: *\nCrawl-delay: 1\nAllow: /\n'))
        assert census.crawl_delay == 20.0

    def test_delay_option_raises_but_never_lowers(self) -> None:
        census, slept = run(FakeSite(), delay=60.0)
        assert census.crawl_delay == 60.0
        assert slept == [60.0] * 4
        census, _ = run(FakeSite(), delay=5.0)
        assert census.crawl_delay == 20.0

    def test_refuses_when_robots_changes_under_us(self) -> None:
        with pytest.raises(ConsentError, match='no longer allows /campaigns'):
            load_policy(FakeSite(robots='User-agent: *\nDisallow: /campaigns\n'))
        with pytest.raises(ConsentError, match='HTTP 404'):
            load_policy(lambda _url: Response(404, None, ''))
        with pytest.raises(ConsentError, match='disallows /campaigns'):
            run(FakeSite(robots='User-agent: *\nAllow: /\nDisallow: /campaigns?*\n'))

    def test_refuses_when_own_campaigns_leave_the_exempt_list(self) -> None:
        gate = "<div data-exempt-cses='[&quot;karmicinquisitors&quot;]'></div>"
        with pytest.raises(ConsentError, match='bureacracy'):
            run(FakeSite(gate=gate))

    def test_cloudflare_challenge_stops_the_run(self) -> None:
        site = FakeSite()
        site.gate = (
            '<html><head><title>Just a moment...</title></head><body>'
            '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script></body></html>'
        )
        with pytest.raises(ConsentError, match='Cloudflare challenge'):
            run(site)
        assert len(site.urls) == 3  # robots, own campaign root, the gate - and nothing after

    def test_non_200_is_an_error(self) -> None:
        with pytest.raises(ConsentError, match='HTTP 404'):
            run(FakeSite(), game_system_id=99)

    def test_write_and_summarize(self, tmp_path: Path) -> None:
        census, _ = run(FakeSite())
        path = write_census(census, tmp_path)
        assert path == tmp_path / 'census-62.json'
        data = json.loads(path.read_text())
        assert data['exempt_total'] == 9
        assert data['rows'][1] == {
            'slug': 'l5rsilkandsteel',
            'name': 'Legend of the Five Rings: Silk & Steel',
            'url': 'https://l5rsilkandsteel.obsidianportal.com/',
            'visibility': 'public',
            'updated': '2024-01-02T03:04:05Z',
            'exempt': True,
            'own': False,
        }
        text = summarize(census, path)
        assert '5 campaigns for game_system_id=62 over 2 pages at one request per 20 s' in text
        assert '9 campaigns site-wide have "allow bots" on' in text
        assert "2 of them are other people's campaigns" in text
        assert 'l5rsilkandsteel' in text
        assert 'horai' in text
        assert 'legends-of-rokugan' not in text
        assert text.endswith(f'written to {path} (gitignored)')
        assert not summarize(census).endswith('(gitignored)')

    def test_row_dataclass(self) -> None:
        row = CensusRow('a', 'A', 'https://a.obsidianportal.com/', 'public', '', False, False)
        assert Census(62, 20.0, 0, 1, [row]).crawlable == []


class Handler(http.server.BaseHTTPRequestHandler):
    agents: list[str] = []

    def do_GET(self) -> None:
        Handler.agents.append(self.headers['User-Agent'])
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

    def log_message(self, *args: object) -> None:  # noqa: D102 - silence the test log
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
        assert http_get(f'{server}/target') == Response(200, None, 'ok é')
        assert http_get(f'{server}/missing') == Response(404, None, 'gone')
        assert set(Handler.agents) == {USER_AGENT}

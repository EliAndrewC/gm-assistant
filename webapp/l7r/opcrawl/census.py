"""The census itself: verify robots.txt, learn the exempt list, visit the front page of every
opted-in campaign once, and write one JSON file saying which of them are L5R and may be read.

Every request goes through `Throttle`, which enforces the larger of the recorded and the live
`Crawl-delay` between ANY two requests to the site, redirect hops included.

WHY THE EXEMPT LIST IS WALKED AND THE CAMPAIGN DIRECTORY IS NOT (measured 2026-08-27/28).
The first design walked `/campaigns?game_system_id=62&page=N`. It was answered with a
Cloudflare challenge (`403`, `cf-mitigated: challenge`) on every attempt across a day, at 20,
61, 121 and 301 s between requests, while robots.txt, the gate page and the GM's own campaign
pages served normally. Two probes at 61 s settled it: four pages of an opted-in campaign, the
unfiltered `/campaigns` and `/campaigns?game_system_id=62` all returned 200; `/campaigns?page=2`
alone was challenged. The rule is on PAGINATION of the directory - the site lets a script see a
listing but not walk it. That is an undocumented but unambiguous wish, so the directory is not
walked by any means (sort orders and search terms would only be the block worked around), and
the GM ruled the same way (2026-08-28). The consent signal never needed the directory: the
exempt list is complete on its own, and each campaign's front page states its game system.

THE ONE robots.txt JUDGMENT CALL (recorded 2026-08-27, the GM may overrule it): `robots.txt`
disallows `/pre-human-check?*`, and that gate page is the only place the exempt list exists. The
census never REQUESTS that path on its own initiative - it requests the root of one of the GM's
OWN campaigns (allowed, and the GM's to read) and follows the server's own 302 to the gate
exactly once per run, throttled. The disallow was read as index-suppression (the page also
carries `noindex` and `x-robots-tag: none`) rather than an access rule. Alternatives priced:
(a) skip the exempt list and treat every campaign as off-limits - defeats the purpose;
(b) ask Obsidian Portal support for the list - worth doing anyway, but it does not make a tool.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from l7r.opcrawl.http import Response, http_get
from l7r.opcrawl.pages import parse_exempt_slugs, parse_front_page
from l7r.opcrawl.robots import RECORDED, RobotsPolicy, parse_robots

Fetcher = Callable[[str, str | None], Response]

HOST = 'https://www.obsidianportal.com'
L5R_GAME_SYSTEM_ID = 62
# The bare cookie the gate's own JavaScript sets for an exempt campaign (`skipHumanCheck`).
HUMAN_CHECK_COOKIE = 'human_check='
# Attempts per URL before a transport error propagates (see `_Site._fetch_retrying`).
RETRIES = 3
# The GM's own campaigns (GM 2026-08-27). Excluded from "other people's games", and the first of
# them is the allowed URL whose redirect reaches the gate page.
OWN_CAMPAIGNS = (
    'karmicinquisitors',
    'bureacracy',
    'kaiu-wall',
    'daidoji',
    'hiddenway',
    'waspbountyhunters',
)


def _shared_opcrawl_dir(module_file: Path) -> Path:
    """The opcrawl cache, resolved to the MAIN checkout's `webapp/opcache/opcrawl` whether the
    tool runs from main or from any session clone.

    The cache is deliberately SHARED across sessions (GM 2026-08-29): a future session should find
    previously-downloaded campaigns without having to know which clone fetched them. Main is the
    tree that holds `.clones/` (the same definition `mainguard` uses), so a clone's path contains
    a `/.clones/<name>/` segment - strip it and everything after to reach main. `opcache/` is
    gitignored in main, so the downloaded pages are never committed; only the tooling is. This is
    the one place opcrawl writes into the main tree, and it is a gitignored data cache, not a
    workspace mutation - the `mainguard` rule it sits beside is about gate/test runs racing a
    push, which this is not.
    """
    parts = module_file.resolve().parts
    if '.clones' in parts:
        root = Path(*parts[: parts.index('.clones')])
    else:
        # <root>/webapp/l7r/opcrawl/census.py -> <root>
        root = module_file.resolve().parents[3]
    return root / 'webapp' / 'opcache' / 'opcrawl'


OUT_DIR = _shared_opcrawl_dir(Path(__file__))


class ConsentError(RuntimeError):
    """The site's published or apparent policy no longer permits what the census wants to do."""


class Throttle:
    """At most one request per `delay` seconds, measured on an injectable clock."""

    def __init__(
        self,
        delay: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.delay = delay
        self._clock = clock
        self._sleep = sleep
        self._last: float | None = None

    def wait(self) -> None:
        if self._last is not None:
            remaining = self.delay - (self._clock() - self._last)
            if remaining > 0:
                self._sleep(remaining)
        self._last = self._clock()


@dataclass(frozen=True)
class CensusRow:
    slug: str
    name: str
    url: str
    game_system: str
    game_system_id: int | None
    updated: str
    http_status: int
    own: bool


@dataclass
class Census:
    game_system_id: int
    crawl_delay: float
    exempt_total: int
    rows: list[CensusRow] = field(default_factory=list)

    @property
    def crawlable(self) -> list[CensusRow]:
        """Other people's campaigns in the target game system whose owners opted in - the only
        ones a fetcher may read."""
        return [
            r
            for r in self.rows
            if r.game_system_id == self.game_system_id and not r.own and r.http_status == 200
        ]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True) + '\n'


def is_challenge(resp: Response) -> bool:
    """A Cloudflare managed-challenge page rather than the content asked for."""
    return (
        '<title>Just a moment...</title>' in resp.text and 'challenges.cloudflare.com' in resp.text
    )


class _Site:
    def __init__(self, fetch: Fetcher, throttle: Throttle, policy: RobotsPolicy) -> None:
        self._fetch, self._throttle, self._policy = fetch, throttle, policy

    def _fetch_retrying(self, url: str, cookie: str | None) -> Response:
        """Retry a TRANSPORT failure (DNS, a dropped connection) a few times, throttled.

        A fault on OUR side of the wire is not the site saying no: on 2026-08-28 a single DNS
        blip 278 campaigns into a 289-campaign run raised out of the whole census. A refusal BY
        the site - a challenge, an HTTP status - is obeyed immediately in `get` and never retried.
        """
        for _ in range(RETRIES - 1):
            try:
                return self._fetch(url, cookie)
            except OSError:
                self._throttle.wait()
        return self._fetch(url, cookie)

    def get(
        self, url: str, *, follow: bool = False, cookie: str | None = None, tolerate: bool = False
    ) -> Response:
        parts = urlsplit(url)
        path = parts.path + ('?' + parts.query if parts.query else '')
        if parts.netloc == urlsplit(HOST).netloc and not self._policy.allows(path):
            raise ConsentError(f'robots.txt now disallows {path}; refusing')
        self._throttle.wait()
        resp = self._fetch_retrying(url, cookie)
        if follow and resp.status in (301, 302, 303, 307, 308) and resp.location:
            self._throttle.wait()
            resp = self._fetch_retrying(resp.location, cookie)
        if is_challenge(resp):
            # Cloudflare's "Just a moment..." interstitial: the site asking us to prove we are a
            # person. That is a NO - stop, never solve it, never route around it.
            raise ConsentError(f'{url} answered with a Cloudflare challenge; stopping')
        if resp.status != 200 and not tolerate:
            raise ConsentError(f'{url} returned HTTP {resp.status}')
        return resp


def load_policy(fetch: Fetcher, delay_floor: float = RECORDED.crawl_delay or 0.0) -> RobotsPolicy:
    """Live robots.txt, checked against the recording: the delay is the larger of the two, and the
    root must still be allowed. Raises ConsentError otherwise."""
    resp = fetch(f'{HOST}/robots.txt', None)
    if resp.status != 200:
        raise ConsentError(f'robots.txt returned HTTP {resp.status}; refusing to guess')
    live = parse_robots(resp.text)
    delay = max(delay_floor, live.crawl_delay or 0.0)
    policy = RobotsPolicy(delay, live.allow, live.disallow)
    if not policy.allows('/'):
        raise ConsentError('robots.txt no longer allows /; refusing')
    return policy


def run_census(
    fetch: Fetcher = http_get,
    *,
    game_system_id: int = L5R_GAME_SYSTEM_ID,
    own: tuple[str, ...] = OWN_CAMPAIGNS,
    delay: float = 0.0,
    known: dict[str, CensusRow] | None = None,
    checkpoint: Callable[[Census], object] = lambda _census: None,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    progress: Callable[[str], None] = lambda _: None,
) -> Census:
    # `delay` can only RAISE the pace. robots.txt says 20 s, but a site's Cloudflare rate rule is
    # configured separately and is often stricter than (or never reconciled with) its robots.txt
    # (GM 2026-08-27), so the CLI runs slower than the published floor by default.
    policy = load_policy(fetch, max(RECORDED.crawl_delay or 0.0, delay))
    throttle = Throttle(policy.crawl_delay or 0.0, clock, sleep)
    throttle.wait()  # robots.txt was a request too
    site = _Site(fetch, throttle, policy)

    gate = site.get(f'https://{own[0]}.obsidianportal.com/', follow=True)
    exempt = parse_exempt_slugs(gate.text)
    missing = [s for s in own if s not in exempt]
    if missing:
        raise ConsentError(f'own campaigns not on the exempt list: {missing}; the signal moved')
    progress(f'exempt list: {len(exempt)} campaigns site-wide')

    # `known` is the resume point: rows a previous run already recorded, kept without re-asking
    # the site for them. `checkpoint` is called after every NEW row, so an interrupted run keeps
    # everything it paid for (the 2026-08-28 DNS failure discarded 4.7 hours of polite requests).
    cached = known or {}
    census = Census(game_system_id, policy.crawl_delay or 0.0, len(exempt))
    for n, slug in enumerate(sorted(exempt), 1):
        prior = cached.get(slug)
        if prior is not None:
            census.rows.append(prior)
            progress(f'{n}/{len(exempt)} {slug}: cached')
            continue
        url = f'https://{slug}.obsidianportal.com/'
        # A deleted or renamed campaign answers 404; that is a fact about the row, not a reason
        # to abandon the run. A challenge still stops everything (inside `get`).
        resp = site.get(url, cookie=HUMAN_CHECK_COOKIE, tolerate=True)
        page = parse_front_page(resp.text) if resp.status == 200 else parse_front_page('')
        census.rows.append(
            CensusRow(
                slug,
                page.name,
                url,
                page.game_system,
                page.game_system_id,
                page.updated,
                resp.status,
                slug in own,
            )
        )
        checkpoint(census)
        tag = page.game_system or f'HTTP {resp.status}'
        progress(f'{n}/{len(exempt)} {slug}: {tag}')
    return census


def read_census(game_system_id: int = L5R_GAME_SYSTEM_ID, out_dir: Path = OUT_DIR) -> Census | None:
    """The census file if one exists - the resume point for an interrupted run."""
    path = out_dir / f'census-{game_system_id}.json'
    if not path.exists():
        return None
    raw = json.loads(path.read_text())
    return Census(
        raw['game_system_id'],
        raw['crawl_delay'],
        raw['exempt_total'],
        [CensusRow(**r) for r in raw['rows']],
    )


def write_census(census: Census, out_dir: Path = OUT_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f'census-{census.game_system_id}.json'
    path.write_text(census.to_json())
    return path


def summarize(census: Census, path: Path | None = None) -> str:
    lines = [
        f'{census.exempt_total} campaigns site-wide have "allow bots" on, visited at one request '
        f'per {census.crawl_delay:g} s',
        f"{len(census.crawlable)} of them are other people's campaigns in game system "
        f'{census.game_system_id}:',
    ]
    lines += [f'  {r.slug:40} {r.name}  (updated {r.updated[:10]})' for r in census.crawlable]
    if path is not None:
        lines.append(f'written to {path} (gitignored)')
    return '\n'.join(lines)

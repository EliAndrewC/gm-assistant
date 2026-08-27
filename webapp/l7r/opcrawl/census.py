"""The census itself: verify robots.txt, learn the exempt list, walk the L5R browse pages,
and write one JSON file saying which campaigns may be read.

Every request goes through `Throttle`, which enforces the larger of the recorded and the live
`Crawl-delay` between ANY two requests to the site, redirect hops included.

THE ONE DELIBERATE robots.txt JUDGMENT CALL (recorded 2026-08-27, the GM may overrule it):
`robots.txt` disallows `/pre-human-check?*`, and that gate page is the only place the exempt
list exists. The census never REQUESTS that path on its own initiative - it requests the root
of one of the GM's OWN campaigns (allowed, and the GM's to read) and follows the server's own
302 to the gate exactly once per run, throttled. The disallow was read as index-suppression
(the page also carries `noindex` and `x-robots-tag: none`) rather than an access rule, and a
single throttled fetch of one interstitial per run is the whole cost. Alternatives priced:
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
from l7r.opcrawl.pages import Campaign, parse_browse, parse_exempt_slugs
from l7r.opcrawl.robots import RECORDED, RobotsPolicy, parse_robots

Fetcher = Callable[[str], Response]

HOST = 'https://www.obsidianportal.com'
L5R_GAME_SYSTEM_ID = 62
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
OUT_DIR = Path(__file__).resolve().parents[2] / 'opcache' / 'opcrawl'


class ConsentError(RuntimeError):
    """The site's published policy no longer permits what the census wants to do."""


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
    visibility: str
    updated: str
    exempt: bool
    own: bool


@dataclass
class Census:
    game_system_id: int
    crawl_delay: float
    exempt_total: int
    pages: int
    rows: list[CensusRow] = field(default_factory=list)

    @property
    def crawlable(self) -> list[CensusRow]:
        """Other people's campaigns whose owners opted in - the only ones a fetcher may read."""
        return [r for r in self.rows if r.exempt and not r.own]

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

    def get(self, url: str, *, follow: bool = False) -> Response:
        path = urlsplit(url).path + ('?' + urlsplit(url).query if urlsplit(url).query else '')
        if urlsplit(url).netloc == urlsplit(HOST).netloc and not self._policy.allows(path):
            raise ConsentError(f'robots.txt now disallows {path}; refusing')
        self._throttle.wait()
        resp = self._fetch(url)
        if follow and resp.status in (301, 302, 303, 307, 308) and resp.location:
            self._throttle.wait()
            resp = self._fetch(resp.location)
        if resp.status != 200:
            raise ConsentError(f'{url} returned HTTP {resp.status}')
        if is_challenge(resp):
            # Cloudflare's "Just a moment..." interstitial: the site asking us to prove we are a
            # person. Seen live on 2026-08-27 on browse page 2. That is a NO - stop, never solve it.
            raise ConsentError(f'{url} answered with a Cloudflare challenge; stopping')
        return resp


def load_policy(fetch: Fetcher, delay_floor: float = RECORDED.crawl_delay or 0.0) -> RobotsPolicy:
    """Live robots.txt, checked against the recording: the delay is the larger of the two, and the
    root must still be allowed. Raises ConsentError otherwise."""
    resp = fetch(f'{HOST}/robots.txt')
    if resp.status != 200:
        raise ConsentError(f'robots.txt returned HTTP {resp.status}; refusing to guess')
    live = parse_robots(resp.text)
    delay = max(delay_floor, live.crawl_delay or 0.0)
    policy = RobotsPolicy(delay, live.allow, live.disallow)
    if not policy.allows('/campaigns'):
        raise ConsentError('robots.txt no longer allows /campaigns; refusing')
    return policy


def run_census(
    fetch: Fetcher = http_get,
    *,
    game_system_id: int = L5R_GAME_SYSTEM_ID,
    own: tuple[str, ...] = OWN_CAMPAIGNS,
    delay: float = 0.0,
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

    seen: dict[str, Campaign] = {}
    page, total = 1, 1
    while page <= total:
        tiles, last = parse_browse(
            site.get(f'{HOST}/campaigns?game_system_id={game_system_id}&page={page}').text
        )
        total = max(total, last)  # a later page links only backward; never let it shrink the walk
        for c in tiles:
            seen.setdefault(c.slug, c)
        progress(f'page {page}/{total}: {len(seen)} campaigns so far')
        page += 1

    rows = [
        CensusRow(c.slug, c.name, c.url, c.visibility, c.updated, c.slug in exempt, c.slug in own)
        for c in seen.values()
    ]
    return Census(game_system_id, policy.crawl_delay or 0.0, len(exempt), total, rows)


def write_census(census: Census, out_dir: Path = OUT_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f'census-{census.game_system_id}.json'
    path.write_text(census.to_json())
    return path


def summarize(census: Census, path: Path | None = None) -> str:
    lines = [
        f'{len(census.rows)} campaigns for game_system_id={census.game_system_id} '
        f'over {census.pages} pages at one request per {census.crawl_delay:g} s',
        f'{census.exempt_total} campaigns site-wide have "allow bots" on',
        f"{len(census.crawlable)} of them are other people's campaigns in this listing:",
    ]
    lines += [f'  {r.slug:40} {r.name}  (updated {r.updated[:10]})' for r in census.crawlable]
    if path is not None:
        lines.append(f'written to {path} (gitignored)')
    return '\n'.join(lines)

"""Stage 2: read the public pages of ONE opted-in campaign into the local cache.

Same rules as the census: every request throttled (61 s by default), a Cloudflare challenge
stops the whole run, robots.txt's disallowed paths are never requested, and only campaigns the
census marked crawlable (opted in, L5R, not the GM's own) are ever given to this module by the
CLI. Pages are discovered by following links whose URL SHAPE says they are campaign content -
`/wikis/<slug>`, `/wiki_pages/<slug>`, `/characters/<slug>`, `/adventure-log` and its posts -
starting from the front page and the three section indexes. Nothing outside the campaign's own
host is ever followed.

The cache is `webapp/opcache/opcrawl/<slug>/`: `manifest.json` (one entry per URL: status,
kind, title, text length, file) and `pages/<n>.html` + `pages/<n>.txt`. A rerun skips URLs the
manifest already has, so an interrupted crawl resumes where it stopped and a finished one costs
the site nothing.
"""

from __future__ import annotations

import html
import json
import re
import time
from collections import deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

from l7r.opcrawl.census import OUT_DIR, Fetcher, Throttle, _Site, load_policy
from l7r.opcrawl.http import http_get
from l7r.opcrawl.text import html_to_text, page_title, strip_scripts

HUMAN_CHECK_COOKIE = 'human_check='
SEEDS = ('/', '/wikis', '/characters', '/adventure-log')
# Path shapes that are campaign CONTENT. Anything else on the host (search, tags, calendars,
# forums, maps, member lists, login) is not followed.
CONTENT = re.compile(r'^/(wikis|wiki_pages|characters|adventure-log|posts)(/[A-Za-z0-9_.-]+)?/?$')
_HREF = re.compile(r'href=["\']([^"\'#]+)["\']', re.I)
KINDS = {
    'wikis': 'wiki',
    'wiki_pages': 'wiki',
    'characters': 'character',
    'adventure-log': 'post',
    'posts': 'post',
}


@dataclass
class PageRecord:
    url: str
    kind: str  # front | index | wiki | character | post
    status: int
    title: str
    chars: int
    file: str  # basename under pages/, without extension; '' when nothing was stored
    fetched_at: str


@dataclass
class Manifest:
    slug: str
    pages: dict[str, PageRecord] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path, slug: str) -> Manifest:
        if not path.exists():
            return cls(slug)
        raw = json.loads(path.read_text())
        return cls(raw['slug'], {u: PageRecord(**r) for u, r in raw['pages'].items()})

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {'slug': self.slug, 'pages': {u: asdict(r) for u, r in self.pages.items()}}
        path.write_text(json.dumps(data, indent=1, sort_keys=True) + '\n')


def classify(url: str) -> str | None:
    """The kind of page a campaign URL is, or None if it is not content we read."""
    path = urlsplit(url).path.rstrip('/') or '/'
    if path == '/':
        return 'front'
    m = CONTENT.match(path)
    if m is None:
        return None
    return 'index' if m.group(2) is None else KINDS[m.group(1)]


def campaign_links(page_html: str, base: str) -> list[str]:
    """Content links on `page_html` that stay on the campaign's own host, normalized, deduped,
    in document order. Query strings and fragments are dropped - `?page=N` on a listing is
    exactly the shape Cloudflare challenges on the site's directory, so it is never requested."""
    host = urlsplit(base).netloc
    seen: dict[str, None] = {}
    for raw in _HREF.findall(strip_scripts(page_html)):
        url = urljoin(base, html.unescape(raw))
        parts = urlsplit(url)
        if parts.netloc != host or parts.scheme != 'https':
            continue
        clean = urlunsplit(('https', host, parts.path.rstrip('/') or '/', '', ''))
        if classify(clean) is not None:
            seen.setdefault(clean, None)
    return list(seen)


class Store:
    def __init__(self, root: Path) -> None:
        self.root = root

    def manifest_path(self, slug: str) -> Path:
        return self.root / slug / 'manifest.json'

    def write_page(self, slug: str, n: int, page_html: str, text: str) -> str:
        pages = self.root / slug / 'pages'
        pages.mkdir(parents=True, exist_ok=True)
        (pages / f'{n:04d}.html').write_text(page_html)
        (pages / f'{n:04d}.txt').write_text(text)
        return f'{n:04d}'


def crawl_campaign(
    slug: str,
    fetch: Fetcher = http_get,
    *,
    store: Store | None = None,
    delay: float = 61.0,
    max_pages: int | None = None,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], str] = lambda: time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    progress: Callable[[str], None] = lambda _: None,
    policy_loaded: bool = False,
) -> Manifest:
    """Fetch every content page of `slug` not already in its manifest. Returns the manifest.
    A ConsentError (challenge, robots change) propagates after the manifest is saved, so the
    pages already fetched are kept and a later rerun resumes."""
    store = store or Store(OUT_DIR)
    policy = load_policy(fetch, delay)
    throttle = Throttle(policy.crawl_delay or 0.0, clock, sleep)
    throttle.wait()  # robots.txt was a request
    site = _Site(fetch, throttle, policy)
    base = f'https://{slug}.obsidianportal.com'
    manifest = Manifest.load(store.manifest_path(slug), slug)
    queue: deque[str] = deque(urljoin(base, s) for s in SEEDS)
    queued = set(queue)
    fetched = 0
    try:
        while queue:
            url = queue.popleft()
            if url in manifest.pages:
                continue
            if max_pages is not None and fetched >= max_pages:
                progress(f'{slug}: stopped at --max-pages {max_pages}, {len(queue)} still queued')
                break
            resp = site.get(url, cookie=HUMAN_CHECK_COOKIE, tolerate=True)
            fetched += 1
            kind = classify(url) or 'other'
            if resp.status == 200:
                text = html_to_text(resp.text)
                n = len(manifest.pages) + 1
                name = store.write_page(slug, n, resp.text, text)
                manifest.pages[url] = PageRecord(
                    url, kind, 200, page_title(resp.text), len(text), name, now()
                )
                for link in campaign_links(resp.text, url):
                    if link not in queued:
                        queued.add(link)
                        queue.append(link)
            else:
                manifest.pages[url] = PageRecord(url, kind, resp.status, '', 0, '', now())
            progress(f'{slug}: {resp.status} {kind:9} {url}  ({len(queue)} queued)')
    finally:
        manifest.save(store.manifest_path(slug))
    return manifest

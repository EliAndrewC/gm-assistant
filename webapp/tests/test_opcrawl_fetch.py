"""Stage 2/3 of l7r.opcrawl: the campaign crawler, text extraction and the local index. All
fixture-driven; no request leaves the process."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from l7r.opcrawl.census import HOST, ConsentError
from l7r.opcrawl.fetch import Manifest, PageRecord, Store, campaign_links, classify, crawl_campaign
from l7r.opcrawl.http import Response
from l7r.opcrawl.index import build_index, digest, search
from l7r.opcrawl.text import html_to_text, page_title

FIX = Path(__file__).parent / 'fixtures' / 'opcrawl'
BASE = 'https://hiddenway.obsidianportal.com'


def fixture(name: str) -> str:
    return (FIX / name).read_text()


class TestText:
    def test_title_strips_site_suffixes(self) -> None:
        assert page_title(fixture('wiki-page.html')) == 'Mass combat'
        assert page_title(fixture('front-links.html')) == 'The Hidden Way'
        assert page_title('<title> A | B </title>') == 'A'
        assert page_title('<title></title>') == ''
        assert page_title('no title') == ''

    def test_html_to_text_keeps_blocks_drops_script(self) -> None:
        text = html_to_text(fixture('front-links.html'))
        assert 'from-script' not in text
        assert 'A smuggling operation & its crew.' in text
        assert 'Second paragraph.' in text
        assert '<' not in text
        assert html_to_text('<p>a</p>\n\n\n<p>b</p>') == 'a\n\nb'


class TestLinks:
    @pytest.mark.parametrize(
        ('url', 'kind'),
        [
            (f'{BASE}/', 'front'),
            (f'{BASE}/wikis', 'index'),
            (f'{BASE}/wikis/mass-combat', 'wiki'),
            (f'{BASE}/wiki_pages/mass-combat/', 'wiki'),
            (f'{BASE}/characters/moto-khunbish', 'character'),
            (f'{BASE}/adventure-log', 'index'),
            (f'{BASE}/adventure-log/tea-and-silk', 'post'),
            (f'{BASE}/posts/1', 'post'),
            (f'{BASE}/search', None),
            (f'{BASE}/characters/x/edit', None),
            (f'{BASE}/maps', None),
        ],
    )
    def test_classify(self, url: str, kind: str | None) -> None:
        assert classify(url) == kind

    def test_campaign_links_stay_on_host_and_drop_queries(self) -> None:
        links = campaign_links(fixture('front-links.html'), f'{BASE}/')
        assert links[:3] == [f'{BASE}/wikis', f'{BASE}/characters', f'{BASE}/adventure-log']
        assert f'{BASE}/wikis' in links  # `/wikis?page=2` collapsed onto it, not requested
        assert f'{BASE}/wikis/mass-combat' in links
        assert f'{BASE}/characters/moto-khunbish' in links
        assert f'{BASE}/wikis/from-script' not in links  # hrefs inside <script> are not links
        assert all(u.startswith(BASE) for u in links)
        assert not any('?' in u or 'profile' in u or 'search' in u for u in links)
        assert len(links) == len(set(links))


class FakeCampaign:
    """The pages of a small campaign, answered by URL."""

    def __init__(self) -> None:
        self.urls: list[str] = []
        self.challenge_at: str | None = None

    def __call__(self, url: str, cookie: str | None) -> Response:
        self.urls.append(url)
        if url == f'{HOST}/robots.txt':
            return Response(200, None, fixture('robots.txt'))
        assert cookie == 'human_check='
        if url == self.challenge_at:
            return Response(403, None, '<title>Just a moment...</title>challenges.cloudflare.com')

        def page(title: str, body: str) -> str:
            return f'<title>{title} | X | Obsidian Portal</title>{body}'

        pages = {
            f'{BASE}/': fixture('front-links.html'),
            f'{BASE}/wikis': page('Wiki', '<a href="/wikis/mass-combat">m</a>'),
            f'{BASE}/characters': page('Characters', '<a href="/characters/moto-khunbish">m</a>'),
            f'{BASE}/adventure-log': page('Log', '<a href="/adventure-log/tea-and-silk">t</a>'),
            f'{BASE}/wikis/mass-combat': fixture('wiki-page.html'),
            f'{BASE}/wikis/main-page': page('Main Page', '<p>Hub.</p>'),
            f'{BASE}/characters/moto-khunbish': fixture('character-page.html'),
            f'{BASE}/adventure-log/tea-and-silk': page('Tea and Silk', '<p>First session.</p>'),
        }
        if url in pages:
            return Response(200, None, pages[url])
        return Response(404, None, 'nope')


def crawl(site: FakeCampaign, root: Path, **kw: object) -> tuple[Manifest, list[float]]:
    slept: list[float] = []
    now = [0.0]

    def sleep(s: float) -> None:
        slept.append(s)
        now[0] += s

    m = crawl_campaign(
        'hiddenway',
        site,
        store=Store(root),
        clock=lambda: now[0],
        sleep=sleep,
        now=lambda: 'T',
        **kw,  # type: ignore[arg-type]
    )
    return m, slept


class TestCrawl:
    def test_crawl_discovers_content_and_stores_it(self, tmp_path: Path) -> None:
        site = FakeCampaign()
        messages: list[str] = []
        manifest, slept = crawl(site, tmp_path, progress=messages.append)
        kinds = {u.removeprefix(BASE): r.kind for u, r in manifest.pages.items()}
        assert kinds['/'] == 'front'
        assert kinds['/wikis'] == 'index'
        assert kinds['/wikis/mass-combat'] == 'wiki'
        assert kinds['/characters/moto-khunbish'] == 'character'
        assert kinds['/adventure-log/tea-and-silk'] == 'post'
        assert kinds['/wikis/main-page'] == 'wiki'  # found via the wiki page's link
        assert f'{BASE}/wikis/from-script' not in manifest.pages
        rec = manifest.pages[f'{BASE}/wikis/mass-combat']
        assert rec.title == 'Mass combat'
        assert rec.chars == len(html_to_text(fixture('wiki-page.html')))
        assert (
            (tmp_path / 'hiddenway' / 'pages' / f'{rec.file}.txt')
            .read_text()
            .startswith('Mass combat')
        )
        assert (tmp_path / 'hiddenway' / 'pages' / f'{rec.file}.html').read_text() == fixture(
            'wiki-page.html'
        )
        # robots + every page, each throttled at the 61 s default, never under the floor
        assert len(site.urls) == 1 + len(manifest.pages)
        # links the fake site does not serve (real hrefs from the front page) are recorded as 404
        assert {r.status for r in manifest.pages.values()} == {200, 404}
        assert slept == [61.0] * len(manifest.pages)
        assert messages[-1].startswith('hiddenway: ')
        saved = Manifest.load(tmp_path / 'hiddenway' / 'manifest.json', 'hiddenway')
        assert saved == manifest

    def test_rerun_fetches_nothing_new(self, tmp_path: Path) -> None:
        crawl(FakeCampaign(), tmp_path)
        site = FakeCampaign()
        manifest, slept = crawl(site, tmp_path)
        assert site.urls == [f'{HOST}/robots.txt']
        assert slept == []
        assert len(manifest.pages) > 5

    def test_max_pages_then_resume(self, tmp_path: Path) -> None:
        messages: list[str] = []
        first, _ = crawl(FakeCampaign(), tmp_path, max_pages=2, progress=messages.append)
        assert len(first.pages) == 2
        assert any('stopped at --max-pages 2' in m for m in messages)
        second, _ = crawl(FakeCampaign(), tmp_path)
        assert len(second.pages) > 2
        assert set(first.pages) <= set(second.pages)

    def test_challenge_stops_and_keeps_what_was_fetched(self, tmp_path: Path) -> None:
        site = FakeCampaign()
        site.challenge_at = f'{BASE}/characters'
        with pytest.raises(ConsentError, match='Cloudflare challenge'):
            crawl(site, tmp_path)
        saved = Manifest.load(tmp_path / 'hiddenway' / 'manifest.json', 'hiddenway')
        assert set(saved.pages) == {f'{BASE}/', f'{BASE}/wikis'}
        assert site.urls[-1] == f'{BASE}/characters'

    def test_manifest_roundtrip_and_empty_load(self, tmp_path: Path) -> None:
        assert Manifest.load(tmp_path / 'none.json', 's') == Manifest('s')
        m = Manifest('s', {'u': PageRecord('u', 'wiki', 200, 't', 3, '0001', 'T')})
        m.save(tmp_path / 'd' / 'manifest.json')
        assert Manifest.load(tmp_path / 'd' / 'manifest.json', 's') == m


class TestIndex:
    def test_build_index_and_digest(self, tmp_path: Path) -> None:
        crawl(FakeCampaign(), tmp_path)
        entries = build_index(tmp_path)
        assert [e.slug for e in entries] == ['hiddenway']
        e = entries[0]
        assert e.name == 'The Hidden Way'
        assert e.counts == {'character': 1, 'post': 1, 'wiki': 2}
        assert e.total_chars == sum(e.chars.values()) > 0
        assert all(p.kind in ('wiki', 'character', 'post') for p in e.pages)
        mass = next(p for p in e.pages if p.title == 'Mass combat')
        assert mass.snippet.startswith('Mass combat Armies in Rokugan clash at dawn.')
        md = (tmp_path / 'index.md').read_text()
        assert '## The Hidden Way (hiddenway)' in md
        assert '1 characters, 1 posts, 2 wikis' in md
        assert '[wiki] Mass combat' in md
        data = json.loads((tmp_path / 'index.json').read_text())
        assert data[0]['slug'] == 'hiddenway'
        assert digest([]) == '# Obsidian Portal L5R campaigns - local index\n'

    def test_index_without_front_page_and_untitled(self, tmp_path: Path) -> None:
        m = Manifest('s', {'u': PageRecord('u', 'wiki', 200, '', 0, '', 'T')})
        m.save(tmp_path / 's' / 'manifest.json')
        (e,) = build_index(tmp_path)
        assert e.name == 's'
        assert e.pages[0].snippet == ''
        assert '(untitled)' in (tmp_path / 'index.md').read_text()

    def test_search(self, tmp_path: Path) -> None:
        crawl(FakeCampaign(), tmp_path)
        hits = search('rokugan clash', tmp_path)
        assert [(h.slug, h.title) for h in hits] == [('hiddenway', 'Mass combat')]
        assert 'Armies in Rokugan clash at dawn' in hits[0].context
        assert hits[0].url == f'{BASE}/wikis/mass-combat'
        assert search('no such phrase anywhere', tmp_path) == []

"""Stage 2/3 of l7r.opcrawl: the content summary, the campaign crawler, text extraction and the
local index. All fixture-driven; no request leaves the process."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from l7r.opcrawl.census import HOST, ConsentError, Fetcher
from l7r.opcrawl.fetch import (
    Manifest,
    PageRecord,
    Store,
    campaign_links,
    classify,
    crawl_campaign,
)
from l7r.opcrawl.http import Response
from l7r.opcrawl.index import build_index, digest, search
from l7r.opcrawl.summary import parse_content_summary, summary_url
from l7r.opcrawl.text import html_to_text, page_title

FIX = Path(__file__).parent / 'fixtures' / 'opcrawl'
BASE = 'https://hiddenway.obsidianportal.com'
SUMMARY_URL = f'{BASE}/content_summary.json?cc=1700000000'


def fixture(name: str) -> str:
    return (FIX / name).read_text()


class TestSummary:
    def test_url_carries_the_cache_buster(self) -> None:
        assert summary_url('hiddenway', 1700000000) == SUMMARY_URL

    def test_parse(self) -> None:
        s = parse_content_summary(fixture('content-summary.json'))
        assert s.campaign_id == 259473
        assert s.tags == ('hub', 'unicorn')
        assert s.counts == {'wiki': 2, 'post': 1, 'character': 1}  # the GM-only page is not counted
        assert [p.path for p in s.public] == [
            '/wikis/main-page',
            '/wikis/mass-combat',
            '/adventure-log/tea-and-silk',
            '/characters/moto-khunbish',
        ]
        secret = next(p for p in s.pages if p.gm_only)
        assert secret.path == '/wikis/gm-secrets'
        khunbish = next(p for p in s.pages if p.kind == 'character')
        assert (khunbish.title, khunbish.tags) == ('Moto Khunbish', ('unicorn',))

    @pytest.mark.parametrize('bad', ['[]', '{"x": 1}', 'not json'])
    def test_parse_rejects_other_payloads(self, bad: str) -> None:
        with pytest.raises(ValueError, match='content_summary|Expecting'):
            parse_content_summary(bad)

    def test_entries_without_a_path_are_skipped(self) -> None:
        s = parse_content_summary('{"wiki_pages": [{"title": "x"}, {"path": "/wikis/y"}]}')
        assert [p.path for p in s.pages] == ['/wikis/y']
        assert (s.campaign_id, s.updated_at, s.version, s.tags) == (0, '', '', ())


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
        assert f'{BASE}/wikis/mass-combat' in links
        assert f'{BASE}/characters/moto-khunbish' in links
        assert f'{BASE}/wikis/from-script' not in links  # hrefs inside <script> are not links
        assert all(u.startswith(BASE) for u in links)
        assert not any('?' in u or 'profile' in u or 'search' in u for u in links)
        assert len(links) == len(set(links))


CHALLENGE = '<title>Just a moment...</title>challenges.cloudflare.com'


class FakeCampaign:
    """The pages of a small campaign, answered by URL."""

    def __init__(self, summary: str | None = None) -> None:
        self.summary = fixture('content-summary.json') if summary is None else summary
        self.urls: list[str] = []
        self.challenge_at: str | None = None

    def __call__(self, url: str, cookie: str | None) -> Response:
        self.urls.append(url)
        if url == f'{HOST}/robots.txt':
            return Response(200, None, fixture('robots.txt'))
        assert cookie == 'human_check='
        if url == self.challenge_at:
            return Response(403, None, CHALLENGE)
        if url.startswith(f'{BASE}/content_summary.json'):
            if not self.summary:
                return Response(400, None, '')
            return Response(200, None, self.summary)

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


def crawl(site: Fetcher, root: Path, **kw: object) -> tuple[Manifest, list[float]]:
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
        unix_time=lambda: 1700000000,
        **kw,  # type: ignore[arg-type]
    )
    return m, slept


class TestCrawlWithSummary:
    def test_the_summary_is_the_crawl_list(self, tmp_path: Path) -> None:
        site = FakeCampaign()
        messages: list[str] = []
        manifest, slept = crawl(site, tmp_path, progress=messages.append)
        assert site.urls[:3] == [f'{HOST}/robots.txt', SUMMARY_URL, f'{BASE}/']
        # exactly the front page plus the summary's PUBLIC pages - the GM-only one is never asked
        assert sorted(u.removeprefix(BASE) for u in manifest.pages) == [
            '/',
            '/adventure-log/tea-and-silk',
            '/characters/moto-khunbish',
            '/wikis/main-page',
            '/wikis/mass-combat',
        ]
        assert not any('gm-secrets' in u for u in site.urls)
        # and no link discovery: /wikis, /characters and the front page's other links are skipped
        assert f'{BASE}/wikis' not in manifest.pages
        assert 'hiddenway: content summary lists 1 characters, 1 posts, 2 wikis' in messages
        assert (
            json.loads((tmp_path / 'hiddenway' / 'content_summary.json').read_text())['id']
            == 259473
        )
        assert slept == [61.0] * 6  # summary + 5 pages, each throttled at the default pace

    def test_summary_only_stops_after_one_request(self, tmp_path: Path) -> None:
        site = FakeCampaign()
        manifest, _ = crawl(site, tmp_path, summary_only=True)
        assert site.urls == [f'{HOST}/robots.txt', SUMMARY_URL]
        assert manifest.pages == {}
        assert (tmp_path / 'hiddenway' / 'content_summary.json').exists()

    @pytest.mark.parametrize('summary', ['', 'not json at all'])
    def test_without_a_usable_summary_it_falls_back_to_link_discovery(
        self, tmp_path: Path, summary: str
    ) -> None:
        site = FakeCampaign(summary)
        messages: list[str] = []
        manifest, _ = crawl(site, tmp_path, progress=messages.append)
        assert any('falling back to link discovery' in m for m in messages)
        assert f'{BASE}/wikis' in manifest.pages  # the section indexes are seeds again
        assert f'{BASE}/wikis/mass-combat' in manifest.pages  # found by following links
        assert f'{BASE}/wikis/main-page' in manifest.pages  # found via the wiki page's own link


class TestCrawl:
    def test_pages_are_stored_with_text(self, tmp_path: Path) -> None:
        site = FakeCampaign()
        manifest, _ = crawl(site, tmp_path)
        rec = manifest.pages[f'{BASE}/wikis/mass-combat']
        assert (rec.kind, rec.title, rec.status) == ('wiki', 'Mass combat', 200)
        assert rec.chars == len(html_to_text(fixture('wiki-page.html')))
        pages = tmp_path / 'hiddenway' / 'pages'
        assert (pages / f'{rec.file}.txt').read_text().startswith('Mass combat')
        assert (pages / f'{rec.file}.html').read_text() == fixture('wiki-page.html')
        assert Manifest.load(tmp_path / 'hiddenway' / 'manifest.json', 'hiddenway') == manifest

    def test_missing_page_is_recorded_not_fatal(self, tmp_path: Path) -> None:
        site = FakeCampaign(json.dumps({'wiki_pages': [{'path': '/wikis/deleted', 'title': 'X'}]}))
        manifest, _ = crawl(site, tmp_path)
        assert manifest.pages[f'{BASE}/wikis/deleted'].status == 404
        assert manifest.pages[f'{BASE}/wikis/deleted'].chars == 0

    def test_rerun_fetches_only_the_summary(self, tmp_path: Path) -> None:
        crawl(FakeCampaign(), tmp_path)
        site = FakeCampaign()
        manifest, _ = crawl(site, tmp_path)
        assert site.urls == [f'{HOST}/robots.txt', SUMMARY_URL]
        assert len(manifest.pages) == 5

    def test_max_pages_then_resume(self, tmp_path: Path) -> None:
        messages: list[str] = []
        first, _ = crawl(FakeCampaign(), tmp_path, max_pages=2, progress=messages.append)
        assert len(first.pages) == 2
        assert any('stopped at --max-pages 2' in m for m in messages)
        second, _ = crawl(FakeCampaign(), tmp_path)
        assert len(second.pages) == 5
        assert set(first.pages) <= set(second.pages)

    def test_challenge_stops_and_keeps_what_was_fetched(self, tmp_path: Path) -> None:
        site = FakeCampaign()
        site.challenge_at = f'{BASE}/wikis/main-page'
        with pytest.raises(ConsentError, match='Cloudflare challenge'):
            crawl(site, tmp_path)
        saved = Manifest.load(tmp_path / 'hiddenway' / 'manifest.json', 'hiddenway')
        assert set(saved.pages) == {f'{BASE}/'}
        assert site.urls[-1] == f'{BASE}/wikis/main-page'

    def test_manifest_roundtrip_and_empty_load(self, tmp_path: Path) -> None:
        assert Manifest.load(tmp_path / 'none.json', 's') == Manifest('s')
        m = Manifest('s', {'u': PageRecord('u', 'wiki', 200, 't', 3, '0001', 'T')})
        m.save(tmp_path / 'd' / 'manifest.json')
        assert Manifest.load(tmp_path / 'd' / 'manifest.json', 's') == m

    def test_store_reads_back_a_summary_and_shrugs_at_a_broken_one(self, tmp_path: Path) -> None:
        store = Store(tmp_path)
        assert store.read_summary('nobody') is None
        store.write_summary('broken', 'not json')
        assert store.read_summary('broken') is None
        store.write_summary('ok', fixture('content-summary.json'))
        assert store.read_summary('ok') is not None


class TestIndex:
    def test_index_from_summary_alone(self, tmp_path: Path) -> None:
        """The GM's first question - who has uploaded a lot - answered with no page fetched."""
        crawl(FakeCampaign(), tmp_path, summary_only=True)
        (entry,) = build_index(tmp_path, names={'hiddenway': 'The Hidden Way'})
        assert entry.name == 'The Hidden Way'
        assert entry.available == {'wiki': 2, 'post': 1, 'character': 1}
        assert entry.total_available == 4
        assert entry.counts == {}
        assert [p.title for p in entry.pages] == [  # by kind, then title
            'Moto Khunbish',
            'Tea and Silk',
            'Main Page',
            'Mass combat',
        ]
        assert not any(p.cached for p in entry.pages)
        md = (tmp_path / 'index.md').read_text()
        assert 'publishes 1 characters, 1 posts, 2 wikis; cached no pages, 0 characters' in md
        assert '[not cached]' in md
        assert 'tags: hub, unicorn' in md

    def test_index_after_a_crawl(self, tmp_path: Path) -> None:
        crawl(FakeCampaign(), tmp_path)
        (entry,) = build_index(tmp_path)
        assert entry.name == 'The Hidden Way'  # from the cached front page
        assert entry.counts == {'wiki': 2, 'post': 1, 'character': 1}
        assert entry.total_chars > 0
        assert all(p.cached for p in entry.pages)
        mass = next(p for p in entry.pages if p.title == 'Mass combat')
        assert mass.snippet.startswith('Mass combat Armies in Rokugan clash at dawn.')
        khunbish = next(p for p in entry.pages if p.kind == 'character')
        assert khunbish.tags == ('unicorn',)
        data = json.loads((tmp_path / 'index.json').read_text())
        assert data[0]['slug'] == 'hiddenway'
        md = (tmp_path / 'index.md').read_text()
        assert '## The Hidden Way (hiddenway)' in md
        assert '[not cached]' not in md

    def test_index_of_a_link_discovered_campaign(self, tmp_path: Path) -> None:
        crawl(FakeCampaign(''), tmp_path)
        (entry,) = build_index(tmp_path)
        assert entry.available == {}
        assert entry.counts['wiki'] == 2  # discovered pages still counted
        assert all(p.cached for p in entry.pages)

    def test_index_edges(self, tmp_path: Path) -> None:
        m = Manifest('s', {'u': PageRecord('u', 'wiki', 200, '', 0, '', 'T')})
        m.save(tmp_path / 's' / 'manifest.json')
        (e,) = build_index(tmp_path)
        assert e.name == 's'
        assert e.pages[0].snippet == ''
        assert '(untitled)' in (tmp_path / 'index.md').read_text()
        assert digest([]) == '# Obsidian Portal L5R campaigns - local index\n'

    def test_search(self, tmp_path: Path) -> None:
        crawl(FakeCampaign(), tmp_path)
        hits = search('rokugan clash', tmp_path)
        assert [(h.slug, h.title) for h in hits] == [('hiddenway', 'Mass combat')]
        assert 'Armies in Rokugan clash at dawn' in hits[0].context
        assert hits[0].url == f'{BASE}/wikis/mass-combat'
        assert search('no such phrase anywhere', tmp_path) == []

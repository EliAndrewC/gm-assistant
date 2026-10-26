"""The price sheets (feature 225): every Rokugani price on exactly one sheet, and the page."""

from __future__ import annotations

import html
from pathlib import Path

import pytest

from l7r.app import Root
from l7r.money import ledger, prices
from l7r.money.ledger import Row


@pytest.fixture
def root() -> Root:
    return Root(relics=[])


@pytest.fixture(scope='module')
def rows() -> list[Row]:
    return ledger.load()


@pytest.fixture(scope='module')
def views(rows: list[Row]) -> dict[str, prices.SheetView]:
    return {v.sheet.id: v for v in prices.sheets(rows, ledger.load_swings(), 453.0, 9398.0)}


def test_every_eligible_row_is_on_exactly_one_sheet(
    rows: list[Row], views: dict[str, prices.SheetView]
) -> None:
    """FR-001, both directions: nothing eligible is dropped, nothing is shown twice."""
    assert prices.unplaced(rows) == []
    shown = [it.row.id for v in views.values() for it in v.items]
    assert len(shown) == len(set(shown))
    assert set(shown) == {r.id for r in rows if prices.eligible(r)}


def test_shrine_builder_lines_stay_off_but_the_fox_charcoal_is_fuel(
    rows: list[Row], views: dict[str, prices.SheetView]
) -> None:
    """Spec-fidelity round 1: the tag `shrine` alone also marks an ordinary fuel price."""
    fuel = {it.row.id for it in views['fuel'].items}
    fox = [r for r in rows if r.id and 'shrine' in r.tags and 'charcoal' in r.tags]
    assert len(fox) == 11
    assert {r.id for r in fox} <= fuel
    builder = [r for r in rows if r.id and {'construction', 'shrine'} <= set(r.tags)]
    assert builder
    assert not any(prices.eligible(r) for r in builder)


def test_comparative_and_source_rows_are_never_rokugani_prices() -> None:
    base = {'item': 'x', 'low': 1, 'high': 2, 'per': 'item', 'source': 'lead:x', 'tags': ('food',)}
    assert not prices.eligible(Row(**{**base, 'label': 'comparative', 'id': 'c'}))  # type: ignore[arg-type]
    assert not prices.eligible(Row(**{**base, 'label': 'estimated'}))  # type: ignore[arg-type]
    orphan = Row(**{**base, 'label': 'estimated', 'id': 'o', 'tags': ('nothing',)})  # type: ignore[arg-type]
    assert prices.unplaced([orphan]) == ['o']
    assert prices.sheet_for(orphan) is None


def test_items_read_in_coins_days_and_the_sheets_dollars(
    views: dict[str, prices.SheetView],
) -> None:
    wages = {it.row.id: it for it in views['wages'].items}
    day = wages['wage-unskilled-day']
    assert (day.price, day.days, day.solidity) == (
        '1 zeni 2 sen to 1 zeni 3 sen',
        '1.0',
        'researched',
    )
    fuel = {it.row.id: it for it in views['fuel'].items}
    assert fuel['charcoal-white-bag'].solidity == 'extrapolated'  # the GM's example (227)
    assert {it.solidity for v in views.values() for it in v.items} <= {
        'researched',
        'extrapolated',
        'estimated',
    }
    assert day.dollars == '$113 to $122'  # wage dollars: 12-13 sen of a $9,398 koku
    assert views['wages'].sheet.wage
    assert [it.row.id for it in views['wages'].items[:2]] == list(prices.FIRST)
    food = views['food'].items
    assert [it.row.low for it in food] == sorted(it.row.low for it in food)  # cheapest first
    donation = next(it for it in views['entertainment'].items if it.row.low == 0)
    assert donation.price.startswith('up to ')
    assert donation.days.startswith('up to ')
    assert donation.dollars.startswith('up to $')
    assert prices.price(13, 13) == '1 zeni 3 sen'
    assert prices.price(150, 1500) == '1 bu 5 zeni to 1 koku 5 bu'
    assert any(s.cls == 'salt' for _, s in views['food'].swings)
    assert [name for name, s in views['travel'].swings if s.cls == 'rent'] == ['lodging']


def test_source_links_say_where_a_price_comes_from() -> None:
    q = 'https://github.com/EliAndrewC/diagram/blob/main/research/questions/0266-what.html'
    link = prices.source_link(q)
    assert 'href="/research/q/what.html"' in link  # the toolkit's own record (GM 2026-10-26)
    assert 'github.com' not in link
    assert prices.research_url('https://example.com/x') == 'https://example.com/x'
    assert prices.research_title('https://x/0300.html') == 'research'
    assert prices.plain('A scribe: SILENT (0307). In 1736 (0305; two sources) diagram 0266.') == (
        'A scribe: unrecorded. In 1736 (two sources) the research.'
    )
    assert prices.plain('SILENT; ATTESTED ONLY FOR Edo; NOT ATTESTED') == (
        'Unrecorded; recorded only for Edo; not recorded'
    )
    assert '>source</a>' in prices.source_link('https://example.com/a?b=1&c=2')
    assert '&amp;c=2' in prices.source_link('https://example.com/a?b=1&c=2')
    est = prices.source_link('derived:webapp/l7r/money/data/estimates.jsonl#E0170')
    assert 'blob/main/webapp/l7r/money/data/estimates.jsonl' in est
    assert '>a logged estimate, E0170</a>' in est
    assert 'derived in the money skill' in prices.source_link('derived:.claude/skills/money/q.md#x')
    canon = prices.source_link('canon:setting/l7r.md "Rent and taxes"')
    assert (
        'href="https://github.com/EliAndrewC/l7r/blob/master/setting/l7r.md#rent-and-taxes"'
        in canon
    )
    assert '>the setting notes</a>' in canon
    assert prices.canon_url('setting/budgets.md').endswith('/blob/master/setting/budgets.md')
    lead = prices.source_link('lead:setting/weapons.txt')
    assert lead == "the GM's earlier notes, not yet checked against research"
    assert 'weapons.txt' not in lead  # no file path shown to a reader


def test_the_page_and_its_landing_card(root: Root) -> None:
    page = html.unescape(root.money('prices').decode())
    for title in ('Wages and incomes', 'Food and drink', 'Fuel', 'Paper and books'):
        assert f'<h2 class="prices__title">{title}</h2>' in page
    assert 'Inn on the Imperial Road' in page
    assert 'Wage dollars' in page
    assert 'Goods dollars' in page
    assert 'href="/shrines"' in page
    assert 'Across periods (salt: swung).' in page
    assert 'Shrine builder:' not in page
    assert 'href="/money/prices"' in root.money().decode()


def test_research_titles_come_from_the_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import gzip

    q = 'https://github.com/EliAndrewC/diagram/blob/main/research/questions/0307-x-y.html'
    monkeypatch.setattr(prices, 'SITE', tmp_path)
    prices.research_title.cache_clear()
    assert prices.research_title(q) == 'X y?'  # no bundle: from the file name
    prices.research_title.cache_clear()
    (tmp_path / 'x-y.html.gz').write_bytes(
        gzip.compress(b'<title>What did a clerk, a guard &amp; a cook earn? - Money</title>')
    )
    assert prices.research_title(q) == 'What did a clerk, a guard & a cook earn?'
    prices.research_title.cache_clear()
    (tmp_path / 'x-y.html.gz').unlink()
    (tmp_path / 'x-y.html').write_text('<p>no title</p>')
    assert prices.research_title(q) == 'X y?'
    prices.research_title.cache_clear()


def test_every_cited_research_page_exists_in_the_record() -> None:
    """A research link must open a page (0257's slug was wrong in eras.py until 2026-10-26)."""
    import json
    import re

    if not prices.SITE.exists():
        pytest.skip('no bundled research record (make prepare-deploy builds it)')
    data = Path(prices.__file__).parent / 'data'
    text = '\n'.join(
        p.read_text()
        for p in [
            data / 'ledger.jsonl',
            data / 'swings.jsonl',
            *sorted((data / 'eras').glob('*.json')),
        ]
    )
    urls = set(
        re.findall(
            r'https://github\.com/EliAndrewC/diagram/blob/main/research/questions/[^"#\s]+', text
        )
    )
    assert urls
    have = {p.name.removesuffix('.gz') for p in prices.SITE.iterdir()}
    missing = sorted(u for u in urls if prices.research_url(u).rsplit('/', 1)[1] not in have)
    assert missing == [], json.dumps(missing, indent=1)


def test_every_canon_section_cited_is_one_heading_of_its_file() -> None:
    """A canon link opens its section: the heading exists once (GitHub numbers repeats)."""
    import re

    root = Path('/host-l7r-repo')
    if not root.exists():
        pytest.skip('the setting notes are not mounted')
    cited = {
        (m.group(1), m.group(2))
        for r in ledger.load()
        if (m := re.match(r'canon:(\S+)\s+"(.+)"', r.source))
    }
    assert cited
    for path, heading in cited:
        heads = re.findall(r'^#+\s+(.+?)\s*$', (root / path).read_text(), re.M)
        assert [prices.anchor(h) for h in heads].count(prices.anchor(heading)) == 1, heading

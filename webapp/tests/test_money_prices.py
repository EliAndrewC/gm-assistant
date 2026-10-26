"""The price sheets (feature 225): every Rokugani price on exactly one sheet, and the page."""

from __future__ import annotations

import html

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
    assert not prices.eligible(Row(**{**base, 'label': 'guess'}))  # type: ignore[arg-type]
    orphan = Row(**{**base, 'label': 'guess', 'id': 'o', 'tags': ('nothing',)})  # type: ignore[arg-type]
    assert prices.unplaced([orphan]) == ['o']
    assert prices.sheet_for(orphan) is None


def test_items_read_in_coins_days_and_the_sheets_dollars(
    views: dict[str, prices.SheetView],
) -> None:
    wages = {it.row.id: it for it in views['wages'].items}
    day = wages['wage-unskilled-day']
    assert (day.price, day.days, day.solidity) == ('1 zeni 3 sen', '1.0', 'researched')
    assert day.dollars == '$122'  # wage dollars: 13 sen of a $9,398 koku
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
    assert any(s.cls == 'salt' for s in views['food'].swings)


def test_source_links_say_where_a_price_comes_from() -> None:
    q = 'https://github.com/EliAndrewC/diagram/blob/main/research/questions/0266-what.html'
    assert '>research: What?</a>' in prices.source_link(q)
    assert prices.research_title(q.replace('what', 'what-did-sake-cost')) == 'What did sake cost?'
    assert prices.research_title('https://x/0300.html') == 'research'
    assert prices.plain('SILENT; ATTESTED ONLY FOR Edo; NOT ATTESTED') == (
        'unrecorded; recorded only for Edo; not recorded'
    )
    assert '>source</a>' in prices.source_link('https://example.com/a?b=1&c=2')
    assert '&amp;c=2' in prices.source_link('https://example.com/a?b=1&c=2')
    est = prices.source_link('derived:webapp/l7r/money/data/estimates.jsonl#E0170')
    assert 'blob/main/webapp/l7r/money/data/estimates.jsonl' in est
    assert '>a logged estimate, E0170</a>' in est
    assert 'derived in the money skill' in prices.source_link('derived:.claude/skills/money/q.md#x')
    assert prices.source_link('canon:setting/l7r.md "Money"') == (
        'the setting notes, setting/l7r.md &quot;Money&quot;'
    )
    assert prices.source_link('lead:setting/weapons.txt') == (
        'an unverified lead (setting/weapons.txt)'
    )


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

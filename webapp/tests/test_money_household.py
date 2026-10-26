"""The household-work page, /money/household (feature 231)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from l7r.app import Root
from l7r.money import household as hh
from l7r.money import ledger
from l7r.money.readings import LABORER_DAY_SEN


@pytest.fixture
def page() -> str:
    page: str = Root(relics=[]).money('household').decode()
    return page


def test_every_figure_has_a_verdict_and_a_research_source() -> None:
    """FR-001: nothing on the page passes for history without its basis."""
    data = hh.load()
    figs = list(hh.figures(data))
    assert len(figs) > 40
    for fig in figs:
        assert fig['verdict'] in hh.VERDICTS
        assert hh.source_url(data, fig['source']).startswith(hh.RESEARCH)


@pytest.mark.parametrize(
    ('change', 'complaint'),
    [({'verdict': 'PROBABLY'}, 'verdict must be'), ({'source': 'my notes'}, 'source must be')],
)
def test_a_figure_without_its_basis_is_refused(
    tmp_path: Path, change: dict[str, str], complaint: str
) -> None:
    data = {
        'sources': {'farm': '0312-x'},
        'tasks': [{'task': 'Cooking', 'verdict': 'SILENT', 'source': 'farm', **change}],
    }
    path = tmp_path / 'h.json'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match=complaint):
        hh.load(path)


def test_homemade_cloth_beside_its_market_price() -> None:
    """User Story 3: days of work, the ledger's market price, and the days at a day's wage."""
    data = hh.load()
    rows = ledger.load()
    cloth = next(r for r in rows if r.id == 'cloth-cotton-kimono-length')
    tan, year = hh.homemade(data, rows)
    assert (tan.days, tan.market_low, tan.market_high) == (4, cloth.low, cloth.high)
    assert tan.laborer_sen == pytest.approx(4 * LABORER_DAY_SEN)
    assert tan.woman_low == pytest.approx(tan.laborer_sen * 16 / 50)
    assert tan.woman_high == pytest.approx(tan.laborer_sen * 33 / 50)
    assert year.days == pytest.approx(12.8 * 4)
    assert year.market_high == pytest.approx(12.8 * cloth.high)


def test_the_years_cloth_is_its_tan_count_times_four_days() -> None:
    data = hh.load()
    assert data['year']['cloth']['days'] == pytest.approx(12.8 * 4)
    counted = data['year']['bars']
    others = sum(b['days'] for b in counted if 'fieldwork' not in b['label'])
    men_field = next(b['days'] for b in counted if b['label'].startswith("Men's"))
    assert men_field + others == data['year']['counted_total'], 'the 811 excludes women'


def test_the_page_answers_each_part_of_the_request(page: str) -> None:
    for heading in (
        "One farm's year, counted",
        'The tasks, and their time',
        "Did clothes take more of one person's time than farming?",
        'Homemade, beside bought',
        'In the city: buying what a farm made',
        'Class by class',
        'Why so much is missing',
        'The proverb',
    ):
        assert heading in page
    assert "Women's household work was almost never written down at the time." in page
    assert '早起三朝當一工' in page


def test_every_task_is_listed_and_an_untimed_one_reads_not_recorded(page: str) -> None:
    """User Story 2: SILENT times read 'not recorded', never a blank or a guess."""
    for group in hh.load()['tasks']:
        for task in group['items']:
            assert task['task'] in page
    tasks = [t for g in hh.load()['tasks'] for t in g['items']]
    blanks = sum(not t.get('time') for t in tasks) + sum(not t.get('who') for t in tasks)
    assert page.count('<span class="hh-none">not recorded</span>') == blanks


def test_badges_link_to_the_research_record(page: str) -> None:
    assert 'href="/research/q/what-work-did-a-farm-household-do-that-was-never-paid.html"' in page
    assert 'href="/research/q/why-was-womens-household-work-so-rarely-written-down.html"' in page


def test_city_prices_come_from_the_ledger(page: str) -> None:
    """FR-002: the researched city prices are ledger rows, shown in Rokugani coin."""
    ids = {r.id for r in ledger.load()}
    for row in hh.load()['city']:
        if 'ledger' in row:
            assert row['ledger'] in ids
    assert '1 sen a visit' in page


def test_landing_lists_the_page_and_links_its_records_section() -> None:
    landing = Root(relics=[]).money().decode()
    assert 'href="/money/household"' in landing
    assert 'href="/money/household#records"' in landing

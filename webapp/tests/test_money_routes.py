"""Route tests for /money and /money/koku (feature 221), and the playground's link state."""

from __future__ import annotations

import html
import json
import re

import pytest

from l7r.app import Root
from l7r.money import basket as bk
from l7r.money import web
from l7r.money.readings import KOKU_KG, load_wages, wage_dollars_per_koku
from l7r.sections import find_section_by_slug

KG = KOKU_KG['sheet-2017']


@pytest.fixture
def root() -> Root:
    return Root(relics=[])


@pytest.fixture
def model() -> bk.Model:
    return bk.load()


def test_money_is_a_public_section() -> None:
    """FR-014 / FR-017."""
    section = find_section_by_slug('money')
    assert section is not None
    assert section.enabled
    assert section.path == '/money'


def test_landing_lists_the_tool(root: Root) -> None:
    page = root.money().decode()
    assert 'href="/money/koku"' in page
    assert "What's a koku worth?" in page


def test_unknown_tool_is_a_404(root: Root) -> None:
    assert b'koku-form' not in root.money('nope')


def test_default_page_shows_the_standard_koku(root: Root, model: bk.Model) -> None:
    """User Story 5 scenario 1: the standard basket at the newest snapshot, both readings."""
    page = root.money('koku').decode()
    per = bk.reading(model, model.basket(), model.snapshot(), KG).per_koku
    assert f'data-out="per-koku" aria-live="polite">${per:,.0f}<' in page
    assert f'${wage_dollars_per_koku(load_wages()[-1]):,.0f}' in page
    for good in model.goods.values():
        assert f'data-good="{good.id}"' in page
    data = json.loads(re.search(r'id="koku-data">(.*?)</script>', page, re.S).group(1))  # type: ignore[union-attr]
    assert data['newest'] == model.snapshots[-1].date
    assert data['goods']['rice']['silver'] == 1.49


def test_a_link_reopens_its_variant(root: Root) -> None:
    """User Story 5 scenario 2: the server renders what the link says."""
    page = root.money(
        'koku', b='bassino-ma-a', s='2017-04', q_fish='0', x_rice='9', c1='Sake|liter|20|2|12'
    ).decode()
    assert '<option value="bassino-ma-a" selected>' in page
    assert '<option value="2017-04" selected>' in page
    assert 'name="q_fish" value="0"' in page
    assert 'value="Sake"' in page
    assert 'name="c1" value="Sake|liter|20|2|12"' in page


def test_parse_state_ignores_what_does_not_parse(model: bk.Model) -> None:
    state = web.parse_state(
        model,
        {
            'b': 'nope',
            's': '1999-01',
            'q_rice': '-3',
            'q_fish': 'lots',
            'q_salt': 'inf',
            'q_soybeans': '40',
            'x_rice': 'two',
            'x_cloth': '1',
            'c1': 'only|three|parts',
            'c2': ' |kg|1|1|1',
            'c3': 'Tea|kg|x|0.5|',
        },
    )
    assert state.basket == 'standard'
    assert state.snapshot == model.snapshots[-1].date
    assert state.quantities == {'soybeans': 40.0}
    assert state.choices == {'cloth': 1}
    assert state.custom[:2] == (None, None)
    assert state.custom[2] == bk.Custom('Tea', 'kg', 0.0, 0.5, None)


def test_rows_list_every_good_and_bring_new_ones_in_at_the_standard_quantity(
    model: bk.Model,
) -> None:
    state = web.parse_state(model, {'b': 'bassino-ma-a', 's': '2017-04'})
    rows = {r.good.id: r for r in web.rows(model, state)}
    assert set(rows) == set(model.goods)
    assert rows['housing'].quantity == 0
    assert rows['housing'].default == 3.31  # switched on, it comes in at the standard quantity
    assert rows['housing'].options == ()
    assert rows['rice'].quantity == 114


def test_page_json_cannot_close_its_script_block(model: bk.Model) -> None:
    text = web.page_json(model, KG, load_wages()[-1])
    assert '</' not in text


def test_drivers_name_what_moves_the_koku(model: bk.Model) -> None:
    """Design review: housing's weight today was visible only in a faint column."""
    std = web.state_reading(model, web.parse_state(model, {}), KG)
    assert web.drivers(std).startswith("Largest share of today's cost: Housing (")
    assert 'Largest share of the 1740s cost: Rice (' in web.drivers(std)
    rice_only = web.state_reading(
        model,
        web.parse_state(
            model, {'b': 'bassino-ma-a', **{f'q_{g}': '0' for g in model.goods if g != 'rice'}}
        ),
        KG,
    )
    assert web.drivers(rice_only) == (
        "Largest share of today's cost: Rice (100%). Largest share of the 1740s cost: Rice (100%)."
    )
    empty = web.state_reading(
        model,
        web.parse_state(
            model,
            {
                'q_rice': '0',
                'b': 'bassino-ma-a',
                's': '2017-04',
                **{f'q_{g}': '0' for g in model.goods},
            },
        ),
        KG,
    )
    assert web.drivers(empty) == 'Nothing in the basket is priced on both sides.'


def test_custom_status_says_whether_a_good_counts(model: bk.Model) -> None:
    state = web.parse_state(model, {'c1': 'Sake|liter|20|2|12', 'c3': 'Tea|kg|1||9'})
    status = web.custom_status(state, web.state_reading(model, state, KG))
    assert status[0].startswith('Counts for ')
    assert status[1] == ''
    assert status[2] == 'Not counted until all five are filled in.'


def test_page_shows_drivers_and_custom_status(root: Root) -> None:
    page = html.unescape(root.money('koku', c1='Sake|liter|20|2|12').decode())
    assert "Largest share of today's cost: Housing" in page
    assert 'Counts for ' in page
    assert 'left out: no price' in root.money('koku', s='2017-04').decode()


def test_a_half_filled_custom_good_is_not_called_unpriced(model: bk.Model) -> None:
    state = web.parse_state(model, {'s': '2017-04', 'c1': 'Tea|kg|1||9'})
    assert web.left_out(web.state_reading(model, state, KG)) == ('Salt', 'Fuel', 'Housing')

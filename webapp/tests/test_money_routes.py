"""Route tests for /money and /money/koku (feature 222), and the playground's link state."""

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
    assert data['rice_ref'] == model.rice_ref
    assert data['eras']['kyoto-1745']['goods']['rice']['ratio'] == 1
    assert data['eras']['kyoto-1745']['goods']['fish']['borrowed']
    assert data['eras']['tokyo-1882']['goods']['cloth']['excluded']
    suzhou = data['eras']['suzhou-1750']['goods']
    assert suzhou == {'rice': {'ratio': 1.0, 'borrowed': False, 'excluded': False}}


def test_a_link_reopens_its_variant(root: Root) -> None:
    """User Story 5 scenario 2: the server renders what the link says."""
    page = root.money(
        'koku', b='bassino-ma-a', q_fish='0', x_rice='9', c1='Sake|liter|20|2|12'
    ).decode()  # an old link's own good (c1) is ignored: the visitor's goods are gone
    assert '<option value="bassino-ma-a" selected>' in page
    fish = re.search(r'<input type="checkbox" class="koku-on" name="q_fish"[^>]*>', page)
    assert fish is not None
    assert 'checked' not in fish.group(0)
    assert 'name="x_rice" value="2" checked' in page  # an index past the end is the last option
    assert 'Sake' not in page
    assert 'koku-custom' not in page


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
        },
    )
    assert state.basket == 'standard'
    assert state.snapshot == model.snapshots[-1].date
    assert state.quantities == {'soybeans': 40.0}
    assert state.choices == {'cloth': 1}


def test_rows_list_every_good_and_bring_new_ones_in_at_the_standard_quantity(
    model: bk.Model,
) -> None:
    state = web.State('bassino-ma-a', '2017-04')
    rows = {r.good.id: r for r in web.rows(model, state, web.state_reading(model, state, KG))}
    assert set(rows) == set(model.goods)
    assert rows['housing'].quantity == 0
    assert rows['housing'].default == 3.31  # switched on, it comes in at the standard quantity
    assert rows['housing'].options == ()
    assert rows['rice'].quantity == 114
    assert rows['housing'].weight is None
    assert rows['housing'].alone is None
    assert sum(r.weight or 0 for r in rows.values()) == pytest.approx(1)
    assert [e.id for e in rows['fish'].eras] == [
        'beijing-1615',
        'beijing-1820',
        'canton-1835',
        'tokyo-1882',
    ]


def test_page_json_cannot_close_its_script_block(model: bk.Model) -> None:
    text = web.page_json(model, KG, load_wages()[-1])
    assert '</' not in text


def test_drivers_name_what_moves_the_koku(model: bk.Model) -> None:
    """Design review: housing's weight today was visible only in a faint column."""
    std = web.state_reading(model, web.parse_state(model, {}), KG)
    assert web.drivers(std).startswith('Pulls the average up most: Housing ($')
    assert 'Pulls it down most: Rice ($' in web.drivers(std)  # cheap alone, and 41% of the weight
    arith = web.state_reading(model, web.parse_state(model, {'m': 'arithmetic'}), KG)
    assert web.drivers(arith).startswith('Pulls the average up most: Housing ($')
    rice_only = web.state_reading(
        model,
        web.parse_state(
            model,
            {
                'b': 'bassino-ma-a',
                **{f'q_{g}': '0' for g in model.goods if g != 'rice'},
            },
        ),
        KG,
    )
    assert web.drivers(rice_only) == (
        f'Every good reads the same: Rice (${KG * 1.26:,.0f} alone, 100% of the weight).'
    )
    empty = web.state_reading(
        model,
        web.parse_state(model, {'b': 'bassino-ma-a', **{f'q_{g}': '0' for g in model.goods}}),
        KG,
    )
    assert web.drivers(empty) == 'Nothing in the basket is priced on both sides.'


def test_page_shows_drivers(root: Root) -> None:
    page = html.unescape(root.money('koku').decode())
    assert 'Pulls the average up most: Housing' in page


def test_the_page_prices_at_the_newest_date_only(root: Root, model: bk.Model) -> None:
    """GM 2026-10-24: the 2017 prices are not shown, and an old link's `s=` is ignored."""
    page = root.money('koku', s='2017-04').decode()
    assert 'data-in="snapshot"' not in page
    assert '2017-04' not in page
    assert web.parse_state(model, {'s': '2017-04'}).snapshot == model.snapshots[-1].date


def test_the_checklist_replaces_the_quantity_boxes(root: Root, model: bk.Model) -> None:
    """GM 2026-10-24: goods are ticked on and off (no quantity to type); each opens for prices."""
    page = root.money('koku').decode()
    assert 'type="number" name="q_' not in page
    assert page.count('<details class="koku-detail">') == len(model.goods)
    assert 'name="q_rice" value="0"' in page  # the hidden 0 an unticked box falls back to
    assert '<input type="checkbox" class="koku-on" name="q_rice" value="114"' in page


def test_a_ticked_good_reads_the_checkboxs_value(model: bk.Model) -> None:
    """Without JavaScript the form sends `q_rice=0&q_rice=114` for a ticked good: the last wins."""
    assert web.parse_state(model, {'q_rice': ['0', '114']}).quantities == {'rice': 114.0}
    assert web.parse_state(model, {'q_housing': ['0']}).quantities == {'housing': 0.0}


def test_goods_the_old_snapshot_cannot_price_are_named(model: bk.Model) -> None:
    state = web.State(bk.STANDARD, '2017-04')
    reading = web.state_reading(model, state, KG)
    assert web.left_out(reading) == ('Miso', 'Soy sauce', 'Salt', 'Fuel', 'Housing')


# --- feature 223: two readings, the mean, era weights ---------------------------------------------


def _whole(page: str) -> str:
    return re.search(r'data-out="whole">([^<]+)<', page).group(1)  # type: ignore[union-attr]


def test_toggles_move_the_average_not_the_whole_basket(root: Root, model: bk.Model) -> None:
    """US2 acceptance 3: a good switched off or added changes only the average over goods."""
    full = root.money('koku').decode()
    off = root.money('koku', q_housing='0').decode()
    whole = web.whole_reading(model, web.parse_state(model, {}), KG)
    assert _whole(full) == _whole(off) == f'${whole.arithmetic:,.0f}'
    assert f'cost {whole.koku_cost:.2f} koku then, ${whole.dollars:,.0f} now' in full
    per = re.compile(r'data-out="per-koku" aria-live="polite">([^<]+)<')
    assert per.search(full).group(1) != per.search(off).group(1)  # type: ignore[union-attr]
    # a substitute price moves both (US2 acceptance 4)
    assert _whole(root.money('koku', x_rice='1').decode()) != _whole(full)


def test_the_link_carries_the_mean_weighting_and_era_weights(root: Root, model: bk.Model) -> None:
    state = web.parse_state(
        model,
        {
            'm': 'arithmetic',
            'eq': '1',
            'w_kyoto-1745': '2',
            'w_nope': '3',
            'wb': 'bassino-ma-a',
        },
    )
    assert (state.mean, state.equal, dict(state.weights)) == (
        'arithmetic',
        True,
        {'kyoto-1745': 2.0},
    )
    assert state.whole == bk.STANDARD  # not a complete basket
    assert web.parse_state(model, {'m': 'median'}).mean == 'geometric'
    page = root.money('koku', m='arithmetic', eq='1', **{'w_osaka-1700': '0'}).decode()
    assert 'name="m" value="arithmetic" data-in="mean" checked' in page
    assert 'name="eq" value="1" data-in="equal" checked' in page
    assert 'name="w_osaka-1700" value="0"' in page
    assert '(equal weights, arithmetic mean)' in page


def test_the_page_names_every_goods_figure(root: Root) -> None:
    """US3: no goods-dollar figure without its reading's name; the eras and the chart are there."""
    page = html.unescape(root.money('koku').decode())
    assert 'Averaged over goods' in page
    assert 'A year of necessities <span class="koku-range__tag">high</span>' in page
    assert '(geometric mean)' in page
    assert 'Which periods set Rokugan' in page
    assert 'rice alone, so it adds nothing' in page
    assert '; borrowed, counted only if no other period is: ' in page
    assert page.count('class="koku-track__dot"') == 14  # the standard basket's fourteen goods
    assert web.axis_pct(10) == 0
    assert web.axis_pct(10_000) == 100
    assert web.axis_pct(1e6) == 100  # clamped
    assert web.axis_pct(1_000) == pytest.approx(66.67)


def test_each_good_cites_the_periods_its_rokugani_price_rests_on(root: Root) -> None:
    """GM 2026-10-25: no single period or silver is the peg any more; each good lists the periods
    behind its price, with a link to the research each price comes from."""
    page = html.unescape(root.money('koku').decode())
    assert 'Rokugan: in silver' not in page
    shown = page.split('id="koku-data"')[0]
    assert 'github.com/EliAndrewC/diagram' not in shown  # research opens in the toolkit
    assert "at Kyoto 1745-54's price" not in page
    assert 'Add goods of your own' not in page
    assert 'diagram#17' not in page
    assert 'Rice is the measure: a koku is' in page
    fish = page[page.index('data-good="fish"') :]
    fish = fish[: fish.index('</ol>')]
    assert 'Canton 1830-1839</span>: ' in fish
    assert 'research: What did a year' in fish  # 0288's title, from the record
    china = 'what-did-a-years-necessities-and-a-days-labor-cost-in-china-era-by-era'
    assert f'href="/research/q/{china}.html"' in fish
    assert 'early Meiji period, after 1868, so it repeats another period' in fish
    assert 'Bassino & Ma, Table 3' in fish  # Kyoto 1745's fish, a borrowed price: listed, hidden
    assert re.search(r'<li data-era="kyoto-1745" hidden>', fish)
    assert 'data-era="tokyo-1882">' in fish  # counted, so shown
    cloth = page[page.index('data-good="cloth"') :]
    assert 'data-era="tokyo-1882"' not in cloth[: cloth.index('</ol>')]  # excluded: never listed


def test_rokugani_prices_read_in_sen(model: bk.Model) -> None:
    assert web.sen(model.rice_ref * KG, model, KG) == pytest.approx(1000)  # a koku of rice
    assert [web.sig3(x) for x in (6.6004, 0.041234, 1234.5, 100.2, 99.94)] == [
        '6.6',
        '0.0412',
        '1,230',
        '100',
        '99.9',
    ]
    assert web.source_label('https://example.com/x.pdf') == 'source'

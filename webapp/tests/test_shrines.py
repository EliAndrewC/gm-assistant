"""Logic tests for the shrine builder (feature 216): catalog, design, pricing, negotiation."""

from __future__ import annotations

import copy
import re
from typing import Any

import pytest
import yaml

from l7r.shrines import (
    CATALOG_PATH,
    DEFAULT_BASELINE,
    Catalog,
    CatalogError,
    Negotiation,
    default_budget,
    format_koku,
    format_number,
    gm_query,
    load_catalog,
    negotiate,
    parse_catalog,
    parse_design,
    parse_negotiation,
    price_design,
    reference_design,
    saving_percent,
    share_query,
    voided_by,
)


@pytest.fixture(scope='module')
def raw() -> dict[str, Any]:
    with CATALOG_PATH.open(encoding='utf-8') as fh:
        data: dict[str, Any] = yaml.safe_load(fh)
    return data


@pytest.fixture(scope='module')
def catalog() -> Catalog:
    return load_catalog()


# --- catalog content (FR-002, FR-002a, FR-003, FR-004) -------------------------------------------

# FR-002's list, by key. A category the GM asked for cannot silently disappear from the catalog.
REQUIRED_CATEGORIES = {
    'form',
    'size',
    'hall',
    'roof',
    'timber',
    'finish',
    'carving',
    'gate_form',
    'gate_material',
    'guardians',
    'lanterns',
    'water',
    'box',
    'bell',
    'altar',
    'sacred',
    'enclosure',
    'path',
    'plaque',
    'rite',
}


def test_catalog_has_every_required_category(catalog: Catalog) -> None:
    assert {c.key for c in catalog.categories} >= REQUIRED_CATEGORIES


def test_most_categories_offer_real_choices(catalog: Catalog) -> None:
    """SC-004: two thirds of categories offer three or more forms, not a cheap/dear pair."""
    rich = [c for c in catalog.categories if len(c.options) >= 3]
    assert len(rich) * 3 >= len(catalog.categories) * 2


# Words that state or imply price (FR-004). Player-facing text is every label, prompt, intro and
# option text in the catalog.
PRICE_WORDS = re.compile(
    r'\b(cheap\w*|cost\w*|expensive|inexpensive|pric\w*|budget\w*|afford\w*|luxur\w*|lavish\w*|'
    r'extravagan\w*|economical|thrift\w*|frugal\w*|bargain\w*|premium|koku|zeni|ryo)\b'
    r'|\d+\s*(koku|bu|zeni|ryo)\b',
    re.IGNORECASE,
)


def price_words(text: str) -> list[str]:
    return [m.group(0) for m in PRICE_WORDS.finditer(text)]


def player_texts(catalog: Catalog) -> list[str]:
    texts: list[str] = []
    for group in catalog.groups:
        texts += [group.label, group.intro]
        for category in group.categories:
            texts += [category.label, category.prompt]
            for option in category.options:
                texts += [option.label, option.text, option.romaji]
    return texts


def test_price_word_guard_fires() -> None:
    """The guard below is only worth something if it catches the thing it guards against."""
    assert price_words('A cheap roof') == ['cheap']
    assert price_words('costs 12 koku') == ['costs', '12 koku']
    assert price_words('the budget allows it') == ['budget']
    assert price_words('A bronze mirror, newly cast') == []


def test_player_text_never_mentions_price(catalog: Catalog) -> None:
    offenders = {t: price_words(t) for t in player_texts(catalog) if price_words(t)}
    assert offenders == {}


def test_no_option_adds_living_quarters(catalog: Catalog) -> None:
    """FR-002a: an unstaffed shrine; no lodging, no office, no quarters offered."""
    words = re.compile(r'\b(lodging|quarters|residence|office|lives there|sleeps?)\b', re.I)
    for category in catalog.categories:
        for option in category.options:
            hit = words.search(option.text)
            assert hit is None or 'nobody lives there' in option.text, option.key


def test_size_stays_one_bay(catalog: Catalog) -> None:
    """FR-002a: a remote site holds only a one-bay sanctuary."""
    size = catalog.category('size')
    assert size is not None
    assert all(o.units <= 2 for o in size.options)


def test_real_catalog_loads_with_porterage(catalog: Catalog) -> None:
    assert 'porterage' in {c.key for c in catalog.contracts}
    assert catalog.category('nope') is None


# --- catalog validation ---------------------------------------------------------------------------


def _first_category(data: dict[str, Any]) -> dict[str, Any]:
    category: dict[str, Any] = data['groups'][0]['categories'][0]
    return category


def _first_option(data: dict[str, Any]) -> dict[str, Any]:
    option: dict[str, Any] = _first_category(data)['options'][0]
    return option


def _drop_porterage(data: dict[str, Any]) -> None:
    data['contracts'] = [c for c in data['contracts'] if c['key'] != 'porterage']


@pytest.mark.parametrize(
    ('mutate', 'message'),
    [
        (lambda d: d['groups'][0]['categories'].append(_first_category(d)), 'duplicate'),
        (lambda d: _first_category(d).update(key='gm_form'), 'collides'),
        (lambda d: _first_category(d).update(key='enshrined'), 'collides'),
        (_drop_porterage, 'porterage'),
        (lambda d: d['remoteness'].update(default='moon'), 'remoteness'),
        (lambda d: d['site_lines'][0].update(contract='bribes'), 'site line'),
        (lambda d: _first_category(d).update(default='pagoda'), 'not one of its options'),
        (lambda d: _first_option(d).update(voids=['nowhere']), 'voids unknown'),
        (lambda d: _first_option(d).update(voids=['form']), 'voids unknown'),
        (lambda d: _first_option(d)['lines'][0].update(contract='bribes'), 'unknown contract'),
        (lambda d: _first_option(d)['lines'][0].update(per='nowhere'), 'per unknown'),
    ],
)
def test_catalog_validation_rejects(raw: dict[str, Any], mutate: Any, message: str) -> None:
    data = copy.deepcopy(raw)
    mutate(data)
    with pytest.raises(CatalogError, match=message):
        parse_catalog(data)


# --- design ---------------------------------------------------------------------------------------


def test_empty_params_give_defaults(catalog: Catalog) -> None:
    design = parse_design(catalog, {})
    for category in catalog.categories:
        if category.key not in design.voided:
            assert design.choices[category.key] == category.default
    assert design.text == {}
    assert design.dropped == ()


def test_valid_choice_and_list_values(catalog: Catalog) -> None:
    design = parse_design(catalog, {'roof': 'copper', 'timber': ['keyaki', 'sugi'], 'bell': []})
    assert design.choices['roof'] == 'copper'
    assert design.choices['timber'] == 'keyaki'
    assert design.choices['bell'] == 'suzu'


def test_unknown_option_is_dropped_and_reported(catalog: Catalog) -> None:
    design = parse_design(catalog, {'roof': 'gold-leaf', 'lanterns': 'neon'})
    assert design.choices['roof'] == catalog.category('roof').default  # type: ignore[union-attr]
    assert design.dropped == ('roof', 'lanterns')


def test_dropped_category_that_is_moot_is_not_reported(catalog: Catalog) -> None:
    design = parse_design(catalog, {'form': 'himorogi', 'roof': 'gold-leaf'})
    assert design.dropped == ()


def test_voids(catalog: Catalog) -> None:
    design = parse_design(catalog, {'form': 'himorogi', 'gate_form': 'none'})
    assert design.voided == {
        'size',
        'timber',
        'roof',
        'finish',
        'carving',
        'sacred',
        'gate_material',
    }
    assert 'roof' not in design.choices
    assert voided_by(catalog, design)['roof'] == 'Form'
    assert voided_by(catalog, design)['gate_material'] == 'Gate'


def test_text_is_trimmed_capped_and_blank_dropped(catalog: Catalog) -> None:
    design = parse_design(
        catalog,
        {'enshrined': '  Shoda the hermit ', 'shrine_name': '   ', 'inscription': 'x' * 5000},
    )
    assert design.text['enshrined'] == 'Shoda the hermit'
    assert 'shrine_name' not in design.text
    assert len(design.text['inscription']) == 2000


def test_share_query_round_trips_and_carries_no_gm_figure(catalog: Catalog) -> None:
    from urllib.parse import parse_qsl

    params = {'form': 'kasuga', 'roof': 'copper', 'enshrined': 'Shoda & co', 'gm_budget': '99'}
    design = parse_design(catalog, params)
    query = share_query(catalog, design)
    assert 'gm_' not in query
    again = parse_design(catalog, dict(parse_qsl(query)))
    assert again == design


# --- pricing --------------------------------------------------------------------------------------


def test_reference_design_and_default_budget(catalog: Catalog) -> None:
    pricing = price_design(catalog, reference_design(catalog), catalog.default_remoteness)
    assert pricing.total == pytest.approx(120.7)
    assert pricing.heavy == pytest.approx(31)
    assert default_budget(catalog) == 145.0


def test_size_scales_the_sanctuary_lines(catalog: Catalog) -> None:
    small = price_design(catalog, parse_design(catalog, {'size': 'small'}), 'road')
    large = price_design(catalog, parse_design(catalog, {'size': 'generous'}), 'road')
    # nagare 16 + hinoki 8 per size step on carpentry; hinoki's 4 heavy loads scale too
    carpentry = large.by_contract['carpentry'] - small.by_contract['carpentry']
    assert carpentry == pytest.approx(24 * 0.8)
    assert large.heavy - small.heavy == pytest.approx(4 * 0.8)


def test_porterage_is_heavy_times_rate(catalog: Catalog) -> None:
    design = reference_design(catalog)
    road = price_design(catalog, design, 'road')
    deep = price_design(catalog, design, 'deep')
    assert road.by_contract['porterage'] == pytest.approx(road.heavy * 0.25)
    assert deep.by_contract['porterage'] == pytest.approx(deep.heavy * 1.0)
    # FR-010: remoteness changes porterage and nothing else
    assert {k: v for k, v in road.by_contract.items() if k != 'porterage'} == {
        k: v for k, v in deep.by_contract.items() if k != 'porterage'
    }


def test_gate_material_scales_with_gate_form(catalog: Catalog) -> None:
    one_gate = parse_design(catalog, {'gate_form': 'shinmei', 'gate_material': 'stone'})
    row_gate = parse_design(catalog, {'gate_form': 'row', 'gate_material': 'stone'})
    one = price_design(catalog, one_gate, 'road')
    row = price_design(catalog, row_gate, 'road')
    assert row.by_contract['stonework'] - one.by_contract['stonework'] == pytest.approx(12)


def test_per_category_that_is_moot_counts_as_one(raw: dict[str, Any]) -> None:
    """A line `per` a voided category is priced at units 1 (no real option hits this today)."""
    data = copy.deepcopy(raw)
    form = _first_category(data)
    hokora = next(o for o in form['options'] if o['key'] == 'hokora')
    hokora['lines'] = [{'contract': 'stonework', 'koku': 6, 'per': 'size'}]
    catalog = parse_catalog(data)
    design = parse_design(catalog, {'form': 'hokora', 'size': 'generous'})
    items = [i for i in price_design(catalog, design, 'road').items if i.category == 'Form']
    assert [i.koku for i in items] == [6]


# --- negotiation ----------------------------------------------------------------------------------


def test_parse_negotiation_defaults(catalog: Catalog) -> None:
    negotiation = parse_negotiation(catalog, {})
    assert negotiation == Negotiation(145.0, 'trail', {}, {})


@pytest.mark.parametrize(
    ('raw_budget', 'expected'),
    [
        ('80', 80.0),
        (' 99.5 ', 99.5),
        ('-4', 0.0),
        ('1e9', 100_000.0),
        ('lots', 145.0),
        ('inf', 145.0),
    ],
)
def test_parse_budget(catalog: Catalog, raw_budget: str, expected: float) -> None:
    assert parse_negotiation(catalog, {'gm_budget': raw_budget}).budget == expected


def test_parse_rolls_and_baselines(catalog: Catalog) -> None:
    negotiation = parse_negotiation(
        catalog,
        {
            'gm_remote': 'deep',
            'gm_roll_carpentry': '42',
            'gm_roll_roofing': 'high',
            'gm_roll_stonework': '999',
            'gm_base_stonework': '31',
            'gm_base_rites': '-3',
        },
    )
    assert negotiation.remoteness == 'deep'
    assert negotiation.rolls == {'carpentry': 42, 'stonework': 200}
    assert negotiation.baselines == {'stonework': 31, 'rites': 0}
    assert parse_negotiation(catalog, {'gm_remote': 'moon'}).remoteness == 'trail'


@pytest.mark.parametrize(
    ('roll', 'baseline', 'pct'),
    [(None, 25, 0), (20, 25, 0), (25, 25, 0), (43, 25, 18), (300, 25, 100)],
)
def test_saving_percent(roll: int | None, baseline: int, pct: int) -> None:
    assert saving_percent(roll, baseline) == pct


def test_negotiate_reference(catalog: Catalog) -> None:
    design = reference_design(catalog)
    negotiation = Negotiation(145.0, 'trail', {'carpentry': 45, 'stonework': 40}, {'stonework': 30})
    ledger = negotiate(catalog, design, negotiation)
    by_key = {c.key: c for c in ledger.contracts}
    assert by_key['carpentry'].saving_pct == 20
    assert by_key['carpentry'].paid == pytest.approx(by_key['carpentry'].fair * 0.8)
    assert by_key['stonework'].baseline == 30
    assert by_key['stonework'].saving_pct == 10
    assert by_key['roofing'].roll is None
    assert by_key['roofing'].baseline == DEFAULT_BASELINE
    assert ledger.fair_total == pytest.approx(120.7)
    assert ledger.remainder == pytest.approx(145.0 - ledger.paid_total)
    assert all(i.contract == 'carpentry' for i in by_key['carpentry'].items)


def test_negotiate_skips_empty_contracts_and_reports_shortfall(catalog: Catalog) -> None:
    design = parse_design(
        catalog,
        {
            'form': 'himorogi',
            'guardians': 'none',
            'lanterns': 'none',
            'bell': 'clap',
            'box': 'plain',
            'sacred': 'stone',
        },
    )
    ledger = negotiate(catalog, design, Negotiation(0.0, 'road'))
    assert 'metalwork' not in {c.key for c in ledger.contracts}
    assert ledger.remainder < 0


def test_gm_query_has_design_and_figures(catalog: Catalog) -> None:
    design = parse_design(catalog, {'roof': 'thatch'})
    negotiation = Negotiation(120.0, 'deep', {'roofing': 33}, {'roofing': 28})
    query = gm_query(catalog, design, negotiation)
    assert query.startswith(share_query(catalog, design))
    for part in ('gm_budget=120', 'gm_remote=deep', 'gm_roll_roofing=33', 'gm_base_roofing=28'):
        assert part in query
    assert 'gm_roll_carpentry' not in query


# --- display --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('value', 'text'),
    [
        (12.43, '12 koku 4 bu'),
        (0.3, '3 bu'),
        (0.0, '0 bu'),
        (5.0, '5 koku'),
        (-2.5, '-2 koku 5 bu'),
        (1234.0, '1,234 koku'),
    ],
)
def test_format_koku(value: float, text: str) -> None:
    assert format_koku(value) == text


def test_format_number() -> None:
    assert format_number(12.0) == '12'
    assert format_number(12.5) == '12.5'

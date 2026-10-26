"""Feature 228: every old link keeps working, "Something else" on every step, and its pricing."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

from l7r.shrines import (
    OTHER_CAP,
    Catalog,
    CatalogError,
    answered,
    gm_query,
    load_catalog,
    load_raw,
    negotiate,
    parse_catalog,
    parse_design,
    parse_negotiation,
    share_query,
    upgrade_params,
)
from l7r.shrines.catalog import _merge_looks

LINKS = Path(__file__).with_name('shrine_links.txt')


@pytest.fixture(scope='module')
def catalog() -> Catalog:
    return load_catalog()


@pytest.fixture(scope='module')
def raw() -> dict[str, Any]:
    return load_raw()


def frozen_links() -> list[str]:
    lines = LINKS.read_text(encoding='utf-8').splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith('#')]


# --- FR-001: old links ---------------------------------------------------------------------------


def test_the_frozen_list_starts_with_shizus_shrine() -> None:
    links = frozen_links()
    assert links, 'an empty list would pass every check below vacuously'
    assert 'kind=memorial&heart=bones' in links[0]
    assert 'Shoda' in links[0]


@pytest.mark.parametrize('link', frozen_links())
def test_every_frozen_link_still_opens_its_design(catalog: Catalog, link: str) -> None:
    """GM 2026-10-26, a standing rule for every future shrine-builder change: a link a player made
    must keep working. Each value in the link must survive into the design - nothing dropped,
    nothing quietly not in play. A renamed key belongs in data/legacy.yaml, which this test reads
    through (parse_design upgrades old keys)."""
    params = parse_qs(urlsplit(link).query)
    params = upgrade_params(catalog, params) or params  # type: ignore[assignment]
    design = parse_design(catalog, params)
    assert design.dropped == ()
    for key, values in params.items():
        if key == 'shrine_name':
            assert design.text['shrine_name'] == values[0]
        elif key.startswith('other_'):
            assert design.others[key.removeprefix('other_')].text == values[0]
        elif key.startswith('instead_'):
            assert design.others[key.removeprefix('instead_')].instead
        elif catalog.category(key).multi:  # type: ignore[union-attr]
            assert set(design.multi[key]) == set(values), key
        else:
            assert design.choices.get(key) == values[0], key


def test_shizus_shrine_resolves_exactly(catalog: Catalog) -> None:
    design = parse_design(catalog, parse_qs(urlsplit(frozen_links()[0]).query))
    assert design.multi == {'sharing': ('headmound', 'temple')}
    assert design.choices['guardians'] == 'foxes'
    assert design.choices['lanterns'] == 'none'
    assert len(design.choices) == 20
    assert design.others == {}


def test_legacy_table_rewrites_old_keys(raw: dict[str, Any]) -> None:
    data = copy.deepcopy(raw)
    data['legacy_steps'] = {'torii': 'gate_form'}
    data['legacy_options'] = {'guardians': {'kitsune': 'foxes'}, 'sharing': {'skull': 'headmound'}}
    catalog = parse_catalog(data)
    old = {
        'torii': 'myojin',
        'guardians': 'kitsune',
        'sharing': ['skull', 'temple'],
        'other_torii': 'gilded',
        'instead_torii': '1',
        'form': 'nagare',
    }
    new = upgrade_params(catalog, old)
    assert new == {
        'gate_form': 'myojin',
        'guardians': 'foxes',
        'sharing': ['headmound', 'temple'],
        'other_gate_form': 'gilded',
        'instead_gate_form': '1',
        'form': 'nagare',
    }
    assert upgrade_params(catalog, new) is None
    design = parse_design(catalog, old)
    assert design.choices['guardians'] == 'foxes'
    assert design.others['gate_form'].text == 'gilded'
    # an old and a new spelling of one multi-select step merge
    data['legacy_steps'] = {'division': 'sharing'}
    both = upgrade_params(parse_catalog(data), {'sharing': ['temple'], 'division': 'headmound'})
    assert both == {'sharing': ['temple', 'headmound']}


def test_no_legacy_table_means_no_rewrite(catalog: Catalog) -> None:
    assert upgrade_params(catalog, {'kind': 'memorial'}) is None


@pytest.mark.parametrize(
    ('steps', 'options', 'message'),
    [
        ({'old': 'nowhere'}, {}, 'legacy step'),
        ({'kind': 'form'}, {}, 'legacy step'),
        ({}, {'nowhere': {'a': 'b'}}, 'unknown step'),
        ({}, {'guardians': {'kitsune': 'nothing'}}, 'legacy option'),
        ({}, {'guardians': {'foxes': 'komainu'}}, 'legacy option'),
    ],
)
def test_legacy_table_is_validated(
    raw: dict[str, Any], steps: dict[str, str], options: dict[str, Any], message: str
) -> None:
    data = copy.deepcopy(raw)
    data['legacy_steps'] = steps
    data['legacy_options'] = options
    with pytest.raises(CatalogError, match=message):
        parse_catalog(data)


def test_reserved_prefixes(raw: dict[str, Any]) -> None:
    data = copy.deepcopy(raw)
    data['groups'][0]['categories'][0]['key'] = 'other_kind'
    with pytest.raises(CatalogError, match='reserved prefix'):
        parse_catalog(data)


def test_every_option_has_a_look(raw: dict[str, Any]) -> None:
    groups = copy.deepcopy(raw['groups'])
    looks = {
        c['key']: {o['key']: 'x' for o in c['options']} for g in groups for c in g['categories']
    }
    del looks['form']['nagare']
    with pytest.raises(CatalogError, match='form.nagare: no look'):
        _merge_looks(groups, looks)
    looks['form']['nagare'] = 'x'
    looks['form']['pagoda'] = 'x'
    with pytest.raises(CatalogError, match='unknown options'):
        _merge_looks(groups, looks)


# --- FR-003/FR-004: "Something else" ------------------------------------------------------------


def test_other_as_well_keeps_the_pick(catalog: Catalog) -> None:
    design = parse_design(catalog, {'bell': 'suzu', 'other_bell': '  a   conch  '})
    assert design.choices['bell'] == 'suzu'
    assert design.others['bell'].text == 'a conch'
    assert not design.others['bell'].instead
    assert answered(design, 'bell')


def test_other_instead_sets_the_cards_aside(catalog: Catalog) -> None:
    design = parse_design(
        catalog,
        {'bell': 'suzu', 'other_bell': 'a conch', 'instead_bell': '1', 'sharing': 'temple'},
    )
    assert 'bell' not in design.choices
    assert design.others['bell'].instead
    assert answered(design, 'bell')
    assert not answered(design, 'roof')


def test_instead_on_a_step_others_depend_on(catalog: Catalog) -> None:
    """The one `when` grammar: "instead" on Kind is no listed kind, so the remains steps go."""
    design = parse_design(
        catalog,
        {'kind': 'memorial', 'other_kind': 'a shrine to a river dragon', 'instead_kind': 'on'},
    )
    assert 'heart' in design.inactive
    assert design.wording == ''


def test_instead_with_a_bad_pick_reports_nothing_dropped(catalog: Catalog) -> None:
    design = parse_design(catalog, {'bell': 'trumpet', 'other_bell': 'x', 'instead_bell': 'true'})
    assert design.dropped == ()


def test_instead_on_a_multi_select_step(catalog: Catalog) -> None:
    design = parse_design(
        catalog,
        {
            'kind': 'memorial',
            'sharing': ['temple', 'headmound'],
            'other_sharing': 'x',
            'instead_sharing': '1',
        },
    )
    assert 'sharing' not in design.multi
    assert answered(design, 'sharing')


def test_other_text_is_capped_and_blank_is_ignored(catalog: Catalog) -> None:
    design = parse_design(
        catalog, {'other_bell': 'a' * 999, 'other_roof': '   ', 'instead_roof': '1'}
    )
    assert len(design.others['bell'].text) == OTHER_CAP
    assert 'roof' not in design.others


def test_other_on_a_step_not_in_play_is_dropped(catalog: Catalog) -> None:
    design = parse_design(catalog, {'form': 'himorogi', 'other_roof': 'gold'})
    assert 'roof' in design.inactive
    assert design.others == {}


def test_other_round_trips_through_the_share_link(catalog: Catalog) -> None:
    params = {'bell': 'suzu', 'other_bell': 'a conch', 'other_roof': 'turf', 'instead_roof': '1'}
    design = parse_design(catalog, params)
    query = share_query(catalog, design)
    assert 'other_bell=a+conch' in query
    assert 'instead_roof=1' in query
    assert 'instead_bell' not in query
    again = parse_design(catalog, {k: v[0] for k, v in parse_qs(query).items()})
    assert again.others == design.others


# --- FR-005: pricing ------------------------------------------------------------------------------


def test_other_is_an_unpriced_line_until_the_gm_prices_it(catalog: Catalog) -> None:
    params: dict[str, Any] = {'bell': 'suzu', 'other_bell': 'a conch'}
    design = parse_design(catalog, params)
    ledger = negotiate(catalog, design, parse_negotiation(catalog, params))
    other = next(c for c in ledger.contracts if c.key == 'other')
    assert other.fair == 0
    assert ledger.pricing.unpriced == 1
    (item,) = other.items
    assert (item.step, item.priced, item.option) == ('bell', False, 'plus a conch')

    params['gm_other_bell'] = '2.5'
    priced = negotiate(catalog, design, parse_negotiation(catalog, params))
    assert priced.pricing.unpriced == 0
    assert priced.fair_total == pytest.approx(ledger.fair_total + 2.5)
    assert 'gm_other_bell=2.5' in gm_query(catalog, design, parse_negotiation(catalog, params))


def test_instead_removes_the_replaced_options_price(catalog: Catalog) -> None:
    base = {'bell': 'gong'}
    plain = negotiate(catalog, parse_design(catalog, base), parse_negotiation(catalog, base))
    swap = {**base, 'other_bell': 'a conch', 'instead_bell': '1', 'gm_other_bell': '0'}
    design = parse_design(catalog, swap)
    swapped = negotiate(catalog, design, parse_negotiation(catalog, swap))
    assert swapped.fair_total < plain.fair_total
    assert any(i.option == 'instead, a conch' for i in swapped.pricing.items)


def test_gm_other_price_is_parsed_like_a_budget(catalog: Catalog) -> None:
    n = parse_negotiation(
        catalog, {'gm_other_bell': '-4', 'gm_other_roof': 'lots', 'gm_other_path': 'nan'}
    )
    assert n.others == {'bell': 0.0}


def test_no_other_means_no_other_contract(catalog: Catalog) -> None:
    params = {'bell': 'suzu', 'gm_other_bell': '3'}
    design = parse_design(catalog, params)
    negotiation = parse_negotiation(catalog, params)
    assert all(c.key != 'other' for c in negotiate(catalog, design, negotiation).contracts)
    assert 'gm_other' not in gm_query(catalog, design, negotiation)

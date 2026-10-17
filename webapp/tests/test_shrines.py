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
        texts += [group.label, group.intro, *group.alt.values()]
        for category in group.categories:
            texts += [category.label, category.prompt, *category.alt.values()]
            for option in category.options:
                texts += [option.label, option.text, option.romaji, option.appeal]
                texts += list(option.alt.values())
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


def test_no_lesser_greater_pairs(catalog: Catalog) -> None:
    """FR-019: no size category, and no option label is another option's label plus more
    ("Vermilion" beside "Black lacquer with vermilion")."""
    assert catalog.category('size') is None
    for category in catalog.categories:
        labels = [o.label.lower() for o in category.options]
        for a in labels:
            for b in labels:
                assert a == b or a not in b, (category.key, a, b)


MEMORIAL_STEPS = {'heart', 'preparation', 'head', 'sharing', 'resting', 'display'}

ABSENCE = re.compile(r'^(none|nothing|no)\b', re.IGNORECASE)
YES_NO_PROMPT = re.compile(r'^(is|are|do|does|can|will) ', re.IGNORECASE)
DEFAULT_FRAMING = re.compile(r'\b(the usual|standard|ordinary|typical)\b', re.IGNORECASE)


def test_absence_and_default_guards_fire() -> None:
    assert ABSENCE.search('None')
    assert ABSENCE.search('No gate')
    assert not ABSENCE.search('Nonesuch lantern')
    assert YES_NO_PROMPT.search('Are there lanterns?')
    assert DEFAULT_FRAMING.search('The usual measure of decoration.')
    assert not DEFAULT_FRAMING.search('One of the most common types of decoration.')


def test_no_option_is_an_absence(catalog: Catalog) -> None:
    """FR-020: every option is a positive form; prompts ask what or how."""
    for category in catalog.categories:
        assert not YES_NO_PROMPT.search(category.prompt), category.key
        for option in category.options:
            assert not ABSENCE.search(option.label), option.label
            assert not ABSENCE.search(option.text), option.text
            assert not ABSENCE.search(option.appeal), option.appeal


def test_nothing_frames_itself_as_the_default(catalog: Catalog) -> None:
    """FR-021: "one of the most common", never "the usual" or "the standard"."""
    offenders = [t for t in player_texts(catalog) if DEFAULT_FRAMING.search(t)]
    assert offenders == []


def test_real_catalog_loads_with_porterage(catalog: Catalog) -> None:
    assert 'porterage' in {c.key for c in catalog.contracts}
    assert catalog.category('nope') is None


# --- catalog validation ---------------------------------------------------------------------------


def _category_raw(data: dict[str, Any], key: str) -> dict[str, Any]:
    for group in data['groups']:
        for category in group['categories']:
            if category['key'] == key:
                found: dict[str, Any] = category
                return found
    raise KeyError(key)


def _first_category(data: dict[str, Any]) -> dict[str, Any]:
    """The `form` category (the tests mutate it; it has lines, voids and many options)."""
    return _category_raw(data, 'form')


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
        (lambda d: _first_category(d).update(key='shrine_name'), 'collides'),
        (_drop_porterage, 'porterage'),
        (lambda d: d['remoteness'].update(default='moon'), 'remoteness'),
        (lambda d: d['site_lines'][0].update(contract='bribes'), 'site line'),
        (lambda d: _first_category(d).update(reference='pagoda'), 'not one of its options'),
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


def test_empty_params_choose_nothing(catalog: Catalog) -> None:
    """Nothing is pre-selected: an option already picked on arrival biases the player."""
    design = parse_design(catalog, {})
    assert design.choices == {}
    # only_with steps wait for the choice they depend on: the open-sky steps for the form, the
    # remains steps for the kind of shrine.
    assert design.voided == {'dwelling', 'ground', *MEMORIAL_STEPS}
    assert price_design(catalog, design, 'road').total == pytest.approx(3.5)  # site work only
    assert design.text == {'shrine_name': catalog.default_name}
    assert design.dropped == ()


def test_valid_choice_and_list_values(catalog: Catalog) -> None:
    design = parse_design(catalog, {'roof': 'copper', 'timber': ['keyaki', 'sugi'], 'bell': []})
    assert design.choices['roof'] == 'copper'
    assert design.choices['timber'] == 'keyaki'
    assert 'bell' not in design.choices


def test_unknown_option_is_dropped_and_reported(catalog: Catalog) -> None:
    design = parse_design(catalog, {'roof': 'gold-leaf', 'lanterns': 'neon'})
    assert 'roof' not in design.choices
    assert design.dropped == ('roof', 'lanterns')


def test_dropped_category_that_is_moot_is_not_reported(catalog: Catalog) -> None:
    design = parse_design(catalog, {'form': 'himorogi', 'roof': 'gold-leaf'})
    assert design.dropped == ()


def test_voids(catalog: Catalog) -> None:
    design = parse_design(catalog, {'kind': 'kami', 'form': 'himorogi', 'gate_form': 'trees'})
    assert design.voided - MEMORIAL_STEPS == {
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


def test_shrine_name_is_trimmed_capped_and_defaulted(catalog: Catalog) -> None:
    assert parse_design(catalog, {'shrine_name': '  Fox Hill  '}).text == {
        'shrine_name': 'Fox Hill'
    }
    assert len(parse_design(catalog, {'shrine_name': 'x' * 500}).text['shrine_name']) == 120
    blank = parse_design(catalog, {'shrine_name': '   '})
    assert blank.text['shrine_name'] == catalog.default_name
    assert catalog.default_name == 'The memorial hermitage of Shoda the Fox-forest Guardian'


def test_only_free_text_field_is_the_name() -> None:
    """FR-017: no field prompts the player to write something beyond the shrine's name."""
    from l7r.shrines import TEXT_FIELDS

    assert set(TEXT_FIELDS) == {'shrine_name'}


def test_share_query_round_trips_and_carries_no_gm_figure(catalog: Catalog) -> None:
    from urllib.parse import parse_qsl

    params = {'form': 'kasuga', 'roof': 'copper', 'shrine_name': 'Shoda & co', 'gm_budget': '99'}
    design = parse_design(catalog, params)
    query = share_query(catalog, design)
    assert 'gm_' not in query
    again = parse_design(catalog, dict(parse_qsl(query)))
    assert again == design


# --- pricing --------------------------------------------------------------------------------------


def test_reference_design_and_default_budget(catalog: Catalog) -> None:
    pricing = price_design(catalog, reference_design(catalog), catalog.default_remoteness)
    assert pricing.total == pytest.approx(130.7)
    assert pricing.heavy == pytest.approx(36)
    assert default_budget(catalog) == 160.0


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
    hokora['lines'] = [{'contract': 'stonework', 'koku': 6, 'per': 'timber'}]
    timber = _category_raw(data, 'timber')
    timber['options'][2]['units'] = 3
    catalog = parse_catalog(data)
    design = parse_design(catalog, {'form': 'hokora', 'timber': timber['options'][2]['key']})
    items = [i for i in price_design(catalog, design, 'road').items if i.category == 'Form']
    assert [i.koku for i in items] == [6]


# --- negotiation ----------------------------------------------------------------------------------


def test_parse_negotiation_defaults(catalog: Catalog) -> None:
    negotiation = parse_negotiation(catalog, {})
    assert negotiation == Negotiation(160.0, 'trail', {}, {})


@pytest.mark.parametrize(
    ('raw_budget', 'expected'),
    [
        ('80', 80.0),
        (' 99.5 ', 99.5),
        ('-4', 0.0),
        ('1e9', 100_000.0),
        ('lots', 160.0),
        ('inf', 160.0),
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
    negotiation = Negotiation(160.0, 'trail', {'carpentry': 45, 'stonework': 40}, {'stonework': 30})
    ledger = negotiate(catalog, design, negotiation)
    by_key = {c.key: c for c in ledger.contracts}
    assert by_key['carpentry'].saving_pct == 20
    assert by_key['carpentry'].paid == pytest.approx(by_key['carpentry'].fair * 0.8)
    assert by_key['stonework'].baseline == 30
    assert by_key['stonework'].saving_pct == 10
    assert by_key['roofing'].roll is None
    assert by_key['roofing'].baseline == DEFAULT_BASELINE
    assert ledger.fair_total == pytest.approx(130.7)
    assert ledger.remainder == pytest.approx(160.0 - ledger.paid_total)
    assert all(i.contract == 'carpentry' for i in by_key['carpentry'].items)


def test_negotiate_skips_empty_contracts_and_reports_shortfall(catalog: Catalog) -> None:
    design = parse_design(
        catalog,
        {
            'form': 'himorogi',
            'guardians': 'none',
            'lanterns': 'none',
            'bell': 'clap',
            'box': 'bamboo',
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


def test_every_option_says_why_unless_it_is_common(catalog: Catalog) -> None:
    """FR-026: an appeal sentence on every option, except "one of the most common" ones."""
    for category in catalog.categories:
        for option in category.options:
            common = 'one of the most common' in option.text.lower()
            assert bool(option.appeal) != common, (category.key, option.key)
            if option.appeal:
                assert option.appeal.endswith('.'), option.key
                assert option.appeal.count('. ') == 0, ('one sentence', option.key)


def test_open_sky_form_has_decisions_of_its_own(catalog: Catalog) -> None:
    """FR-025: dwelling and ground apply to the open-to-the-sky form and to no other."""
    for form in catalog.category('form').options:  # type: ignore[union-attr]
        design = parse_design(catalog, {'form': form.key, 'dwelling': 'rock', 'ground': 'moss'})
        if form.key == 'himorogi':
            assert design.choices['dwelling'] == 'rock'
            assert design.choices['ground'] == 'moss'
            assert 'sacred' in design.voided
        else:
            assert {'dwelling', 'ground'} <= design.voided
            assert voided_by(catalog, design)['dwelling'] == 'Form'
    open_sky = parse_design(catalog, {'form': 'himorogi', 'dwelling': 'standing'})
    lines = [
        i
        for i in price_design(catalog, open_sky, 'road').items
        if i.category == "The kami's dwelling"
    ]
    assert [i.koku for i in lines] == [3]


def _only_with_unknown_category(d: dict[str, Any]) -> None:
    _first_category(d)['only_with'] = {'nowhere': ['x']}


def _only_with_self(d: dict[str, Any]) -> None:
    _first_category(d)['only_with'] = {'form': ['nagare']}


def _only_with_unknown_option(d: dict[str, Any]) -> None:
    _category_raw(d, 'dwelling')['only_with'] = {'form': ['pagoda']}


@pytest.mark.parametrize(
    ('mutate', 'message'),
    [
        (_only_with_unknown_category, 'only_with names unknown category'),
        (_only_with_self, 'only_with names unknown category'),
        (_only_with_unknown_option, 'only_with names an unknown option'),
    ],
)
def test_only_with_validation(raw: dict[str, Any], mutate: Any, message: str) -> None:
    data = copy.deepcopy(raw)
    mutate(data)
    with pytest.raises(CatalogError, match=message):
        parse_catalog(data)


def test_memorial_brings_the_remains_steps(catalog: Catalog) -> None:
    """FR-028/FR-029: the remains steps appear for a memorial and never for a kami shrine."""
    kami = parse_design(catalog, {'kind': 'kami'})
    assert kami.voided >= MEMORIAL_STEPS
    memorial = parse_design(catalog, {'kind': 'memorial'})
    assert not (memorial.voided & MEMORIAL_STEPS)
    head = parse_design(catalog, {'kind': 'memorial', 'head': 'mound'})
    priced = price_design(catalog, head, 'road')
    assert (
        priced.by_contract['earthwork']
        > price_design(catalog, memorial, 'road').by_contract['earthwork']
    )


def test_remains_at_the_heart_means_no_kami(catalog: Catalog) -> None:
    """FR-030: no sacred object, no kami's dwelling, and the alternative wording."""
    bones = parse_design(catalog, {'kind': 'memorial', 'heart': 'bones', 'form': 'himorogi'})
    assert {'sacred', 'dwelling'} <= bones.voided
    assert 'ground' not in bones.voided  # the open-sky form keeps a decision of its own
    assert bones.alt is True
    spirit = parse_design(catalog, {'kind': 'memorial', 'heart': 'spirit'})
    assert spirit.alt is False
    rite = catalog.category('rite')
    assert rite is not None
    assert rite.alt['prompt'] == 'How is the shrine consecrated?'
    no_kami = [t for t in player_texts(catalog) if t and 'kami' in t]
    alt_texts = [
        v
        for g in catalog.groups
        for v in [*g.alt.values(), *(x for c in g.categories for x in c.alt.values())]
    ]
    assert all('kami' not in v for v in alt_texts), no_kami


def test_no_boiled_bones(catalog: Catalog) -> None:
    """FR-031: the European boiling practice has no East Asian record and is not offered."""
    texts = ' '.join(player_texts(catalog)).lower()
    assert 'boil' not in texts
    assert 'vinegar' not in texts


def _bad_alt_field(d: dict[str, Any]) -> None:
    _first_category(d)['alt'] = {'reference': 'x'}


def _bad_alt_when(d: dict[str, Any]) -> None:
    d['alt_when'] = {'heart': ['ghost']}


@pytest.mark.parametrize(
    ('mutate', 'message'),
    [(_bad_alt_field, 'alt may only replace'), (_bad_alt_when, 'alt_when names')],
)
def test_alt_validation(raw: dict[str, Any], mutate: Any, message: str) -> None:
    data = copy.deepcopy(raw)
    mutate(data)
    with pytest.raises(CatalogError, match=message):
        parse_catalog(data)

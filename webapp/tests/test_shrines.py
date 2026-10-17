"""Logic tests for the shrine builder (feature 216): catalog, rules, design, prices, haggling."""

from __future__ import annotations

import copy
import json
import re
from typing import Any
from urllib.parse import parse_qsl

import pytest

from l7r.shrines import (
    DEFAULT_BASELINE,
    TEXT_FIELDS,
    Catalog,
    CatalogError,
    Clause,
    Negotiation,
    default_budget,
    enables,
    format_koku,
    format_number,
    gm_query,
    load_catalog,
    load_raw,
    moot_note,
    negotiate,
    option_offered,
    parse_catalog,
    parse_design,
    parse_negotiation,
    price_design,
    reference_design,
    rules_json,
    saving_percent,
    share_query,
)


@pytest.fixture(scope='module')
def raw() -> dict[str, Any]:
    return load_raw()


@pytest.fixture(scope='module')
def catalog() -> Catalog:
    return load_catalog()


def _category_raw(data: dict[str, Any], key: str) -> dict[str, Any]:
    for group in data['groups']:
        for category in group['categories']:
            if category['key'] == key:
                found: dict[str, Any] = category
                return found
    raise KeyError(key)


def _option_raw(data: dict[str, Any], category: str, option: str) -> dict[str, Any]:
    found: dict[str, Any] = next(
        o for o in _category_raw(data, category)['options'] if o['key'] == option
    )
    return found


MEMORIAL_STEPS = {'heart', 'preparation', 'sharing', 'resting', 'display'}
REFERENCE_TOTAL = 135.2
SUGGESTED_BUDGET = 165.0


# --- catalog content (FR-002, FR-002a, FR-003, FR-004, FR-017 to FR-036) -------------------------

# FR-002's list plus the later amendments, by key. A step the GM asked for cannot silently vanish.
REQUIRED_CATEGORIES = {
    'kind', 'form', 'hall', 'roof', 'timber', 'finish', 'carving', 'gate_form', 'gate_material',
    'guardians', 'lanterns', 'water', 'box', 'bell', 'altar', 'sacred', 'enclosure', 'path',
    'plaque', 'rite', 'dwelling', 'ground', *MEMORIAL_STEPS,
}  # fmt: skip


def test_catalog_has_every_required_category(catalog: Catalog) -> None:
    assert {c.key for c in catalog.categories} >= REQUIRED_CATEGORIES


def test_no_separate_head_or_size_step(catalog: Catalog) -> None:
    """FR-019 (no size) and FR-034 (the head is part of dividing the remains)."""
    assert catalog.category('size') is None
    assert catalog.category('head') is None


def test_most_categories_offer_real_choices(catalog: Catalog) -> None:
    """SC-004: two thirds of categories offer three or more forms, not a cheap/dear pair."""
    rich = [c for c in catalog.categories if len(c.options) >= 3]
    assert len(rich) * 3 >= len(catalog.categories) * 2


# Words that state or imply price (FR-004).
PRICE_WORDS = re.compile(
    r'\b(cheap\w*|cost\w*|expensive|inexpensive|pric\w*|budget\w*|afford\w*|luxur\w*|lavish\w*|'
    r'extravagan\w*|economical|thrift\w*|frugal\w*|bargain\w*|premium|koku|zeni|ryo)\b'
    r'|\d+\s*(koku|bu|zeni|ryo)\b',
    re.IGNORECASE,
)
ABSENCE = re.compile(r'^(none|nothing|no)\b', re.IGNORECASE)
YES_NO_PROMPT = re.compile(r'^(is|are|do|does|can|will) ', re.IGNORECASE)
DEFAULT_FRAMING = re.compile(r'\b(the usual|standard|ordinary|typical)\b', re.IGNORECASE)


def price_words(text: str) -> list[str]:
    return [m.group(0) for m in PRICE_WORDS.finditer(text)]


def player_texts(catalog: Catalog) -> list[str]:
    texts: list[str] = []
    for group in catalog.groups:
        texts += [group.label, group.intro, *group.alt.values()]
        for category in group.categories:
            texts += [category.label, category.prompt, category.decides, *category.alt.values()]
            for option in category.options:
                texts += [option.label, option.text, option.romaji, option.appeal]
                texts += list(option.alt.values())
    return [t for t in texts if t]


def test_guards_fire() -> None:
    """Each guard below is only worth something if it catches the thing it guards against."""
    assert price_words('A cheap roof') == ['cheap']
    assert price_words('costs 12 koku') == ['costs', '12 koku']
    assert price_words('A bronze mirror, newly cast') == []
    assert ABSENCE.search('None')
    assert ABSENCE.search('No gate')
    assert not ABSENCE.search('Nonesuch lantern')
    assert YES_NO_PROMPT.search('Are there lanterns?')
    assert DEFAULT_FRAMING.search('The usual measure of decoration.')
    assert not DEFAULT_FRAMING.search('One of the most common types of decoration.')


def test_player_text_never_mentions_price(catalog: Catalog) -> None:
    offenders = {t: price_words(t) for t in player_texts(catalog) if price_words(t)}
    assert offenders == {}


def test_no_option_is_an_absence(catalog: Catalog) -> None:
    """FR-020: every option is a positive form; prompts ask what or how."""
    for category in catalog.categories:
        prompts = [category.prompt, *category.alt.values()]
        assert not any(YES_NO_PROMPT.search(p) for p in prompts), category.key
        for option in category.options:
            for text in (option.label, option.text, option.appeal, *option.alt.values()):
                assert not ABSENCE.search(text), text


def test_nothing_frames_itself_as_the_default(catalog: Catalog) -> None:
    """FR-021: "one of the most common", never "the usual" or "the standard"."""
    assert [t for t in player_texts(catalog) if DEFAULT_FRAMING.search(t)] == []


def test_no_lesser_greater_pairs(catalog: Catalog) -> None:
    """FR-019: no option label is another option's label plus more."""
    for category in catalog.categories:
        labels = [o.label.lower() for o in category.options]
        for a in labels:
            for b in labels:
                assert a == b or a not in b, (category.key, a, b)


def test_every_option_says_why_unless_it_is_common(catalog: Catalog) -> None:
    """FR-026: an appeal sentence on every option, except "one of the most common" ones."""
    for category in catalog.categories:
        for option in category.options:
            common = 'one of the most common' in option.text.lower()
            assert bool(option.appeal) != common, (category.key, option.key)
            if option.appeal:
                assert option.appeal.endswith('.'), option.key
                assert option.appeal.count('. ') == 0, ('one sentence', option.key)


def test_no_option_adds_living_quarters(catalog: Catalog) -> None:
    """FR-002a: an unstaffed shrine; no lodging, no office, no quarters offered."""
    words = re.compile(r'\b(lodging|quarters|residence|office|lives there|sleeps?)\b', re.I)
    for category in catalog.categories:
        for option in category.options:
            hit = words.search(option.text)
            assert hit is None or 'nobody lives there' in option.text, option.key


def test_memorial_options_stay_generic(catalog: Catalog) -> None:
    """FR-034: Shoda and the Temple of Ebisu appear only as an example, never as the option."""
    for key in MEMORIAL_STEPS:
        category = catalog.category(key)
        assert category is not None
        for option in category.options:
            assert 'Ebisu' not in option.label
            if 'Ebisu' in option.text:
                assert 'for Shoda' in option.text


def test_no_boiled_bones(catalog: Catalog) -> None:
    """FR-031: the European boiling practice has no East Asian record and is not offered."""
    texts = ' '.join(player_texts(catalog)).lower()
    assert 'boil' not in texts
    assert 'vinegar' not in texts


def test_only_free_text_field_is_the_name(catalog: Catalog) -> None:
    """FR-017/FR-022: one free-text field, pre-filled with the GM's name."""
    assert set(TEXT_FIELDS) == {'shrine_name'}
    assert catalog.default_name == 'The memorial hermitage of Shoda the Fox-forest Guardian'


# --- catalog validation ---------------------------------------------------------------------------


def _forward_rule(d: dict[str, Any]) -> None:
    _category_raw(d, 'kind')['when'] = {'form': ['nagare']}  # kind comes before form


def _self_rule(d: dict[str, Any]) -> None:
    _category_raw(d, 'form')['when'] = {'form': ['nagare']}


def _unknown_rule_option(d: dict[str, Any]) -> None:
    _category_raw(d, 'timber')['when'] = {'form': {'not': ['pagoda']}}


def _forward_option_rule(d: dict[str, Any]) -> None:
    _option_raw(d, 'display', 'reliquary')['when'] = {'rite': ['full']}


def _bad_alt_when(d: dict[str, Any]) -> None:
    d['alt_when'] = {'heart': ['ghost']}


def _bad_alt_field(d: dict[str, Any]) -> None:
    _category_raw(d, 'form')['alt'] = {'reference': 'x'}


def _forward_per(d: dict[str, Any]) -> None:
    line = {'contract': 'carpentry', 'koku': 1, 'per': 'rite'}
    _option_raw(d, 'form', 'nagare')['lines'] = [line]


def _drop_porterage(d: dict[str, Any]) -> None:
    d['contracts'] = [c for c in d['contracts'] if c['key'] != 'porterage']


def _duplicate(d: dict[str, Any]) -> None:
    d['groups'][0]['categories'].append(_category_raw(d, 'kind'))


def _bad_contract(d: dict[str, Any]) -> None:
    _option_raw(d, 'form', 'nagare')['lines'][0]['contract'] = 'bribes'


@pytest.mark.parametrize(
    ('mutate', 'message'),
    [
        (_duplicate, 'duplicate'),
        (lambda d: _category_raw(d, 'form').update(key='gm_form'), 'collides'),
        (lambda d: _category_raw(d, 'form').update(key='shrine_name'), 'collides'),
        (_drop_porterage, 'porterage'),
        (lambda d: d['remoteness'].update(default='moon'), 'remoteness'),
        (lambda d: d['site_lines'][0].update(contract='bribes'), 'site line'),
        (lambda d: _category_raw(d, 'form').update(reference='pagoda'), 'not one of its options'),
        (_forward_rule, 'not an earlier step'),
        (_self_rule, 'not an earlier step'),
        (_unknown_rule_option, 'unknown option'),
        (_forward_option_rule, 'not an earlier step'),
        (_bad_alt_when, 'unknown option'),
        (_bad_alt_field, 'alt may only replace'),
        (_forward_per, 'not an earlier step'),
        (_bad_contract, 'unknown contract'),
    ],
)
def test_catalog_validation_rejects(raw: dict[str, Any], mutate: Any, message: str) -> None:
    data = copy.deepcopy(raw)
    mutate(data)
    with pytest.raises(CatalogError, match=message):
        parse_catalog(data)


# --- rules and design -----------------------------------------------------------------------------


def test_clause_semantics() -> None:
    """An unchosen step is "no value": a plain clause fails, a negated one passes."""
    plain = Clause('form', frozenset({'himorogi'}))
    negated = Clause('form', frozenset({'himorogi'}), negate=True)
    assert not plain.holds({})
    assert negated.holds({})
    assert plain.holds({'form': 'himorogi'})
    assert not negated.holds({'form': 'himorogi'})


def test_empty_params_choose_nothing(catalog: Catalog) -> None:
    """Nothing is pre-selected; steps waiting on an unanswered step are not in play."""
    design = parse_design(catalog, {})
    assert design.choices == {}
    assert design.voided == {'dwelling', 'ground', *MEMORIAL_STEPS}
    assert design.text == {'shrine_name': catalog.default_name}
    assert price_design(catalog, design, 'road').total == pytest.approx(3.5)  # site work only


def test_valid_choice_and_list_values(catalog: Catalog) -> None:
    design = parse_design(catalog, {'roof': 'copper', 'timber': ['keyaki', 'sugi'], 'bell': []})
    assert design.choices == {'roof': 'copper', 'timber': 'keyaki'}


def test_unknown_option_is_dropped_and_reported(catalog: Catalog) -> None:
    design = parse_design(catalog, {'roof': 'gold-leaf', 'lanterns': 'neon'})
    assert 'roof' not in design.choices
    assert design.dropped == ('roof', 'lanterns')


def test_dropped_step_that_is_not_in_play_is_not_reported(catalog: Catalog) -> None:
    design = parse_design(catalog, {'form': 'himorogi', 'roof': 'gold-leaf'})
    assert design.dropped == ()


def test_form_rules(catalog: Catalog) -> None:
    open_sky = parse_design(catalog, {'kind': 'kami', 'form': 'himorogi', 'gate_form': 'trees'})
    assert open_sky.voided == {
        'timber', 'roof', 'finish', 'carving', 'sacred', 'gate_material', *MEMORIAL_STEPS,
    }  # fmt: skip
    assert open_sky.inactive['roof'] == Clause(
        'form', frozenset({'hokora', 'himorogi'}), negate=True
    )
    hokora = parse_design(catalog, {'form': 'hokora'})
    assert {'timber', 'roof'} <= hokora.voided
    assert 'sacred' not in hokora.voided


def test_memorial_brings_the_remains_steps(catalog: Catalog) -> None:
    """FR-028/FR-029: the remains steps appear for a memorial and never for a kami shrine."""
    assert parse_design(catalog, {'kind': 'kami'}).voided >= MEMORIAL_STEPS
    assert not (parse_design(catalog, {'kind': 'memorial'}).voided & MEMORIAL_STEPS)


def test_heart_options_bundle_registration(catalog: Catalog) -> None:
    """FR-032/FR-033: honored as an ancestor, registered or not, or the remains themselves."""
    heart = catalog.category('heart')
    assert heart is not None
    assert {o.key for o in heart.options} == {'registered', 'disciples', 'bones'}
    registered = parse_design(catalog, {'kind': 'memorial', 'heart': 'registered'})
    disciples = parse_design(catalog, {'kind': 'memorial', 'heart': 'disciples'})
    assert (
        price_design(catalog, registered, 'road').by_contract['rites']
        > (price_design(catalog, disciples, 'road').by_contract['rites'])
    )
    assert all('kami' not in o.label for o in heart.options)


def test_remains_at_the_heart_means_no_kami(catalog: Catalog) -> None:
    """FR-030: no sacred object, no spirit's dwelling; the open-sky form keeps its ground step."""
    bones = parse_design(catalog, {'kind': 'memorial', 'heart': 'bones', 'form': 'himorogi'})
    assert {'sacred', 'dwelling'} <= bones.voided
    assert 'ground' not in bones.voided
    spirit = parse_design(catalog, {'kind': 'memorial', 'heart': 'disciples', 'form': 'himorogi'})
    assert 'dwelling' not in spirit.voided


def test_memorial_wording_replaces_kami_wording(catalog: Catalog) -> None:
    """FR-030/FR-032: for any memorial the dead are honored ancestors, so `alt` wording applies."""
    assert parse_design(catalog, {'kind': 'memorial'}).alt is True
    assert parse_design(catalog, {'kind': 'kami'}).alt is False
    alt_texts = [
        v
        for g in catalog.groups
        for v in [
            *g.alt.values(),
            *(x for c in g.categories for x in c.alt.values()),
            *(x for c in g.categories for o in c.options for x in o.alt.values()),
        ]
    ]
    assert alt_texts
    assert [v for v in alt_texts if 'kami' in v] == []
    # every kami mention in a step a memorial can reach has an alt replacement
    for category in catalog.categories:
        if category.key not in {'kind', *MEMORIAL_STEPS} and 'kami' in category.prompt:
            assert 'prompt' in category.alt, category.key


def test_reliquary_needs_washed_bones(catalog: Catalog) -> None:
    """FR-036: preparing the bones decides whether one can be shown; the card says so."""
    washed = parse_design(
        catalog, {'kind': 'memorial', 'preparation': 'washed', 'display': 'reliquary'}
    )
    assert washed.choices['display'] == 'reliquary'
    wrapped = parse_design(
        catalog, {'kind': 'memorial', 'preparation': 'wrapped', 'display': 'reliquary'}
    )
    assert 'display' not in wrapped.choices
    display = catalog.category('display')
    preparation = catalog.category('preparation')
    assert display is not None
    assert preparation is not None
    reliquary = display.option('reliquary')
    washed_option = preparation.option('washed')
    assert reliquary is not None
    assert washed_option is not None
    assert option_offered(reliquary, washed)
    assert not option_offered(reliquary, wrapped)
    assert enables(catalog, preparation, washed_option) == ('One bone in a reliquary',)
    assert preparation.decides  # the step explains why it is asked


def test_moot_notes_come_from_the_rules(catalog: Catalog) -> None:
    roof = catalog.category('roof')
    dwelling = catalog.category('dwelling')
    kind = catalog.category('kind')
    assert roof is not None
    assert dwelling is not None
    assert kind is not None
    assert moot_note(catalog, roof) == 'Not with "Stone shrine-house" or "Open to the sky" (Form).'
    assert moot_note(catalog, dwelling) == (
        'Only for "Open to the sky" (Form); not with "The remains themselves" '
        '(The heart of the shrine).'
    )
    assert moot_note(catalog, kind) == ''


def test_rules_json_carries_conditions_and_nothing_else(catalog: Catalog) -> None:
    text = rules_json(catalog)
    rules = json.loads(text)
    assert set(rules) == {'categories', 'options', 'alt'}
    assert rules['options'] == {'display': {'reliquary': [['preparation', ['washed'], False]]}}
    assert rules['alt'] == [['kind', ['memorial'], False]]
    for word in ('koku', 'heavy', 'contract', 'lines', 'label'):
        assert word not in text


def test_shrine_name_is_trimmed_capped_and_defaulted(catalog: Catalog) -> None:
    trimmed = parse_design(catalog, {'shrine_name': '  Fox\n  Hill  '})
    assert trimmed.text == {'shrine_name': 'Fox Hill'}
    assert len(parse_design(catalog, {'shrine_name': 'x' * 500}).text['shrine_name']) == 120
    assert parse_design(catalog, {'shrine_name': '   '}).text['shrine_name'] == (
        catalog.default_name
    )


def test_share_query_round_trips_and_carries_no_gm_figure(catalog: Catalog) -> None:
    params = {'form': 'kasuga', 'roof': 'copper', 'shrine_name': 'Shoda & co', 'gm_budget': '99'}
    design = parse_design(catalog, params)
    query = share_query(catalog, design)
    assert 'gm_' not in query
    assert parse_design(catalog, dict(parse_qsl(query))) == design


# --- pricing --------------------------------------------------------------------------------------


def test_reference_design_and_default_budget(catalog: Catalog) -> None:
    design = reference_design(catalog)
    assert design.choices['kind'] == 'memorial'
    pricing = price_design(catalog, design, catalog.default_remoteness)
    assert pricing.total == pytest.approx(REFERENCE_TOTAL)
    assert pricing.heavy == pytest.approx(36)
    assert default_budget(catalog) == SUGGESTED_BUDGET


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


def test_per_step_that_is_unchosen_counts_as_one(catalog: Catalog) -> None:
    """A line `per` an unchosen step is priced at units 1."""
    design = parse_design(catalog, {'gate_material': 'stone'})
    items = [
        i for i in price_design(catalog, design, 'road').items if i.category == 'Gate material'
    ]
    assert [i.koku for i in items] == [12]


# --- negotiation ----------------------------------------------------------------------------------


def test_parse_negotiation_defaults(catalog: Catalog) -> None:
    assert parse_negotiation(catalog, {}) == Negotiation(SUGGESTED_BUDGET, 'trail', {}, {})


@pytest.mark.parametrize(
    ('raw_budget', 'expected'),
    [
        ('80', 80.0),
        (' 99.5 ', 99.5),
        ('-4', 0.0),
        ('1e9', 100_000.0),
        ('lots', SUGGESTED_BUDGET),
        ('inf', SUGGESTED_BUDGET),
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
    negotiation = Negotiation(
        SUGGESTED_BUDGET, 'trail', {'carpentry': 45, 'stonework': 40}, {'stonework': 30}
    )
    ledger = negotiate(catalog, design, negotiation)
    by_key = {c.key: c for c in ledger.contracts}
    assert by_key['carpentry'].saving_pct == 20
    assert by_key['carpentry'].paid == pytest.approx(by_key['carpentry'].fair * 0.8)
    assert by_key['stonework'].baseline == 30
    assert by_key['stonework'].saving_pct == 10
    assert by_key['roofing'].roll is None
    assert by_key['roofing'].baseline == DEFAULT_BASELINE
    assert ledger.fair_total == pytest.approx(REFERENCE_TOTAL)
    assert ledger.remainder == pytest.approx(SUGGESTED_BUDGET - ledger.paid_total)
    assert all(i.contract == 'carpentry' for i in by_key['carpentry'].items)


def test_negotiate_skips_empty_contracts_and_reports_shortfall(catalog: Catalog) -> None:
    design = parse_design(
        catalog,
        {'form': 'himorogi', 'guardians': 'none', 'lanterns': 'none', 'bell': 'clap',
         'box': 'bamboo', 'sacred': 'stone'},
    )  # fmt: skip
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

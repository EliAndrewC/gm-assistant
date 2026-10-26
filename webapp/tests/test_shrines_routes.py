"""Route tests for /shrines (feature 216): what the player sees, what only the GM sees."""

from __future__ import annotations

import html as htmllib
import re
from collections.abc import Iterator
from urllib.parse import parse_qsl

import cherrypy
import pytest

from l7r.app import Root
from l7r.auth import CurrentUser
from l7r.shrines import Catalog, load_catalog, negotiate, parse_design, parse_negotiation
from l7r.shrines.access import FAILURE_TTL, TTL, CostAccess, commerce_owners

#: The sheet app's `GET /api/characters` shape, trimmed to what FR-048 reads.
ROSTER = {
    'characters': [
        # Commerce, in a group: sees costs.
        {'id': 14, 'owner_discord_id': 'merchant', 'gaming_group_id': 1, 'skills': {'commerce': 3}},
        # Commerce, but in no group.
        {'id': 30, 'owner_discord_id': 'loner', 'gaming_group_id': None, 'skills': {'commerce': 2}},
        # In a group, no Commerce (absent, and rank 0).
        {'id': 10, 'owner_discord_id': 'builder', 'gaming_group_id': 1, 'skills': {'etiquette': 2}},
        {'id': 11, 'owner_discord_id': 'zero', 'gaming_group_id': 2, 'skills': {'commerce': 0}},
        # Merely an editor of a Commerce character.
        {
            'id': 3,
            'owner_discord_id': 'other',
            'editor_discord_ids': ['helper'],
            'gaming_group_id': 2,
            'skills': {'commerce': 1},
        },
        # A combat-tracker NPC, even if it somehow had a group.
        {
            'id': 40,
            'owner_discord_id': 'npcgm',
            'gaming_group_id': 1,
            'is_npc': True,
            'skills': {'commerce': 5},
        },
        {'id': 41, 'owner_discord_id': None, 'gaming_group_id': 1, 'skills': {'commerce': 5}},
    ]
}


@pytest.fixture(scope='module')
def catalog() -> Catalog:
    return load_catalog()


@pytest.fixture
def root(catalog: Catalog) -> Root:
    # Never the network: the roster is the fixture above.
    return Root(
        relics=[], shrine_catalog=catalog, cost_access=CostAccess(lambda: 't', lambda t: ROSTER)
    )


@pytest.fixture
def as_user() -> Iterator[object]:
    def set_role(role: str | None, discord_id: str = '1') -> None:
        if role is None:
            if hasattr(cherrypy.request, 'l7r_user'):
                del cherrypy.request.l7r_user
        else:
            user = CurrentUser(discord_id, 'Someone', role)  # type: ignore[arg-type]
            cherrypy.request.l7r_user = user

    yield set_role
    set_role(None)


def most_expensive(catalog: Catalog) -> dict[str, str]:
    return {
        c.key: max(c.options, key=lambda o: sum(ln.koku + ln.heavy for ln in o.lines) * o.units).key
        for c in catalog.categories
    }


# Feature 228 adds a player's "Something else" and the GM's price for it (spec US3.5).
GM_PARAMS = {
    'gm_budget': '7',
    'gm_remote': 'deep',
    'gm_roll_carpentry': '40',
    'other_bell': 'a conch',
    'gm_other_bell': '9',
}


@pytest.mark.parametrize('role', [None, 'player'])
def test_player_view_carries_no_cost_information(
    root: Root, catalog: Catalog, as_user: object, role: str | None
) -> None:
    """FR-007 / SC-002, for the costliest design and with GM params forced into the link."""
    as_user(role)  # type: ignore[operator]
    page = root.shrines(**most_expensive(catalog), **GM_PARAMS).decode('utf-8')
    lowered = page.lower()
    assert 'koku' not in lowered
    assert 'gm_' not in page
    assert 'ledger' not in lowered
    for contract in catalog.contracts:
        assert contract.label not in page
    for remote in catalog.remoteness:
        assert remote.label not in page


def test_player_view_lists_every_category(root: Root, catalog: Catalog) -> None:
    page = root.shrines().decode('utf-8')
    for category in catalog.categories:
        assert f'data-cat="{category.key}"' in page
    assert 'href="/shrines"' in page  # in the nav
    assert '>Shrines<' in page


def test_moot_category_is_disabled(root: Root) -> None:
    page = root.shrines(form='himorogi').decode('utf-8')
    fieldset = re.search(r'<fieldset class="shrine-cat is-moot" data-cat="roof" disabled>', page)
    assert fieldset is not None
    assert 'Not with &#34;Stone shrine-house&#34; or &#34;Open to the sky&#34; (Form).' in page


def test_dropped_choice_notice(root: Root) -> None:
    page = root.shrines(roof='gold-leaf').decode('utf-8')
    assert '1 choice in this link could not be restored and was reset: Roof covering.' in page
    page = root.shrines(roof='gold-leaf', bell='trumpet').decode('utf-8')
    assert '2 choices in this link could not be restored and were reset' in page


def test_share_link_round_trips(root: Root, catalog: Catalog) -> None:
    """SC-003: the link on the page reproduces every selection and the free text."""
    params = {
        'form': 'kasuga',
        'roof': 'kokera',
        'guardians': 'komainu',
        'shrine_name': 'Shoda <the> hermit',
    }
    page = root.shrines(**params).decode('utf-8')
    value = re.search(r'id="shrine-share-url"[^>]*>([^<]*)</textarea>', page)
    assert value is not None
    query = htmllib.unescape(value.group(1)).split('?', 1)[1]
    assert parse_design(catalog, dict(parse_qsl(query))) == parse_design(catalog, params)
    assert '<the>' not in page  # free text is escaped


def test_gm_view_sums_match_the_ledger(root: Root, catalog: Catalog, as_user: object) -> None:
    """SC-005: the GM's totals are the module's arithmetic."""
    as_user('gm')  # type: ignore[operator]
    params = {'form': 'shinmei', 'roof': 'thatch', **GM_PARAMS}
    page = root.shrines(**params).decode('utf-8')
    ledger = negotiate(catalog, parse_design(catalog, params), parse_negotiation(catalog, params))
    assert 'GM ledger' in page
    assert ledger.remainder < 0
    assert re.search(r'Shortfall</dt><dd>([^<]*)', page) is not None
    for contract in ledger.contracts:
        assert contract.label in page
    assert 'name="gm_roll_carpentry" min="0" max="200" value="40"' in page
    assert 'gm_budget=7' in page
    assert 'choices still open' in page  # the GM's own link keeps the figures


def test_gm_view_shows_what_tadashi_keeps(root: Root, as_user: object) -> None:
    as_user('gm')  # type: ignore[operator]
    page = root.shrines(form='himorogi').decode('utf-8')
    assert re.search(r'Tadashi keeps so far</dt><dd>[^<]*koku', page) is not None
    assert 'not yet negotiated' in page


def test_chosen_option_with_voids_stays_checked(root: Root) -> None:
    """A whitespace slip once glued `checked` onto `data-voids` ("checkeddata-voids"), so the
    browser saw no checked form and dropped it from the share link."""
    page = root.shrines(form='himorogi').decode('utf-8')
    assert re.search(r'value="himorogi" checked />', page) is not None
    assert 'checkeddata' not in page


def test_summary_lists_the_picks(root: Root) -> None:
    page = root.shrines(form='kasuga', roof='copper').decode('utf-8')
    assert 'data-goto="form"><span>Form</span> <em>Gable-entry</em></a>' in page
    assert 'data-goto="roof"><span>Roof covering</span> <em>Copper sheet</em></a>' in page
    assert (
        'data-goto="bell"><span>Announcing</span> <em class="is-open">not chosen yet</em></a>'
        in page
    )


def test_wizard_has_a_step_per_category_plus_name_and_review(root: Root, catalog: Catalog) -> None:
    """FR-018: one decision per step; the name first, the summary and link last."""
    page = root.shrines().decode('utf-8')
    steps = re.findall(r'class="wizard-step[^"]*" id="shrine-step-([a-z_]+)"', page)
    assert steps == ['name', *(c.key for c in catalog.categories), 'review']
    assert 'data-next' in page
    assert 'data-back' in page


def test_name_is_prefilled_and_no_homework_fields(root: Root, catalog: Catalog) -> None:
    """FR-017: one free-text field the player must have, pre-filled; no sacred-object notes, no
    inscription box. Feature 228 (FR-010) adds one OPTIONAL "Something else" box per step: disabled
    until the player turns it on, so it is never asked of them and never reaches the link empty."""
    page = root.shrines().decode('utf-8')
    assert (
        f'name="shrine_name" rows="1" maxlength="120" data-one-line>{catalog.default_name}<' in page
    )
    assert page.count('<textarea name=') == 1
    others = re.findall(r'<textarea class="shrine-other__text"[^>]*>', page)
    assert len(others) == len(catalog.categories)
    assert all(' disabled' in t for t in others)
    for gone in ('enshrined', 'sacred_note', 'inscription'):
        assert f'name="{gone}"' not in page


def test_nothing_is_preselected(root: Root) -> None:
    page = root.shrines().decode('utf-8')
    assert ' checked' not in page


def test_open_choices_are_flagged_on_the_summary_and_ledger(root: Root, as_user: object) -> None:
    page = root.shrines(form='hokora').decode('utf-8')
    assert re.search(r'<strong data-open-count>\d+ choices still open\.</strong>', page)
    as_user('gm')  # type: ignore[operator]
    gm = root.shrines(form='hokora').decode('utf-8')
    assert 'Tadashi keeps so far' in gm


def test_complete_design_has_no_open_note(root: Root, catalog: Catalog) -> None:
    page = root.shrines(**{c.key: c.reference for c in catalog.categories}).decode('utf-8')
    assert 'data-open-note hidden' in page


def test_appeal_and_only_with_render(root: Root) -> None:
    page = root.shrines().decode('utf-8')
    assert 'class="shrine-opt__appeal">The purest finish in the old view' in page
    assert '<script type="application/json" id="shrine-rules">' in page
    assert 'Only for &#34;Open to the sky&#34; (Form).' in page


def test_kind_step_comes_right_after_the_name(root: Root) -> None:
    page = root.shrines().decode('utf-8')
    steps = re.findall(r'class="wizard-step[^"]*" id="shrine-step-([a-z_]+)"', page)
    assert steps[:3] == ['name', 'kind', 'heart']


def test_alt_wording_renders_and_switches(root: Root) -> None:
    plain = root.shrines(kind='kami').decode('utf-8')
    assert 'class="w-memorial">How is the shrine consecrated?' in plain
    assert 'class="w-fortune">How is the Fortune called to the shrine?' in plain
    assert 'wording-plain" id="shrine-form"' in plain
    assert 'wording-memorial" id="shrine-form"' in root.shrines(kind='memorial').decode('utf-8')
    assert 'wording-fortune" id="shrine-form"' in root.shrines(kind='fortune').decode('utf-8')
    assert '.shrine-form:not(.wording-fortune) .w-fortune' in plain


def test_memorial_path_reaches_summary_and_ledger(root: Root, as_user: object) -> None:
    params = {
        'kind': 'memorial',
        'heart': 'registered',
        'preparation': 'washed',
        'sharing': 'temple',
        'resting': 'gorinto',
        'display': 'reliquary',
    }
    page = root.shrines(**params).decode('utf-8')
    assert (
        'data-goto="sharing"><span>Dividing the remains</span> '
        '<em>A portion to a temple they were connected to</em>'
    ) in page
    assert (
        'data-goto="display"><span>Showing the remains</span> <em>One bone in a reliquary' in page
    )
    assert (
        'data-goto="preparation"><span>Preparing the remains</span> <em>Washed clean</em>' in page
    )
    as_user('gm')  # type: ignore[operator]
    gm = root.shrines(**params).decode('utf-8')
    assert 'Burakumin (retrieving and preparing the remains)' in gm
    assert 'Dividing the remains: A portion to a temple they were connected to' in gm


def test_rules_script_in_player_page_carries_no_prices(root: Root, catalog: Catalog) -> None:
    """The browser gets the rules (conditions only); the whole-page test above covers the rest."""
    page = root.shrines(**most_expensive(catalog)).decode('utf-8')
    found = re.search(r'id="shrine-rules">(.*?)</script>', page, re.S)
    assert found is not None
    blob = found.group(1)
    for word in ('koku', 'heavy', 'contract', 'lines', 'porter'):
        assert word not in blob


def test_preparation_says_what_it_decides(root: Root) -> None:
    """FR-036: the step explains why it is asked, and the washed card names what it opens."""
    page = root.shrines(kind='memorial').decode('utf-8')
    assert (
        'class="shrine-cat__decides">Burned or buried, what is left is more than clean bone' in page
    )
    assert '<b>Makes possible later:</b> One bone in a reliquary' in page
    assert 'data-effect-tag>1 custom choice</span>' in page
    assert 'shrine-opt-cell is-unavailable' in page  # the reliquary, until bones are washed


def test_counter_counts_phases(root: Root) -> None:
    """FR-042: every step carries its phase; the denominator is the fixed number of phases."""
    page = root.shrines(kind='memorial').decode('utf-8')
    assert 'data-phases="5"' in page
    assert 'data-step="heart" data-chapter="The remains" data-phase="1"' in page
    assert 'data-step="review" data-chapter="Your shrine" data-phase="5"' in page
    assert 'skipped' not in page


def test_multi_select_step_renders_checkboxes_and_hint(root: Root) -> None:
    page = root.shrines(kind='memorial', sharing=['temple', 'mountain']).decode('utf-8')
    assert (
        'class="shrine-multi__hint">Choose any that apply - or, below, keep them together' in page
    )
    assert page.count('type="checkbox" name="sharing"') == 4
    assert 'value="together" data-exclusive' in page
    assert 'value="temple" checked' in page
    assert (
        '<em>A portion to a temple they were connected to; A portion to a mountain temple</em>'
        in page
    )


def test_japanese_terms_carry_tooltips(root: Root) -> None:
    page = root.shrines(kind='memorial').decode('utf-8')
    assert (
        'data-gloss><span lang="ja">洗骨</span> <em>senkotsu</em><span class="shrine-term__tip"'
        in page
    )


# ---------------------------------------------------------------- FR-048: Commerce players


def test_commerce_owners_reads_owner_group_skill_and_npc() -> None:
    assert commerce_owners(ROSTER) == frozenset({'merchant', 'other'})
    assert commerce_owners({}) == frozenset()


@pytest.mark.parametrize('who', ['loner', 'builder', 'zero', 'helper', 'npcgm', '1'])
def test_a_player_without_a_grouped_commerce_character_sees_no_cost(
    root: Root, catalog: Catalog, as_user: object, who: str
) -> None:
    as_user('player', who)  # type: ignore[operator]
    page = root.shrines(**most_expensive(catalog), **GM_PARAMS).decode('utf-8')
    assert 'koku' not in page.lower()
    assert 'gm_' not in page


def test_a_commerce_player_sees_the_ledger_read_only(
    root: Root, catalog: Catalog, as_user: object
) -> None:
    as_user('player', 'merchant')  # type: ignore[operator]
    page = root.shrines(**most_expensive(catalog), **GM_PARAMS).decode('utf-8')
    assert 'koku' in page
    assert '>Ledger</h2>' in page
    assert 'GM ledger' not in page
    assert 'Only a GM' not in page
    # The link's GM figures are shown and carried, never editable (the GM said "see").
    assert 'type="number"' not in page
    assert '<select name="gm_remote"' not in page
    assert '<input type="hidden" name="gm_budget" value="7" />' in page
    assert '<input type="hidden" name="gm_remote" value="deep" />' in page
    assert '<input type="hidden" name="gm_roll_carpentry" value="40" />' in page
    assert 'Roll 40 against baseline 25' in page
    assert 'Roll -' not in page
    assert 'Only your GM can change these figures' in page
    assert 'Update totals' not in page
    assert 'Link with these GM figures' not in page
    assert 'data-priced="true"' in page
    assert 'data-gm="false"' in page


def test_the_gm_ledger_keeps_its_inputs_and_says_who_else_sees_it(
    root: Root, catalog: Catalog, as_user: object
) -> None:
    as_user('gm')  # type: ignore[operator]
    page = root.shrines(**most_expensive(catalog), **GM_PARAMS).decode('utf-8')
    assert '<select name="gm_remote"' in page
    assert 'name="gm_roll_carpentry"' in page
    assert 'type="number"' in page
    assert 'Players whose characters have Commerce see these figures too' in page
    assert 'data-priced="true"' in page
    assert 'data-gm="true"' in page


def test_the_roster_is_fetched_only_for_a_signed_in_non_gm(
    catalog: Catalog, as_user: object
) -> None:
    calls: list[str] = []

    def fetch(token: str) -> object:
        calls.append(token)
        return ROSTER

    root = Root(relics=[], shrine_catalog=catalog, cost_access=CostAccess(lambda: 't', fetch))
    root.shrines()
    as_user('gm')  # type: ignore[operator]
    root.shrines()
    assert calls == []
    as_user('player', 'merchant')  # type: ignore[operator]
    root.shrines()
    root.shrines()
    assert calls == ['t']  # cached


def test_cost_access_caches_and_fails_closed() -> None:
    now = [0.0]
    answers: list[object] = [ROSTER, OSError('down'), ROSTER]

    def fetch(token: str) -> object:
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    access = CostAccess(lambda: 't', fetch, clock=lambda: now[0])
    assert access.allows('merchant')
    now[0] = TTL - 1
    assert access.allows('merchant')  # still cached
    now[0] = TTL
    assert not access.allows('merchant')  # sheet down: GM only
    now[0] = TTL + FAILURE_TTL - 1
    assert not access.allows('merchant')  # the failure is cached briefly
    now[0] = TTL + FAILURE_TTL
    assert access.allows('merchant')  # back
    assert answers == []


def test_cost_access_without_a_token_never_fetches() -> None:
    def fetch(token: str) -> object:
        raise AssertionError('fetched without a token')

    access = CostAccess(lambda: '', fetch)
    assert not access.allows('merchant')
    assert not access.allows('merchant')


def test_the_sheet_token_comes_from_the_secrets_file(monkeypatch: pytest.MonkeyPatch) -> None:
    import l7r.app as app

    monkeypatch.setattr(
        app, '_load_secrets', lambda: {'character_sheet': {'roll_query_token': ' r '}}
    )
    assert app._sheet_token() == 'r'
    monkeypatch.setattr(app, '_load_secrets', lambda: {})
    assert app._sheet_token() == ''

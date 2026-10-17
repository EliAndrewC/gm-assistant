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


@pytest.fixture(scope='module')
def catalog() -> Catalog:
    return load_catalog()


@pytest.fixture
def root(catalog: Catalog) -> Root:
    return Root(relics=[], shrine_catalog=catalog)


@pytest.fixture
def as_user() -> Iterator[object]:
    def set_role(role: str | None) -> None:
        if role is None:
            if hasattr(cherrypy.request, 'l7r_user'):
                del cherrypy.request.l7r_user
        else:
            cherrypy.request.l7r_user = CurrentUser('1', 'Someone', role)  # type: ignore[arg-type]

    yield set_role
    set_role(None)


def most_expensive(catalog: Catalog) -> dict[str, str]:
    return {
        c.key: max(c.options, key=lambda o: sum(ln.koku + ln.heavy for ln in o.lines) * o.units).key
        for c in catalog.categories
    }


GM_PARAMS = {'gm_budget': '7', 'gm_remote': 'deep', 'gm_roll_carpentry': '40'}


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
    assert 'Does not apply with this form.' in page


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
    assert re.search(r'value="himorogi" checked data-voids="', page) is not None
    assert 'checkeddata' not in page


def test_summary_lists_the_picks(root: Root) -> None:
    page = root.shrines(form='kasuga', roof='copper').decode('utf-8')
    assert 'data-goto="form"><span>Form</span> <em>Gable-entry</em></a>' in page
    assert 'data-goto="roof"><span>Roof covering</span> <em>Copper sheet</em></a>' in page
    assert 'data-goto="bell"><span>Bell</span> <em class="is-open">not chosen yet</em></a>' in page


def test_wizard_has_a_step_per_category_plus_name_and_review(root: Root, catalog: Catalog) -> None:
    """FR-018: one decision per step; the name first, the summary and link last."""
    page = root.shrines().decode('utf-8')
    steps = re.findall(r'class="wizard-step[^"]*" id="shrine-step-([a-z_]+)"', page)
    assert steps == ['name', *(c.key for c in catalog.categories), 'review']
    assert 'data-next' in page
    assert 'data-back' in page


def test_name_is_prefilled_and_no_homework_fields(root: Root, catalog: Catalog) -> None:
    """FR-017: one free-text field, pre-filled; no sacred-object notes, no inscription box."""
    page = root.shrines().decode('utf-8')
    assert f'name="shrine_name" maxlength="120" value="{catalog.default_name}"' in page
    assert '<textarea name=' not in page
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

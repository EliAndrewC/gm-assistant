"""Route-level tests for the /places section.

Each test calls Root.places(...) directly with query parameters and inspects
the returned HTML. The places fixture pool has 7 hand-picked entries spanning
all four scales and several commonalities.
"""

from __future__ import annotations

from pathlib import Path

import cherrypy
import pytest

from l7r.app import Root
from l7r.places import load_places


@pytest.fixture
def sample_places_dir() -> Path:
    return Path(__file__).parent / 'fixtures' / 'places_sample'


@pytest.fixture
def root(sample_places_dir: Path) -> Root:
    """Root wired against the places fixture pool only.

    Relics and names default to empty lists; we only exercise the /places
    handler here.
    """
    return Root(relics=[], places=load_places(sample_places_dir))


# ---------------------- index ----------------------


def test_places_index_renders(root: Root) -> None:
    html = root.places().decode('utf-8')
    assert '7 of 7' in html  # filtered_count of total_count
    assert 'Owari' in html
    assert 'Yuhimura' in html
    assert 'Mori-tono' in html


def test_places_index_shows_all_filter_rails(root: Root) -> None:
    html = root.places().decode('utf-8')
    assert 'Filter by place type' in html
    assert 'Filter by commonality' in html
    assert 'Filter by regional context' in html
    assert 'Filter by suffix' in html


def test_places_index_random_button_present(root: Root) -> None:
    html = root.places().decode('utf-8')
    assert 'places-random' in html
    assert 'random=1' in html


def test_places_index_filters_by_place_type(root: Root) -> None:
    html = root.places(place_type='province').decode('utf-8')
    # Only entries tagged 'province' should appear in the listing card.
    assert 'place-card' in html
    assert 'Owari' in html  # multi-scale entry includes province
    assert 'Yamashiro' in html
    # Yuhimura is village-only and should not appear.
    assert 'Yuhimura</h2>' not in html


def test_places_index_filters_by_commonality(root: Root) -> None:
    html = root.places(commonality='rare').decode('utf-8')
    assert '1 of 7' in html
    assert 'Mori-tono' in html
    assert 'Yuhimura</h2>' not in html


def test_places_index_filters_by_regional(root: Root) -> None:
    html = root.places(regional='riverine').decode('utf-8')
    assert 'Aozawa' in html
    assert 'Owari' not in html or '>Owari<' not in html


def test_places_index_filters_by_suffix(root: Root) -> None:
    html = root.places(suffix='-mura').decode('utf-8')
    assert 'Yuhimura' in html
    assert 'Mori-tono</h2>' not in html


def test_places_index_filters_by_suffix_none(root: Root) -> None:
    html = root.places(suffix='none').decode('utf-8')
    # Entries with null suffix: Owari, Yuhi, Yamashiro
    assert 'Owari' in html
    assert 'Yuhi</h2>' in html
    assert 'Yamashiro' in html
    # Entries with a suffix should not appear in the cards.
    assert 'Yuhimura</h2>' not in html


def test_places_index_composes_filters(root: Root) -> None:
    html = root.places(place_type='village', commonality='rare').decode('utf-8')
    assert 'Mori-tono' in html
    assert '1 of 7' in html


def test_places_index_ignores_unknown_filter_values(root: Root) -> None:
    # Unknown place_type, commonality, regional are silently dropped.
    html = root.places(place_type='nonsense').decode('utf-8')
    assert '7 of 7' in html


def test_places_index_empty_state_when_no_matches(root: Root) -> None:
    html = root.places(place_type='village', commonality='unique').decode('utf-8')
    assert 'No places match' in html
    assert '0 of 7' in html


def test_places_index_preserves_filter_links(root: Root) -> None:
    # When place_type is set, the commonality filter links should still carry
    # place_type=village so changing commonality doesn't reset place_type.
    # Browsers tolerate raw '&' in href; Jinja macros return Markup so the
    # ampersand from the macro's literal text is not auto-escaped.
    html = root.places(place_type='village').decode('utf-8')
    assert 'href="/places?commonality=common&place_type=village"' in html


# ---------------------- random ----------------------


def test_places_index_random_redirects_to_detail(root: Root) -> None:
    # CherryPy's HTTPRedirect resolves URLs through cherrypy.url(), so the
    # exception holds an absolute URL. Check the path suffix.
    with pytest.raises(cherrypy.HTTPRedirect) as exc:
        root.places(random='1')
    url = exc.value.urls[0]
    assert '/places/' in url
    # Strip the query string and pull the slug from the path.
    slug = url.split('?', 1)[0].rsplit('/', 1)[-1]
    assert slug in {'owari', 'yuhimura', 'yuhi', 'aozawa', 'yamashiro', 'mori-tono', 'hon-machi'}


def test_places_index_random_respects_filter(root: Root) -> None:
    # rare + village filters to exactly Mori-tono; random must redirect there.
    with pytest.raises(cherrypy.HTTPRedirect) as exc:
        root.places(random='1', place_type='village', commonality='rare')
    url = exc.value.urls[0]
    assert '/places/mori-tono?' in url


def test_places_index_random_redirect_includes_via_param(root: Root) -> None:
    # The redirect URL must carry via=random so the detail page knows it
    # was reached from a random pick (and renders "Another random pick").
    with pytest.raises(cherrypy.HTTPRedirect) as exc:
        root.places(random='1')
    assert 'via=random' in exc.value.urls[0]


def test_places_index_random_redirect_preserves_filter_qs(root: Root) -> None:
    # Filter params are passed through the redirect so "Another random pick"
    # on the detail page stays within the same filtered subset.
    with pytest.raises(cherrypy.HTTPRedirect) as exc:
        root.places(random='1', place_type='village', commonality='rare')
    url = exc.value.urls[0]
    assert 'via=random' in url
    assert 'place_type=village' in url
    assert 'commonality=rare' in url


def test_places_index_random_with_empty_filter_renders_empty_index(root: Root) -> None:
    # When the filter returns nothing, the random param is a no-op and we
    # render the empty index instead of redirecting or 404ing.
    html = root.places(random='1', place_type='village', commonality='unique').decode('utf-8')
    assert 'No places match' in html


# ---------------------- detail ----------------------


def test_places_detail_renders_for_village(root: Root) -> None:
    html = root.places(slug='yuhimura').decode('utf-8')
    assert '夕日村' in html
    assert 'Yuhimura' in html
    assert 'sunset village' in html
    # Suffix emit-time note is shown.
    assert 'generic word for village' in html


def test_places_detail_renders_for_multi_scale_entry(root: Root) -> None:
    html = root.places(slug='owari').decode('utf-8')
    assert '尾張' in html
    # Multi-scale entries get the scale toggle.
    assert 'places-copy__scale-toggle' in html
    assert 'data-scale="province"' in html
    assert 'data-scale="hamlet"' in html


def test_places_detail_single_scale_uses_scale_label(root: Root) -> None:
    html = root.places(slug='yuhimura').decode('utf-8')
    # Single-scale entries should NOT get the toggle.
    assert 'places-copy__scale-toggle' not in html
    assert 'places-copy__scale-label' in html


def test_places_detail_preselects_first_scale_by_default(root: Root) -> None:
    # Aozawa.place_types == ('village', 'hamlet'). With no filter context the
    # toggle defaults to the first scale (village).
    html = root.places(slug='aozawa').decode('utf-8')
    village_active = (
        '<button type="button"\n                      '
        'class="places-copy__scale-btn places-copy__scale-btn--active"\n                      '
        'data-scale="village"'
    )
    hamlet_active_aria = (
        'data-scale="hamlet"\n                      role="radio"\n'
        '                      aria-checked="true"'
    )
    assert village_active in html
    assert hamlet_active_aria not in html


def test_places_detail_preselects_filtered_scale(root: Root) -> None:
    # Same entry, but the GM came in from the hamlet filter. The hamlet
    # button should be the preselected one this time.
    html = root.places(slug='aozawa', place_type='hamlet').decode('utf-8')
    hamlet_active = (
        '<button type="button"\n                      '
        'class="places-copy__scale-btn places-copy__scale-btn--active"\n                      '
        'data-scale="hamlet"'
    )
    village_active = (
        '<button type="button"\n                      '
        'class="places-copy__scale-btn places-copy__scale-btn--active"\n                      '
        'data-scale="village"'
    )
    assert hamlet_active in html
    assert village_active not in html


def test_places_detail_falls_back_when_filter_scale_not_in_entry(root: Root) -> None:
    # Mori-tono is village-only. If the GM filter was hamlet (which mori-tono
    # is not), the toggle isn't shown at all (single-scale uses the label),
    # so this just confirms no crash and the scale label still renders.
    html = root.places(slug='mori-tono', place_type='hamlet').decode('utf-8')
    assert 'places-copy__scale-label' in html
    assert 'places-copy__scale-toggle' not in html


def test_places_detail_multi_scale_falls_back_when_filter_scale_not_in_entry(
    root: Root,
) -> None:
    # Aozawa is village+hamlet. If the GM came from province filter (not
    # applicable to this entry), the toggle should default to the first
    # scale (village), not blow up.
    html = root.places(slug='aozawa', place_type='province').decode('utf-8')
    village_active = (
        '<button type="button"\n                      '
        'class="places-copy__scale-btn places-copy__scale-btn--active"\n                      '
        'data-scale="village"'
    )
    assert village_active in html


def test_places_detail_includes_entry_notes(root: Root) -> None:
    html = root.places(slug='yuhi').decode('utf-8')
    assert 'Paired with Yuhimura.' in html


def test_places_detail_includes_region(root: Root) -> None:
    html = root.places(slug='aozawa').decode('utf-8')
    assert 'riverine' in html


def test_places_detail_unknown_slug_returns_404(root: Root) -> None:
    try:
        html = root.places(slug='does-not-exist').decode('utf-8')
    finally:
        cherrypy.response.status = 200
    assert '404' in html


# ---------------------- navigation state preservation ----------------------


def test_places_detail_from_random_shows_another_pick_button(root: Root) -> None:
    html = root.places(slug='yuhimura', via='random').decode('utf-8')
    assert 'Another random pick' in html
    # The button links back to /places?random=1 so the next pick happens
    # server-side with the same filter context.
    assert 'href="/places?random=1' in html


def test_places_detail_without_via_omits_another_pick_button(root: Root) -> None:
    html = root.places(slug='yuhimura').decode('utf-8')
    assert 'Another random pick' not in html


def test_places_detail_another_pick_preserves_filter_qs(root: Root) -> None:
    html = root.places(
        slug='mori-tono', via='random', place_type='village', commonality='rare'
    ).decode('utf-8')
    # Filter axes ride along on the "Another random pick" button.
    assert 'random=1' in html
    assert 'place_type=village' in html
    assert 'commonality=rare' in html


def test_places_detail_back_link_includes_filter_qs(root: Root) -> None:
    html = root.places(slug='yuhimura', place_type='village').decode('utf-8')
    assert 'href="/places?place_type=village#card-yuhimura"' in html


def test_places_detail_back_link_includes_card_anchor(root: Root) -> None:
    html = root.places(slug='yuhimura').decode('utf-8')
    # Without filters the back-link still anchors to the card just visited.
    assert 'href="/places#card-yuhimura"' in html


def test_places_index_card_link_carries_filter_qs(root: Root) -> None:
    html = root.places(place_type='village').decode('utf-8')
    # The card link forward-carries the filter context so clicking a card
    # and then "back to the pool" returns to the same filtered view.
    assert 'href="/places/yuhimura?place_type=village"' in html


def test_places_index_card_has_anchor_id(root: Root) -> None:
    html = root.places().decode('utf-8')
    assert 'id="card-yuhimura"' in html


def test_build_filter_qs_skips_empty_axes() -> None:
    from l7r.app import _build_filter_qs

    result = _build_filter_qs(place_type='village', commonality=None, regional=None, suffix='-mura')
    assert result == 'place_type=village&suffix=-mura'


def test_build_filter_qs_empty_when_no_axes() -> None:
    from l7r.app import _build_filter_qs

    assert _build_filter_qs(place_type=None, commonality=None, regional=None, suffix=None) == ''

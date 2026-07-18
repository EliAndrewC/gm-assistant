"""Integration tests for the CherryPy Root.

These exercise the Root class directly - we do not stand up a real HTTP
server. CherryPy `expose`d methods are plain callables; we call them and
inspect the returned HTML bytes.
"""

from __future__ import annotations

from pathlib import Path

import cherrypy
import pytest

from l7r.app import (
    Root,
    _error_page_handler,
    _forbidden_handler,
    _group_relics_by_fortune,
    make_app,
)
from l7r.names import load_names
from l7r.pool import load_relics


@pytest.fixture
def sample_names_dir() -> Path:
    return Path(__file__).parent / 'fixtures' / 'names_sample'


@pytest.fixture
def root(sample_pool_dir: Path, sample_names_dir: Path) -> Root:
    """A Root wired against the fixture relic + names pools."""
    return Root(
        relics=load_relics(sample_pool_dir),
        names=load_names(sample_names_dir),
    )


def test_index_renders_landing(root: Root) -> None:
    html = root.index().decode('utf-8')
    assert '<!doctype html>' in html.lower()
    assert 'L7R' in html
    assert 'Toolkit' in html
    assert 'Characters' in html
    assert 'Relics' in html


def test_viewer_serves_standalone_page(root: Root) -> None:
    html = root.viewer().decode('utf-8')
    # Full standalone document (not wrapped in the site layout), neutral title.
    assert html.lower().startswith('<!doctype html>')
    assert '<title>Portrait</title>' in html
    assert 'Portrait viewer' in html


def test_relics_index_lists_all_fortune_sections(root: Root) -> None:
    html = root.relics().decode('utf-8')
    # Sections for fortunes that have relics in the fixture pool.
    assert 'fortune-benten' in html
    assert 'fortune-bishamon' in html
    assert 'fortune-ebisu' in html
    # Seal-filter rail is present.
    assert 'data-fortune="all"' in html
    # Filter buttons for fortunes without any relics still render.
    assert 'data-fortune="daikoku"' in html


def test_relics_index_cards_show_summary_not_named_entity(root: Root) -> None:
    html = root.relics().decode('utf-8')
    # The card now carries a 1-sentence summary (derived from the
    # description's first sentence), replacing the prior named-entity line.
    assert 'card__summary' in html
    assert 'card__entity' not in html
    # Sample fixture description starts: "A small stone used in tests."
    assert 'A small stone used in tests.' in html
    # The named-entity text is intentionally NOT on the card anymore.
    assert 'A fictional figure used as a test fixture' not in html


def test_relics_index_has_both_filter_rails(root: Root) -> None:
    html = root.relics().decode('utf-8')
    # Fortune rail (existing) + clan rail (new) both present.
    assert 'Filter by fortune' in html
    assert 'Filter by clan' in html
    # The "all" button shows up in each rail.
    assert 'data-fortune="all"' in html
    assert 'data-clan="all"' in html


def test_relics_index_clan_rail_only_lists_clans_with_relics(root: Root) -> None:
    html = root.relics().decode('utf-8')
    # Fixture has relics for fox + scorpion + crab + crane (sample pool).
    # A clan with no relic in the fixture should NOT have a filter button.
    assert 'data-clan="fox"' in html or 'data-clan="crab"' in html  # at least one fixture clan
    # 'wasp' has no fixture relic - must not appear in the rail.
    assert 'data-clan="wasp"' not in html


def test_relic_detail_renders(root: Root) -> None:
    html = root.relics(slug='sample-benten-cup').decode('utf-8')
    assert '試の盃' in html
    assert 'detail-prose' in html


def test_relic_detail_includes_prev_next_within_fortune(root: Root) -> None:
    # Benten has two relics in the fixture; the first should have a "next" link.
    html = root.relics(slug='sample-benten-cup').decode('utf-8')
    assert 'sample-benten-stone' in html


def test_relic_detail_unknown_slug_returns_404(root: Root) -> None:
    try:
        html = root.relics(slug='does-not-exist').decode('utf-8')
    finally:
        cherrypy.response.status = 200  # reset for other tests
    assert '404' in html


def test_relic_detail_with_unknown_fortune_returns_404(
    sample_pool_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from l7r.pool import Relic

    fake = Relic(
        slug='ghost',
        name='Ghost',
        japanese_romaji='Yurei',
        japanese_kanji='幽霊',
        fortune='not-a-fortune',
        clan='any',
        temple='nowhere',
        named_entity='nobody',
        relic_type='nothing',
        description='ghosts.',
    )
    root = Root(relics=[fake, *load_relics(sample_pool_dir)])
    try:
        html = root.relics(slug='ghost').decode('utf-8')
    finally:
        cherrypy.response.status = 200
    assert '404' in html


def test_terms_renders(root: Root) -> None:
    html = root.terms().decode('utf-8')
    assert 'Terms of Service' in html
    assert 'L7R' in html


def test_privacy_renders(root: Root) -> None:
    html = root.privacy().decode('utf-8')
    assert 'Privacy Policy' in html
    assert 'identify' in html  # mentions the OAuth scope we request


def test_names_renders_index(root: Root) -> None:
    html = root.names().decode('utf-8')
    assert 'Hiroshi' in html
    assert 'Akiko' in html
    assert '5 of 5' in html  # filtered_count of total_count


def test_names_filters_by_gender(root: Root) -> None:
    html = root.names(gender='female').decode('utf-8')
    assert 'Akiko' in html
    assert 'Hanae' in html
    assert 'Hiroshi' not in html
    assert '2 of 5' in html


def test_names_filters_by_caste_peasant(root: Root) -> None:
    html = root.names(caste='peasant').decode('utf-8')
    assert 'Goro' in html
    assert 'Hiroshi' not in html
    assert '1 of 5' in html


def test_names_filters_by_caste_samurai(root: Root) -> None:
    html = root.names(caste='samurai').decode('utf-8')
    assert 'Hiroshi' in html
    assert 'Goro' not in html


def test_names_filters_compose_gender_and_caste(root: Root) -> None:
    # fixture: Akiko + Hanae (female/samurai), Hiroshi + Toshiro (male/samurai), Goro (male/peasant)
    html = root.names(gender='female', caste='samurai').decode('utf-8')
    assert 'Akiko' in html
    assert 'Hanae' in html
    assert 'Hiroshi' not in html
    assert 'Goro' not in html
    assert '2 of 5' in html


def test_names_filters_compose_to_empty(root: Root) -> None:
    # No female peasant in the fixture.
    html = root.names(gender='female', caste='peasant').decode('utf-8')
    assert '0 of 5' in html
    assert 'No names match' in html


def test_names_template_preserves_other_axis_in_links(root: Root) -> None:
    # When viewing ?gender=female, the caste filter links should still carry gender=female,
    # so picking samurai vs peasant doesn't reset the gender choice.
    html = root.names(gender='female').decode('utf-8')
    assert 'href="/names?caste=samurai&amp;gender=female"' in html
    assert 'href="/names?caste=peasant&amp;gender=female"' in html


def test_names_ignores_unknown_gender(root: Root) -> None:
    html = root.names(gender='other').decode('utf-8')
    assert '5 of 5' in html


def test_names_ignores_unknown_caste(root: Root) -> None:
    html = root.names(caste='nobility').decode('utf-8')
    assert '5 of 5' in html


def test_names_default_button_label_is_random_pick(root: Root) -> None:
    html = root.names().decode('utf-8')
    # No pick yet: pill reads "Random pick".
    assert '>Random pick<' in html
    assert 'Another random pick' not in html


def test_names_with_valid_picked_morphs_button_label(root: Root) -> None:
    html = root.names(picked='male-hiroshi').decode('utf-8')
    # A confirmed pick switches the masthead pill label.
    assert 'Another random pick' in html
    # The picked card has an anchor target the browser can scroll to.
    assert 'id="card-male-hiroshi"' in html


def test_names_with_unknown_picked_falls_back_to_default_label(root: Root) -> None:
    # A bogus picked slug shouldn't leave the button stuck on "Another...".
    html = root.names(picked='nope-nope').decode('utf-8')
    assert '>Random pick<' in html
    assert 'Another random pick' not in html


def test_names_random_redirects_with_picked_and_anchor(root: Root) -> None:
    with pytest.raises(cherrypy.HTTPRedirect) as exc:
        root.names(random='1')
    url = exc.value.urls[0]
    assert '/names?picked=' in url
    # Fragment for browser auto-scroll to the picked card.
    assert '#card-' in url


def test_names_random_redirects_preserve_filter_qs(root: Root) -> None:
    with pytest.raises(cherrypy.HTTPRedirect) as exc:
        root.names(random='1', gender='female', caste='samurai')
    url = exc.value.urls[0]
    assert 'gender=female' in url
    assert 'caste=samurai' in url


def test_names_random_with_empty_filter_renders_index(root: Root) -> None:
    # No female peasants in the fixture; random should be a no-op.
    html = root.names(random='1', gender='female', caste='peasant').decode('utf-8')
    assert 'No names match' in html


def test_names_picked_outside_current_filter_is_cleared(root: Root) -> None:
    # male-hiroshi is a samurai name; filtering to peasants should drop the pick.
    html = root.names(picked='male-hiroshi', caste='peasant').decode('utf-8')
    # Hiroshi isn't in the peasant filter, so the button reverts to "Random pick".
    assert '>Random pick<' in html
    assert 'Another random pick' not in html


def test_names_card_has_anchor_id(root: Root) -> None:
    html = root.names().decode('utf-8')
    # Every name card carries an id so the picked-pick anchor works.
    assert 'id="card-male-hiroshi"' in html
    assert 'id="card-female-akiko"' in html


def test_build_names_filter_qs_skips_empty_axes() -> None:
    from l7r.app import _build_names_filter_qs

    assert _build_names_filter_qs(gender='female', caste=None) == 'gender=female'
    assert _build_names_filter_qs(gender=None, caste='peasant') == 'caste=peasant'
    assert _build_names_filter_qs(gender=None, caste=None) == ''


def test_group_relics_by_fortune_has_all_fortune_keys(sample_pool_dir: Path) -> None:
    relics = load_relics(sample_pool_dir)
    grouped = _group_relics_by_fortune(relics)
    # Every FORTUNES entry - major + minor - appears as a key even if the
    # fixture pool has no relics for that Fortune.
    assert set(grouped.keys()) == {
        'benten',
        'bishamon',
        'daikoku',
        'ebisu',
        'fukurokujin',
        'hotei',
        'jurojin',
        'inari',
    }
    assert len(grouped['benten']) == 2
    assert len(grouped['daikoku']) == 0
    assert len(grouped['inari']) == 0


def test_make_app_returns_root_with_relics() -> None:
    app = make_app(
        pool_dir=Path('/nonexistent'),
        names_dir=Path('/nonexistent'),
        places_dir=Path('/nonexistent'),
    )
    assert isinstance(app, Root)
    assert app._relics == []
    assert app._names == []
    assert app._places == []


def test_error_page_handler_renders_404_template() -> None:
    html = _error_page_handler(404, 'Not Found', '', 'cherrypy/0').decode('utf-8')
    assert '404' in html
    assert 'L7R' in html


def test_forbidden_handler_renders_403_template() -> None:
    html = _forbidden_handler(403, 'Forbidden', '', 'cherrypy/0').decode('utf-8')
    assert 'GM' in html
    assert 'L7R' in html


# ---------------------------------------------------------------------------
# /archive/save - GM-only stub
# ---------------------------------------------------------------------------


def _stub_request_body(payload_bytes: bytes) -> None:
    """Install a one-shot request body that returns the given bytes."""

    class _Body:
        def __init__(self, data: bytes) -> None:
            self._data = data

        def read(self) -> bytes:
            return self._data

    cherrypy.request.body = _Body(payload_bytes)
    cherrypy.request.method = 'POST'
    # response.headers exists on the thread-local response; reset to a fresh
    # dict so the handler's Content-Type assignment doesn't bleed across tests.
    cherrypy.response.headers = {}
    # Some test paths read response.cookie even without setting it; provide one.
    import http.cookies

    cherrypy.response.cookie = http.cookies.SimpleCookie()


def test_archive_save_returns_stub_ok_for_valid_post(root: Root) -> None:
    import json

    _stub_request_body(b'{"name": "Test Character", "type": "samurai"}')
    body = root.archive(action='save').decode('utf-8')
    payload = json.loads(body)
    assert payload['ok'] is True
    assert 'stub' in payload['note'].lower()


def test_archive_save_handles_empty_body(root: Root) -> None:
    import json

    _stub_request_body(b'')
    payload = json.loads(root.archive(action='save').decode('utf-8'))
    assert payload['ok'] is True


def test_archive_save_returns_400_on_invalid_json(root: Root) -> None:
    _stub_request_body(b'{not valid json')
    with pytest.raises(cherrypy.HTTPError) as exc:
        root.archive(action='save')
    assert exc.value.status == 400


def test_archive_with_unknown_action_returns_404(root: Root) -> None:
    _stub_request_body(b'{}')
    with pytest.raises(cherrypy.HTTPError) as exc:
        root.archive(action='unknown')
    assert exc.value.status == 404


def test_archive_save_rejects_get(root: Root) -> None:
    _stub_request_body(b'{}')
    cherrypy.request.method = 'GET'
    with pytest.raises(cherrypy.HTTPError) as exc:
        root.archive(action='save')
    assert exc.value.status == 405


def test_load_secrets_returns_empty_dict_when_file_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from l7r import app as app_module

    # Point _HERE.parent at a directory with no development-secrets.ini.
    monkeypatch.setattr(app_module, '_HERE', tmp_path / 'nope')
    assert app_module._load_secrets() == {}


def test_resolve_default_pool_dir_uses_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    from l7r.app import _resolve_default_pool_dir

    monkeypatch.setenv('L7R_RELIC_POOL_DIR', '/some/where')
    assert _resolve_default_pool_dir() == Path('/some/where')


def test_resolve_default_pool_dir_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    from l7r.app import _resolve_default_pool_dir

    monkeypatch.delenv('L7R_RELIC_POOL_DIR', raising=False)
    result = _resolve_default_pool_dir()
    assert result.name == 'pool'


def test_resolve_default_names_dir_uses_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    from l7r.app import _resolve_default_names_dir

    monkeypatch.setenv('L7R_NAMES_DIR', '/some/names')
    assert _resolve_default_names_dir() == Path('/some/names')


def test_resolve_default_names_dir_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    from l7r.app import _resolve_default_names_dir

    monkeypatch.delenv('L7R_NAMES_DIR', raising=False)
    result = _resolve_default_names_dir()
    assert result.name == 'name'


def test_resolve_default_places_dir_uses_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    from l7r.app import _resolve_default_places_dir

    monkeypatch.setenv('L7R_PLACES_DIR', '/some/places')
    assert _resolve_default_places_dir() == Path('/some/places')


def test_resolve_default_places_dir_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    from l7r.app import _resolve_default_places_dir

    monkeypatch.delenv('L7R_PLACES_DIR', raising=False)
    result = _resolve_default_places_dir()
    assert result.name == 'place-names'


def _no_container_markers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force os.path.exists to report no container marker files.

    The test suite may itself run inside a container (podman/docker), so to
    isolate "is this code in a container?" branches we have to stub the
    marker-file checks rather than rely on the real filesystem.
    """
    import os

    real_exists = os.path.exists
    markers = {'/run/.containerenv', '/.dockerenv'}
    monkeypatch.setattr(os.path, 'exists', lambda p: False if p in markers else real_exists(p))


def test_apply_server_config_binds_for_fly(monkeypatch: pytest.MonkeyPatch) -> None:
    import cherrypy

    from l7r.app import _apply_server_config

    _no_container_markers(monkeypatch)
    monkeypatch.setenv('FLY_APP_NAME', 'l7r-gm-assistant')
    monkeypatch.setenv('PORT', '8080')
    cherrypy.config.update(
        {'server.socket_host': '127.0.0.1', 'server.socket_port': 9999, 'tools.proxy.on': False}
    )
    _apply_server_config()
    assert cherrypy.config['server.socket_host'] == '0.0.0.0'
    assert cherrypy.config['server.socket_port'] == 8080
    assert cherrypy.config['tools.proxy.on'] is True


def _force_marker(monkeypatch: pytest.MonkeyPatch, present: str) -> None:
    """Make only `present` return True for the two container marker files."""
    import os

    real_exists = os.path.exists
    markers = {'/run/.containerenv', '/.dockerenv'}
    monkeypatch.setattr(
        os.path,
        'exists',
        lambda p: True if p == present else (False if p in markers else real_exists(p)),
    )


def test_apply_server_config_binds_for_podman(monkeypatch: pytest.MonkeyPatch) -> None:
    import cherrypy

    from l7r.app import _apply_server_config

    monkeypatch.delenv('FLY_APP_NAME', raising=False)
    _force_marker(monkeypatch, '/run/.containerenv')
    cherrypy.config.update(
        {'server.socket_host': '127.0.0.1', 'server.socket_port': 9999, 'tools.proxy.on': False}
    )
    _apply_server_config()
    assert cherrypy.config['server.socket_host'] == '0.0.0.0'
    # Podman has no TLS-terminating proxy in front - proxy tool stays off.
    assert cherrypy.config['tools.proxy.on'] is False


def test_apply_server_config_binds_for_docker(monkeypatch: pytest.MonkeyPatch) -> None:
    import cherrypy

    from l7r.app import _apply_server_config

    monkeypatch.delenv('FLY_APP_NAME', raising=False)
    _force_marker(monkeypatch, '/.dockerenv')
    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    _apply_server_config()
    assert cherrypy.config['server.socket_host'] == '0.0.0.0'


def test_apply_server_config_noop_locally(monkeypatch: pytest.MonkeyPatch) -> None:
    import cherrypy

    from l7r.app import _apply_server_config

    _no_container_markers(monkeypatch)
    monkeypatch.delenv('FLY_APP_NAME', raising=False)
    cherrypy.config.update({'server.socket_host': '127.0.0.1', 'tools.proxy.on': False})
    _apply_server_config()
    assert cherrypy.config['server.socket_host'] == '127.0.0.1'
    assert cherrypy.config['tools.proxy.on'] is False


def test_mount_application_handles_missing_chargen(monkeypatch: pytest.MonkeyPatch) -> None:
    """If chargen.website cannot be imported, the call should still succeed."""
    import builtins
    import importlib
    from typing import Any

    from l7r import app as app_module

    real_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.startswith('chargen'):
            raise ImportError('chargen unavailable')
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', fake_import)
    monkeypatch.setattr(app_module, '_DEFAULT_POOL_DIR', Path('/nonexistent'))
    # Reload the cherrypy tree so mount succeeds cleanly.
    importlib.reload(app_module)

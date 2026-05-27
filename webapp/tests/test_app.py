"""Integration tests for the CherryPy Root.

These exercise the Root class directly — we do not stand up a real HTTP
server. CherryPy `expose`d methods are plain callables; we call them and
inspect the returned HTML bytes.
"""

from __future__ import annotations

from pathlib import Path

import cherrypy
import pytest

from l7r.app import Root, _error_page_handler, _group_relics_by_fortune, make_app
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


def test_relics_index_contains_relic_kanji(root: Root) -> None:
    html = root.relics().decode('utf-8')
    # The fixture relics' kanji should appear on the cards.
    assert '試の盃' in html
    assert '試の石' in html
    assert '試の刀' in html
    assert '試の槌' in html


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


def test_names_ignores_unknown_gender(root: Root) -> None:
    html = root.names(gender='other').decode('utf-8')
    assert '5 of 5' in html


def test_names_ignores_unknown_caste(root: Root) -> None:
    html = root.names(caste='nobility').decode('utf-8')
    assert '5 of 5' in html


def test_group_relics_by_fortune_has_all_fortune_keys(sample_pool_dir: Path) -> None:
    relics = load_relics(sample_pool_dir)
    grouped = _group_relics_by_fortune(relics)
    # All seven fortunes appear as keys, even if some have no relics.
    assert set(grouped.keys()) == {
        'benten',
        'bishamon',
        'daikoku',
        'ebisu',
        'fukurokujin',
        'hotei',
        'jurojin',
    }
    assert len(grouped['benten']) == 2
    assert len(grouped['daikoku']) == 0


def test_make_app_returns_root_with_relics() -> None:
    app = make_app(pool_dir=Path('/nonexistent'), names_dir=Path('/nonexistent'))
    assert isinstance(app, Root)
    assert app._relics == []
    assert app._names == []


def test_error_page_handler_renders_404_template() -> None:
    html = _error_page_handler(404, 'Not Found', '', 'cherrypy/0').decode('utf-8')
    assert '404' in html
    assert 'L7R' in html


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


def test_apply_server_config_binds_for_fly(monkeypatch: pytest.MonkeyPatch) -> None:
    import cherrypy

    from l7r.app import _apply_server_config

    monkeypatch.setenv('FLY_APP_NAME', 'l7r-gm-assistant')
    monkeypatch.setenv('PORT', '8080')
    # Reset to known state.
    cherrypy.config.update({'server.socket_host': '127.0.0.1', 'server.socket_port': 9999})
    _apply_server_config()
    assert cherrypy.config['server.socket_host'] == '0.0.0.0'
    assert cherrypy.config['server.socket_port'] == 8080


def test_apply_server_config_noop_locally(monkeypatch: pytest.MonkeyPatch) -> None:
    import cherrypy

    from l7r.app import _apply_server_config

    monkeypatch.delenv('FLY_APP_NAME', raising=False)
    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    _apply_server_config()
    assert cherrypy.config['server.socket_host'] == '127.0.0.1'


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

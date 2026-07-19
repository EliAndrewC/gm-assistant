"""Integration tests for the /dreams routes on the CherryPy Root."""

from __future__ import annotations

from pathlib import Path

import cherrypy
import pytest

from l7r.app import Root
from l7r.dreams import load_dream_scenes, render_markdown


@pytest.fixture
def dream_root(sample_dream_pool_dir: Path) -> Root:
    """A Root wired against the fixture dream pool (which has a sibling pool-local decoy)."""
    return Root(
        relics=[],
        dream_scenes=load_dream_scenes(sample_dream_pool_dir),
        dream_framework_html=render_markdown('## The framework\n\nSome player-facing prose.'),
    )


def test_dreams_index_renders_framework_and_gallery(dream_root: Root) -> None:
    html = dream_root.dreams().decode('utf-8')
    assert 'Dreams' in html
    assert 'The framework' in html  # the framework block is rendered
    assert 'Sample Daikoku Scene' in html  # a scene card is listed
    assert '/dreams/sample-daikoku-scene' in html


def test_dreams_appears_in_nav(dream_root: Root) -> None:
    html = dream_root.dreams().decode('utf-8')
    assert 'href="/dreams"' in html
    assert '>Dreams<' in html


def test_dreams_index_omits_pool_local_decoy(dream_root: Root) -> None:
    """FR-007 at the route level: the spoiler-tier decoy never appears."""
    html = dream_root.dreams().decode('utf-8')
    assert 'decoy-spoiler-scene' not in html
    assert 'Decoy Spoiler Scene' not in html


def test_dream_detail_renders_scene(dream_root: Root) -> None:
    html = dream_root.dreams(slug='sample-daikoku-scene').decode('utf-8')
    assert 'Sample Daikoku Scene' in html
    assert 'A dream-omen sought of' in html
    assert '<h2>A section</h2>' in html  # the scene body is rendered


def test_dream_detail_unknown_slug_returns_404(dream_root: Root) -> None:
    try:
        html = dream_root.dreams(slug='does-not-exist').decode('utf-8')
        assert 'not' in html.lower()
        assert cherrypy.response.status == 404
    finally:
        cherrypy.response.status = 200


def test_dream_detail_pool_local_slug_returns_404(dream_root: Root) -> None:
    """FR-007: a slug that exists only in the pool-local tier is not resolvable."""
    try:
        dream_root.dreams(slug='decoy-spoiler-scene')
        assert cherrypy.response.status == 404
    finally:
        cherrypy.response.status = 200


def test_dreams_index_empty_pool_shows_graceful_state() -> None:
    root = Root(relics=[], dream_scenes=[], dream_framework_html='')
    html = root.dreams().decode('utf-8')
    assert 'No worked examples yet' in html

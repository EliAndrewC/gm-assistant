"""Regression tests for the chargen view layer.

Background: ``chargen/templates/index.html`` and ``ministry.html`` inline
the full config dict into the page via ``{{ config|tojson }}`` so the
frontend JavaScript can build dropdowns from it. Before the fix being
guarded here, that included every section ConfigObj had merged in from
``development-secrets.ini`` - Gemini API key, Discord OAuth client secret,
Obsidian Portal session cookie, the ``[auth]`` HMAC key, and the
``[discord_whitelist]`` allowlist. Anyone with the URL could view-source
and read them. The view now filters those sections before serialization;
this test exists so a future view that bypasses the filter fails CI.

We also pin the index.html change that fixed the rank dropdown (it used to
read a nonexistent ``config.base_ranks`` and render empty).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from chargen import config
from chargen import website as chargen_website
from chargen.website import Root
from l7r.jinja_env import build_environment

# Sections this test treats as secret. Kept as a literal tuple here (not
# imported from chargen.website) so the assertions stay coupled to the
# *security boundary* - "these section names must not appear in rendered
# HTML" - rather than to the implementation symbol that enforces it. If
# development-secrets.ini gains a new section, add it here too.
_EXPECTED_SECRET_SECTIONS: tuple[str, ...] = (
    'auth',
    'discord',
    'discord_whitelist',
    'gemini',
    'gm_whitelist',
    'obsidian_portal',
)


@pytest.fixture(autouse=True)
def _shared_jinja_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # In production, ``l7r.app.run()`` swaps chargen's Jinja environment
    # for the shared ChoiceLoader so ``{% extends "_layout.html" %}``
    # resolves against ``l7r/templates/``. Mirror that here so the
    # templates render the same way they would for a real user.
    monkeypatch.setattr(chargen_website, 'jinja_env', build_environment())


def _string_leaves(value: object) -> Iterator[str]:
    """Yield every non-empty string anywhere inside a ConfigObj section."""
    if isinstance(value, str):
        if value:
            yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _string_leaves(v)
    elif isinstance(value, list):
        for v in value:
            yield from _string_leaves(v)


def _live_secret_values() -> list[str]:
    """Harvest live secret values from config at runtime.

    Pulling these from the parsed config means the test file itself
    contains no credentials, and the assertion still adapts to whatever
    the deployed ``development-secrets.ini`` actually holds.
    """
    out: list[str] = []
    for section in _EXPECTED_SECRET_SECTIONS:
        if section in config:
            out.extend(_string_leaves(config[section]))
    return out


def _render(method_name: str) -> str:
    # chargen is on the Principle X grace period - its return types are Any
    # to mypy, so the decode() result is Any too. Cast to str at the boundary.
    raw = getattr(Root(), method_name)()
    decoded: str = raw.decode('utf-8')
    return decoded


class TestRenderedHTMLDoesNotLeakSecrets:
    @pytest.fixture
    def index_html(self) -> str:
        return _render('index')

    @pytest.fixture
    def ministry_html(self) -> str:
        return _render('ministry')

    @pytest.mark.parametrize('section', _EXPECTED_SECRET_SECTIONS)
    def test_secret_section_key_absent_from_index(self, section: str, index_html: str) -> None:
        # The tojson serialization writes each section name as a quoted
        # JSON key, e.g. ``"discord":``. Checking the quoted form avoids
        # matching incidental occurrences of the bare word in markup.
        assert f'"{section}"' not in index_html, (
            f'secret section {section!r} appears in rendered index.html'
        )

    @pytest.mark.parametrize('section', _EXPECTED_SECRET_SECTIONS)
    def test_secret_section_key_absent_from_ministry(
        self, section: str, ministry_html: str
    ) -> None:
        assert f'"{section}"' not in ministry_html, (
            f'secret section {section!r} appears in rendered ministry.html'
        )

    def test_no_live_secret_value_appears_in_index(self, index_html: str) -> None:
        # Belt-and-suspenders: even if a future refactor renames a secret
        # section so the key-name check would pass, a live credential
        # value showing up in the page would still fail this assertion.
        for value in _live_secret_values():
            # Skip very short values - single tokens like "true" or short
            # numeric IDs would produce false positives against incidental
            # substrings in the markup. Real credentials are all longer.
            if len(value) >= 12:
                assert value not in index_html, (
                    'a live secret value from development-secrets.ini '
                    'appears in the rendered index.html'
                )

    def test_no_live_secret_value_appears_in_ministry(self, ministry_html: str) -> None:
        for value in _live_secret_values():
            if len(value) >= 12:
                assert value not in ministry_html, (
                    'a live secret value from development-secrets.ini '
                    'appears in the rendered ministry.html'
                )

    def test_template_still_has_non_secret_dropdown_data(self, index_html: str) -> None:
        # Sanity check on the filter going too far the other direction: if
        # someone accidentally over-filtered, the dropdowns wouldn't render
        # but the page would still come back 200. Pin the keys the
        # template depends on so over-filtering is caught here too.
        for key in ('"ranks"', '"clans"', '"clan"', '"family"', '"house"'):
            assert key in index_html, (
                f'expected dropdown data key {key} missing from rendered index.html'
            )


class TestRankDropdownWiring:
    def test_index_reads_config_ranks_not_base_ranks(self) -> None:
        # The dropdown used to read ``config.base_ranks`` (no such key in
        # any config file) and render empty. After the fix it cascades
        # off the type selector and reads ``config.ranks[type]``.
        html = _render('index')
        assert 'config.ranks' in html
        assert 'config.base_ranks' not in html

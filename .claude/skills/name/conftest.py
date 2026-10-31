"""Keep the picker tests off the live campaign roster.

``opcache.used_given_names`` grew two sources after these tests were written -
every character on the character-sheet app and every family / house / lineage
name (GM 2026-08-27) - and the tests, which point only the cache and extra
files at tmp paths, began reading the real roster: seven failed and the file
took 4.5 minutes (measured 2026-10-31, feature 232). The same tests also let
``pick()`` refresh the cache from Obsidian Portal - ~26 s a test, and the real
roster then overwrote the tmp one. This fixture points both new sources at
nothing and makes refreshing a no-op (a test that exercises refresh patches it
itself), so a test's roster is exactly what it wrote.
"""

import pytest

from similarity import is_too_similar  # noqa: F401  - puts webapp/ on sys.path

from chargen import opcache


@pytest.fixture(autouse=True)
def isolated_roster(tmp_path, monkeypatch):
    monkeypatch.setattr(opcache, "SHEET_USED_PATH", tmp_path / "no-sheet.json")
    monkeypatch.setattr(opcache, "LINEAGE_NAMES", lambda path: frozenset())
    monkeypatch.setattr(opcache, "_used_key", None)
    monkeypatch.setattr(opcache, "refresh_if_stale", lambda *a, **k: False)

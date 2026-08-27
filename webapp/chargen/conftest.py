"""chargen-wide fixtures: never let a test reach the character-sheet app."""

from pathlib import Path

import pytest

from chargen import opcache, sheetroster


@pytest.fixture(autouse=True)
def _offline_sheet_index(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse() -> str:
        raise RuntimeError('tests are offline: patch sheetroster.fetch_index')

    monkeypatch.setattr(sheetroster, 'fetch_index', refuse)


@pytest.fixture(autouse=True)
def _no_real_sheet_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Tests never read the real character-sheet roster cache; each gets an
    absent one (a test that wants names writes this path)."""
    monkeypatch.setattr(opcache, 'SHEET_USED_PATH', tmp_path / 'sheet-characters.json')
    monkeypatch.setattr(opcache, 'LINEAGE_NAMES', lambda path: frozenset())

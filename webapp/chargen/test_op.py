"""Boundary tests for the ``chargen.op`` additions used by the /synthesize skill.

``op`` is on the Principle X grace list (excluded from the coverage gate), so
these tests exist to validate behavior (Principle VI), not for coverage. The OP
transport is replaced by lightweight fakes fed from saved fixtures - no network,
no mocking of ``requests`` internals beyond the session seam op.py exposes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from chargen import op

_FIXTURES = Path(__file__).resolve().parent / 'fixtures'
_PAGE_HTML = (_FIXTURES / 'op_character_page.html').read_text(encoding='utf-8')
_CHARACTER_JSON = json.loads((_FIXTURES / 'op_character.json').read_text(encoding='utf-8'))


class _FakeResponse:
    def __init__(self, *, text: str = '', payload: object = None, raises: bool = False) -> None:
        self.text = text
        self._payload = payload
        self._raises = raises

    def raise_for_status(self) -> None:
        if self._raises:
            raise RuntimeError('HTTP 500')

    def json(self) -> object:
        return self._payload


class _FakeSession:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response

    def get(self, url: str, timeout: int = 0) -> _FakeResponse:
        return self._response


def test_fetch_character_page_returns_html_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        op, '_get_browser_session', lambda: _FakeSession(_FakeResponse(text=_PAGE_HTML))
    )
    html = op.fetch_character_page('https://example.test/characters/x')
    assert html is not None
    assert "class='tagline'" in html
    assert 'drinking companion of Kyoma' in html


def test_fetch_character_page_returns_none_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        op, '_get_browser_session', lambda: _FakeSession(_FakeResponse(raises=True))
    )
    assert op.fetch_character_page('https://example.test/characters/x') is None


def test_get_character_body_projects_description(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Api:
        def get(self, url: str, timeout: int = 0) -> _FakeResponse:
            return _FakeResponse(payload=_CHARACTER_JSON)

    monkeypatch.setattr(op, '_get_oauth_session', lambda: _Api())
    monkeypatch.setattr(op, '_get_campaign_id', lambda: 'camp')
    body = op.get_character_body('cid')
    assert body is not None
    assert body['description'] == _CHARACTER_JSON['description']
    assert body['game_master_info'] == _CHARACTER_JSON['game_master_info']

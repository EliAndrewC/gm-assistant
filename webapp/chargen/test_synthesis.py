"""Prompt-assembly tests and the Gemini synthesis boundary (fixture-replayed).

The external model call is exercised by substituting the client's
``generate_content`` with a stub that returns a SAVED REAL response (Principle
X.5: saved fixtures, not transport-layer mocks). ``build_prompt`` is tested with
no network at all.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from chargen import synthesis

_FIXTURE = Path(__file__).resolve().parent / 'fixtures' / 'synthesis_response.txt'
_CHAR = synthesis.SAMPLES[0]


def test_build_prompt_wraps_brief_and_character() -> None:
    prompt = synthesis.build_prompt(_CHAR, brief='SETTING BODY', extra_notes='')
    assert '# SETTING BRIEF' in prompt
    assert 'SETTING BODY' in prompt
    assert '# CHARACTER' in prompt
    assert str(_CHAR['full_name']) in prompt
    assert '# GM STEERING NOTES' not in prompt


def test_build_prompt_includes_steering_when_given() -> None:
    prompt = synthesis.build_prompt(_CHAR, brief='X', extra_notes='make her reluctant')
    assert '# GM STEERING NOTES' in prompt
    assert 'make her reluctant' in prompt


def test_build_prompt_omits_steering_when_blank() -> None:
    prompt = synthesis.build_prompt(_CHAR, brief='X', extra_notes='   ')
    assert '# GM STEERING NOTES' not in prompt


def test_format_character_includes_summary() -> None:
    out = synthesis.format_character(
        {'full_name': 'Suzume Hina', 'summary': 'Sparrow Clan ambassador to Shiro Reiji'}
    )
    assert 'Sparrow Clan ambassador to Shiro Reiji' in out


def test_format_character_includes_tags_from_comma_string() -> None:
    out = synthesis.format_character(
        {'full_name': 'X', 'public': 'p', 'tags': 'Wasp Clan, Escort, Shiro Reiji'}
    )
    assert 'Tags: Wasp Clan, Escort, Shiro Reiji' in out


def test_format_character_includes_tags_from_list() -> None:
    out = synthesis.format_character(
        {'full_name': 'X', 'public': 'p', 'tags': ['Crane Clan', 'Duelist']}
    )
    assert 'Tags: Crane Clan, Duelist' in out


class _StubResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class _StubModels:
    def __init__(self, text: str) -> None:
        self._text = text
        self.calls: list[dict[str, object]] = []

    def generate_content(self, *, model: str, contents: str) -> _StubResponse:
        self.calls.append({'model': model, 'contents': contents})
        return _StubResponse(self._text)


class _StubClient:
    def __init__(self, text: str) -> None:
        self.models = _StubModels(text)


def test_synthesize_returns_stripped_recorded_response(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded = _FIXTURE.read_text(encoding='utf-8')
    client = _StubClient(recorded)
    monkeypatch.setattr(synthesis, '_get_client', lambda: client)

    out = synthesis.synthesize(_CHAR, brief='small brief', model='gemini-3.1-pro-preview')

    assert out == recorded.strip()
    assert len(client.models.calls) == 1
    assert client.models.calls[0]['model'] == 'gemini-3.1-pro-preview'
    assert 'small brief' in str(client.models.calls[0]['contents'])

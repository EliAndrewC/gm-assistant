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


def test_build_prompt_inserts_campaign_context_between_brief_and_character() -> None:
    ctx = '# OTHER CAMPAIGN CHARACTERS\n\n## Grand Abbot\nStern and devout.'
    prompt = synthesis.build_prompt(_CHAR, brief='SETTING', campaign_context=ctx)
    assert '# OTHER CAMPAIGN CHARACTERS' in prompt
    assert 'Grand Abbot' in prompt
    # ordering: setting brief -> campaign characters -> the character being made
    assert prompt.index('# SETTING BRIEF') < prompt.index('# OTHER CAMPAIGN CHARACTERS')
    assert prompt.index('# OTHER CAMPAIGN CHARACTERS') < prompt.index('# CHARACTER')


def test_build_prompt_omits_campaign_section_when_empty() -> None:
    prompt = synthesis.build_prompt(_CHAR, brief='X', campaign_context='   ')
    assert '# OTHER CAMPAIGN CHARACTERS' not in prompt


def test_build_prompt_layers_all_blocks_stable_first() -> None:
    """The full 5-layer caching order: base corpus, snapshot cast, caste
    supplement, runtime cast additions, then the subject + steering."""
    prompt = synthesis.build_prompt(
        _CHAR,
        brief='SETTING',
        extra_notes='steer',
        campaign_context='# OTHER CAMPAIGN CHARACTERS\n\n## Old Abbot',
        caste_supplement='# SETTING BRIEF SUPPLEMENT\n\ntemple lore',
        campaign_context_recent='# OTHER CAMPAIGN CHARACTERS (RECENT ADDITIONS)\n\n## New Guard',
    )
    order = [
        prompt.index('# SETTING BRIEF'),
        prompt.index('# OTHER CAMPAIGN CHARACTERS\n'),
        prompt.index('# SETTING BRIEF SUPPLEMENT'),
        prompt.index('# OTHER CAMPAIGN CHARACTERS (RECENT ADDITIONS)'),
        prompt.index('# CHARACTER'),
        prompt.index('# GM STEERING NOTES'),
    ]
    assert order == sorted(order)


def test_build_prompt_omits_supplement_and_recent_when_blank() -> None:
    # The INSTRUCTIONS legitimately mention these sections by name; assert the
    # section headings themselves are absent.
    prompt = synthesis.build_prompt(
        _CHAR, brief='X', caste_supplement='  ', campaign_context_recent=''
    )
    assert '# SETTING BRIEF SUPPLEMENT' not in prompt
    assert '# OTHER CAMPAIGN CHARACTERS (RECENT ADDITIONS)' not in prompt


def test_instructions_ask_for_campaign_consistency() -> None:
    assert 'OTHER CAMPAIGN CHARACTERS' in synthesis.INSTRUCTIONS
    assert 'SETTING BRIEF SUPPLEMENT' in synthesis.INSTRUCTIONS


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


def test_synthesize_appends_supplement_for_monk_type(monkeypatch: pytest.MonkeyPatch) -> None:
    from chargen import brief as brief_mod

    client = _StubClient('prose')
    monkeypatch.setattr(synthesis, '_get_client', lambda: client)
    seen: list[str] = []

    def fake_supplement(character_type: str) -> str:
        seen.append(character_type)
        return '# SETTING BRIEF SUPPLEMENT\n\nTEMPLE LORE'

    monkeypatch.setattr(brief_mod, 'build_caste_supplement', fake_supplement)

    synthesis.synthesize(_CHAR, brief='B', model='m', character_type='Monk')

    assert seen == ['Monk']
    contents = str(client.models.calls[0]['contents'])
    assert 'TEMPLE LORE' in contents
    assert contents.index('# SETTING BRIEF SUPPLEMENT') < contents.index('# CHARACTER')


def test_synthesize_no_supplement_for_types_without_sections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # An unrecognized dropdown value has no caste sections; the real
    # build_caste_supplement returns '' before touching the corpus, so no
    # corpus is needed here.
    client = _StubClient('prose')
    monkeypatch.setattr(synthesis, '_get_client', lambda: client)

    synthesis.synthesize(_CHAR, brief='B', model='m', character_type='Ronin')

    assert '# SETTING BRIEF SUPPLEMENT' not in str(client.models.calls[0]['contents'])

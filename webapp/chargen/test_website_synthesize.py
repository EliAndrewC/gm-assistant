"""Envelope tests for the chargen ``synthesize`` AJAX route.

The route is thin glue over ``synthesis.synthesize`` (fixture-tested) and
``opcache.get_campaign_context`` (unit-tested). Both are substituted here to
assert the JSON envelope, the fail-loud model errors, and the fail-SOFT campaign
context (a context failure must not turn a good synthesis into an error).
"""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest

from chargen import opcache, synthesis, website


def _call(
    monkeypatch: pytest.MonkeyPatch,
    synth: Callable[..., str],
    *,
    context: tuple[str, str, int] = (
        '# OTHER CAMPAIGN CHARACTERS\n\n## Foo',
        '# OTHER CAMPAIGN CHARACTERS (RECENT ADDITIONS)\n\n## Bar',
        2,
    ),
    context_raises: bool = False,
    **char: str,
) -> dict[str, object]:
    monkeypatch.setattr(synthesis, 'synthesize', synth)
    if context_raises:

        def boom(*args: object, **kwargs: object) -> tuple[str, str, int]:
            raise RuntimeError('OP unreachable')

        monkeypatch.setattr(opcache, 'get_campaign_context', boom)
    else:
        monkeypatch.setattr(opcache, 'get_campaign_context', lambda *a, **k: context)
    result = website.Root().synthesize(extra_notes='', **char)
    data: dict[str, object] = json.loads(result)
    return data


def test_synthesize_returns_ok_envelope_with_context_count(monkeypatch: pytest.MonkeyPatch) -> None:
    out = _call(monkeypatch, lambda *a, **k: 'A grounded backstory.', full_name='Hideki')
    assert out['ok'] is True
    assert out['backstory'] == 'A grounded backstory.'
    assert out['error'] is None
    assert out['context_count'] == 2


def test_synthesize_passes_context_into_synthesis(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def synth(character: dict[str, object], **kwargs: object) -> str:
        seen.update(kwargs)
        return 'ok'

    _call(monkeypatch, synth, full_name='Hideki')
    assert 'OTHER CAMPAIGN CHARACTERS' in str(seen.get('campaign_context'))
    assert 'RECENT ADDITIONS' in str(seen.get('campaign_context_recent'))


def test_synthesize_pops_character_type_out_of_character_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}
    seen_char: dict[str, object] = {}

    def synth(character: dict[str, object], **kwargs: object) -> str:
        seen_char.update(character)
        seen.update(kwargs)
        return 'ok'

    _call(monkeypatch, synth, full_name='Kitsune', character_type='Monk')
    assert seen.get('character_type') == 'Monk'
    assert 'character_type' not in seen_char  # the dropdown value is routing, not character data


def test_synthesize_returns_error_envelope_on_model_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*args: object, **kwargs: object) -> str:
        raise RuntimeError('Gemini API key not configured.')

    out = _call(monkeypatch, boom, full_name='Hideki')
    assert out['ok'] is False
    assert out['backstory'] is None
    assert 'not configured' in str(out['error'])
    assert out['context_count'] == 2


def test_synthesize_reports_empty_output_as_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    out = _call(monkeypatch, lambda *a, **k: '', full_name='Hideki')
    assert out['ok'] is False
    assert 'empty' in str(out['error']).lower()


def test_synthesize_survives_context_gather_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    # OP down mid-gather: synthesis must still succeed with 0 context.
    out = _call(monkeypatch, lambda *a, **k: 'Still works.', context_raises=True, full_name='X')
    assert out['ok'] is True
    assert out['backstory'] == 'Still works.'
    assert out['context_count'] == 0

"""Envelope tests for the chargen ``synthesize`` AJAX route.

The route is thin glue over ``synthesis.synthesize`` (which is itself
fixture-tested). Here we substitute ``synthesize`` to assert the success and
failure JSON envelopes, including the fail-loud behavior (FR-010).
"""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest

from chargen import synthesis, website


def _call(
    monkeypatch: pytest.MonkeyPatch, synth: Callable[..., str], **char: str
) -> dict[str, object]:
    # website.py did `from chargen import synthesis`, so patching the module
    # object is seen by the route (same object).
    monkeypatch.setattr(synthesis, 'synthesize', synth)
    result = website.Root().synthesize(extra_notes='', **char)
    data: dict[str, object] = json.loads(result)
    return data


def test_synthesize_returns_ok_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    out = _call(monkeypatch, lambda *a, **k: 'A grounded backstory.', full_name='Hideki')
    assert out == {'ok': True, 'backstory': 'A grounded backstory.', 'error': None}


def test_synthesize_returns_error_envelope_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args: object, **kwargs: object) -> str:
        raise RuntimeError('Gemini API key not configured.')

    out = _call(monkeypatch, boom, full_name='Hideki')
    assert out['ok'] is False
    assert out['backstory'] is None
    assert 'not configured' in str(out['error'])


def test_synthesize_reports_empty_output_as_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    out = _call(monkeypatch, lambda *a, **k: '', full_name='Hideki')
    assert out['ok'] is False
    assert 'empty' in str(out['error']).lower()

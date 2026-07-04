"""Behavior tests for the campaign-character context cache (``chargen.opcache``).

The OP boundary is injected (fixture-shaped data / monkeypatched ``op`` module) -
no network, no transport mocks (Principle X.5).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from chargen import opcache

LIST: list[dict[str, object]] = [
    {'id': '1', 'name': 'Abbot', 'tags': ['Temple'], 'updated_at': '2026-01-01T00:00:00Z'},
    {'id': '2', 'name': 'Steward', 'tags': [], 'updated_at': '2026-01-02T00:00:00Z'},
]
BODIES: dict[str, dict[str, object]] = {
    '1': {
        'name': 'Abbot',
        'tags': ['Temple'],
        'bio': 'Public abbot bio.',
        'game_master_info': 'Secret abbot note.',
        'updated_at': '2026-01-01T00:00:00Z',
    },
    '2': {
        'name': 'Steward',
        'tags': [],
        'bio': '',
        'game_master_info': 'GM steward note.',
        'updated_at': '2026-01-02T00:00:00Z',
    },
}


def _list_fn() -> list[dict[str, object]]:
    return [dict(e) for e in LIST]


def _body_fn(cid: str) -> dict[str, object] | None:
    return BODIES.get(cid)


# --- _norm_ts ---


def test_norm_ts_treats_z_and_offset_as_equal() -> None:
    assert opcache._norm_ts('2026-01-01T00:00:00Z') == opcache._norm_ts('2026-01-01T00:00:00+00:00')


def test_norm_ts_empty_is_empty() -> None:
    assert opcache._norm_ts('') == ''


def test_norm_ts_falls_back_on_unparseable() -> None:
    assert opcache._norm_ts('not-a-date') == 'not-a-date'


# --- load_cache / save_cache ---


def test_load_cache_missing_file_returns_empty(tmp_path: Path) -> None:
    assert opcache.load_cache(tmp_path / 'nope.json') == {}


def test_load_cache_malformed_returns_empty(tmp_path: Path) -> None:
    p = tmp_path / 'c.json'
    p.write_text('{ not json', encoding='utf-8')
    assert opcache.load_cache(p) == {}


def test_load_cache_non_object_returns_empty(tmp_path: Path) -> None:
    p = tmp_path / 'c.json'
    p.write_text('[1, 2, 3]', encoding='utf-8')
    assert opcache.load_cache(p) == {}


def test_save_then_load_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / 'sub' / 'characters.json'
    opcache.save_cache({'1': {'name': 'X'}}, p)
    assert opcache.load_cache(p) == {'1': {'name': 'X'}}


# --- refresh ---


def test_refresh_fetches_new_entries() -> None:
    cache, stats = opcache.refresh({}, _list_fn, _body_fn)
    assert set(cache) == {'1', '2'}
    assert stats == {'fetched': 2, 'kept': 0, 'dropped': 0}
    assert cache['1']['bio'] == 'Public abbot bio.'


def test_refresh_keeps_unchanged_and_refetches_changed() -> None:
    base, _ = opcache.refresh({}, _list_fn, _body_fn)
    calls: list[str] = []

    def body_fn(cid: str) -> dict[str, object] | None:
        calls.append(cid)
        return BODIES.get(cid)

    changed = [dict(LIST[0]), {**LIST[1], 'updated_at': '2026-09-09T00:00:00Z'}]
    _, stats = opcache.refresh(base, lambda: changed, body_fn)
    assert calls == ['2']  # only the changed id is refetched
    assert stats == {'fetched': 1, 'kept': 1, 'dropped': 0}


def test_refresh_drops_deleted() -> None:
    base, _ = opcache.refresh({}, _list_fn, _body_fn)
    cache, stats = opcache.refresh(base, lambda: [dict(LIST[0])], _body_fn)
    assert set(cache) == {'1'}
    assert stats['dropped'] == 1


def test_refresh_body_failure_keeps_prior_but_skips_new() -> None:
    base, _ = opcache.refresh({}, _list_fn, _body_fn)
    lst: list[dict[str, object]] = [
        {**LIST[0], 'updated_at': 'changed'},  # existing, now "changed", body fails -> keep prior
        {'id': '3', 'name': 'New', 'tags': [], 'updated_at': 'x'},  # new, body fails -> skip
    ]
    cache, _ = opcache.refresh(base, lambda: lst, lambda cid: None)
    assert '1' in cache
    assert cache['1']['bio'] == 'Public abbot bio.'
    assert '3' not in cache


def test_refresh_ignores_entries_without_id() -> None:
    cache, _ = opcache.refresh({}, lambda: [{'name': 'no id'}], _body_fn)
    assert cache == {}


def test_refresh_preserves_prior_order_when_op_listing_reorders() -> None:
    """Prompt-prefix caching contract: established entries keep their cache
    order even when the OP listing comes back reshuffled."""
    base, _ = opcache.refresh({}, _list_fn, _body_fn)
    assert list(base) == ['1', '2']
    reordered = [dict(LIST[1]), dict(LIST[0])]
    cache, stats = opcache.refresh(base, lambda: reordered, _body_fn)
    assert list(cache) == ['1', '2']
    assert stats == {'fetched': 0, 'kept': 2, 'dropped': 0}


def test_refresh_appends_new_ids_at_the_end() -> None:
    """New characters join at the tail of the block, even when the OP listing
    puts them first."""
    base, _ = opcache.refresh({}, _list_fn, _body_fn)

    def body_fn(cid: str) -> dict[str, object] | None:
        return BODIES.get(cid, {'bio': 'new bio', 'game_master_info': '', 'updated_at': 'x'})

    lst: list[dict[str, object]] = [
        {'id': '9', 'name': 'Newest', 'tags': [], 'updated_at': 'x'},
        dict(LIST[1]),
        dict(LIST[0]),
        {'id': '8', 'name': 'Newer', 'tags': [], 'updated_at': 'x'},
    ]
    cache, stats = opcache.refresh(base, lambda: lst, body_fn)
    assert list(cache) == ['1', '2', '9', '8']  # priors in order, new appended in list order
    assert stats == {'fetched': 2, 'kept': 2, 'dropped': 0}


def test_refresh_changed_entry_keeps_its_position() -> None:
    base, _ = opcache.refresh({}, _list_fn, _body_fn)
    changed = [{**LIST[1], 'updated_at': '2026-09-09T00:00:00Z'}, dict(LIST[0])]
    cache, _ = opcache.refresh(base, lambda: changed, _body_fn)
    assert list(cache) == ['1', '2']


def test_refresh_falls_back_to_list_name_when_body_lacks_it() -> None:
    lst: list[dict[str, object]] = [
        {'id': '7', 'name': 'FromList', 'tags': ['t'], 'updated_at': 'a'}
    ]

    def body_fn(cid: str) -> dict[str, object] | None:
        return {'bio': 'b', 'game_master_info': '', 'updated_at': 'a'}  # no name/tags

    cache, _ = opcache.refresh({}, lambda: lst, body_fn)
    assert cache['7']['name'] == 'FromList'
    assert cache['7']['tags'] == ['t']


# --- assemble_context ---


def test_assemble_context_formats_and_counts() -> None:
    cache, _ = opcache.refresh({}, _list_fn, _body_fn)
    text, count = opcache.assemble_context(cache)
    assert count == 2
    assert text.startswith('# OTHER CAMPAIGN CHARACTERS')
    assert '## Abbot' in text
    assert 'Tags: Temple' in text
    assert 'Public abbot bio.' in text
    assert 'GM steward note.' in text


def test_assemble_context_excludes_by_name_case_insensitive() -> None:
    cache, _ = opcache.refresh({}, _list_fn, _body_fn)
    text, count = opcache.assemble_context(cache, exclude_name='  ABBOT ')
    assert count == 1
    assert '## Abbot' not in text


def test_assemble_context_empty_when_no_cache() -> None:
    assert opcache.assemble_context({}) == ('', 0)


def test_assemble_context_skips_bodyless_entries() -> None:
    cache: dict[str, dict[str, object]] = {
        '9': {'name': 'Empty', 'tags': ['x'], 'bio': '', 'game_master_info': ''}
    }
    assert opcache.assemble_context(cache) == ('', 0)


def test_assemble_context_filters_by_ids_and_uses_heading() -> None:
    cache, _ = opcache.refresh({}, _list_fn, _body_fn)
    text, count = opcache.assemble_context(cache, ids=frozenset({'2'}), heading='# RECENT')
    assert count == 1
    assert text.startswith('# RECENT')
    assert '## Steward' in text
    assert '## Abbot' not in text


def test_assemble_context_empty_ids_filter_yields_empty() -> None:
    cache, _ = opcache.refresh({}, _list_fn, _body_fn)
    assert opcache.assemble_context(cache, ids=frozenset()) == ('', 0)


# --- get_campaign_context (TTL) ---


def test_get_campaign_context_refreshes_then_reuses_within_ttl(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from chargen import op

    monkeypatch.setattr(op, 'existing_characters', _list_fn)
    monkeypatch.setattr(op, 'get_character_body', _body_fn)
    monkeypatch.setattr(opcache, '_CACHE_PATH', tmp_path / 'characters.json')
    monkeypatch.setattr(opcache, '_cache', None)
    monkeypatch.setattr(opcache, '_assembled_at', None)
    monkeypatch.setattr(opcache, '_baseline_ids', None)

    calls = {'n': 0}
    real_refresh = opcache.refresh

    def counting(
        *args: object, **kwargs: object
    ) -> tuple[dict[str, opcache.JsonObj], dict[str, int]]:
        calls['n'] += 1
        return real_refresh(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(opcache, 'refresh', counting)

    _, _, count = opcache.get_campaign_context(now=1000.0)
    assert count == 2
    assert calls['n'] == 1

    opcache.get_campaign_context(now=1000.0 + opcache._TTL_SECONDS - 1)
    assert calls['n'] == 1  # within TTL: reused, no refresh

    opcache.get_campaign_context(now=1000.0 + opcache._TTL_SECONDS + 1)
    assert calls['n'] == 2  # past TTL: refreshed again


def test_get_campaign_context_default_now_uses_clock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from chargen import op

    monkeypatch.setattr(op, 'existing_characters', _list_fn)
    monkeypatch.setattr(op, 'get_character_body', _body_fn)
    monkeypatch.setattr(opcache, '_CACHE_PATH', tmp_path / 'characters.json')
    monkeypatch.setattr(opcache, '_cache', None)
    monkeypatch.setattr(opcache, '_assembled_at', None)
    monkeypatch.setattr(opcache, '_baseline_ids', None)
    snapshot, recent, count = opcache.get_campaign_context()  # now=None -> time.monotonic()
    assert count == 2
    # No cache file at process start -> empty baseline; everything the first
    # refresh discovers is a runtime addition.
    assert snapshot == ''
    assert recent.startswith('# OTHER CAMPAIGN CHARACTERS (RECENT ADDITIONS)')


def test_get_campaign_context_splits_snapshot_from_runtime_discoveries(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The process-start cache file is the layer-2/layer-4 boundary: bundled
    characters render in the stable block, later discoveries in the recent one."""
    from chargen import op

    path = tmp_path / 'characters.json'
    seeded, _ = opcache.refresh({}, lambda: [dict(LIST[0])], _body_fn)  # only Abbot on disk
    opcache.save_cache(seeded, path)

    monkeypatch.setattr(op, 'existing_characters', _list_fn)  # OP now also has Steward
    monkeypatch.setattr(op, 'get_character_body', _body_fn)
    monkeypatch.setattr(opcache, '_CACHE_PATH', path)
    monkeypatch.setattr(opcache, '_cache', None)
    monkeypatch.setattr(opcache, '_assembled_at', None)
    monkeypatch.setattr(opcache, '_baseline_ids', None)

    snapshot, recent, count = opcache.get_campaign_context(now=1000.0)
    assert count == 2
    assert snapshot.startswith('# OTHER CAMPAIGN CHARACTERS')
    assert '## Abbot' in snapshot
    assert '## Steward' not in snapshot
    assert recent.startswith('# OTHER CAMPAIGN CHARACTERS (RECENT ADDITIONS)')
    assert '## Steward' in recent
    assert '## Abbot' not in recent


# --- refresh_cache_file ---


def test_refresh_cache_file_writes_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from chargen import op

    monkeypatch.setattr(op, 'existing_characters', _list_fn)
    monkeypatch.setattr(op, 'get_character_body', _body_fn)
    p = tmp_path / 'characters.json'
    stats = opcache.refresh_cache_file(p)
    assert stats['fetched'] == 2
    assert set(opcache.load_cache(p)) == {'1', '2'}

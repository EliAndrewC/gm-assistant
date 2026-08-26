"""Campaign-character context cache for backstory synthesis.

Maintains an id-keyed cache of the campaign's characters (from Obsidian Portal)
so a synthesized backstory can stay consistent with the existing cast and honor
steering-note references to them. Refreshing is incremental: one OP list call
gives every character's ``updated_at``; a full body is fetched only for ids that
are new or changed, and ids no longer present are dropped.

The cache is a gitignored artifact (``webapp/opcache/characters.json``): refreshed
and bundled at ``make prepare-deploy`` as a cold-start base, and refreshed
in-memory at runtime with a short TTL. Gathering context is non-fatal - if OP is
unreachable the cache simply stays as-is (possibly empty) and synthesis proceeds
without campaign context (unlike the setting corpus, which fails loud).

The OP calls are the external boundary and live in the grace-listed ``op.py``
(fail-soft: they return ``[]`` / ``None`` on failure, never raise), so this
module stays free of broad excepts and is unit-tested against injected fetchers.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

#: One character entry / a raw OP object: heterogeneous string-keyed mapping.
JsonObj = dict[str, object]

_OPCACHE_DIR = Path(__file__).resolve().parent.parent / 'opcache'
_CACHE_PATH = _OPCACHE_DIR / 'characters.json'

#: Runtime refresh cadence - re-rolls within this window reuse the cache.
_TTL_SECONDS = 60.0

#: In-memory runtime state (per process instance).
_cache: dict[str, JsonObj] | None = None
_assembled_at: float | None = None

#: Ids present in the cache file at process start (the deploy-time snapshot).
#: This is the deterministic boundary between the two cast blocks in the
#: prompt: snapshot characters render in the stable block right after the
#: corpus; ids discovered by runtime refreshes render in a second block placed
#: AFTER the caste supplement, so mid-session roster additions perturb only the
#: prompt's tail (implicit prefix caching). Resets naturally at each deploy,
#: when the re-bundled cache file absorbs everything.
_baseline_ids: frozenset[str] | None = None


def _norm_ts(ts: str) -> str:
    """Normalize an OP timestamp for comparison (the list gives ``...Z``, bodies
    may give a numeric offset; both should compare equal)."""
    if not ts:
        return ''
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00')).astimezone().isoformat()
    except ValueError:
        return ts


def _s(obj: JsonObj, key: str) -> str:
    """Read a string field, coercing missing/non-string to ''."""
    value = obj.get(key)
    return value if isinstance(value, str) else ''


def _as_tags(value: object) -> list[str]:
    """Coerce a tags value to a list of strings."""
    return [str(t) for t in value] if isinstance(value, list) else []


def load_cache(path: Path = _CACHE_PATH) -> dict[str, JsonObj]:
    """Read the JSON cache; return ``{}`` for a missing/malformed/non-object file
    (logged) so a bad cache never blocks synthesis."""
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning('opcache: could not read cache %s: %s', path, e)
        return {}
    if not isinstance(data, dict):
        logger.warning('opcache: cache file %s is not an object; ignoring', path)
        return {}
    return data


def save_cache(cache: dict[str, JsonObj], path: Path = _CACHE_PATH) -> None:
    """Write the JSON cache atomically (temp file + rename), creating the
    parent directory if needed.

    Atomic because the file now has concurrent readers (feature 200, FR-014):
    the skill picker and the chargen engine derive the used-name set from it,
    and a reader that saw a half-written file would get an EMPTY roster - every
    name would look free. With rename, a reader sees the old file or the new."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def cache_age(path: Path = _CACHE_PATH) -> float | None:
    """Seconds since the cache file was last written; ``None`` if absent."""
    try:
        return max(0.0, time.time() - path.stat().st_mtime)
    except FileNotFoundError:
        return None


def refresh_if_stale(max_age_seconds: float = 3600.0, path: Path = _CACHE_PATH) -> bool:
    """Reconcile the cache file against Obsidian Portal if it is missing or
    older than ``max_age_seconds``. Returns True when a refresh was written.

    Fail-soft, and one guard beyond ``refresh_cache_file``: an EMPTY listing
    is treated as an OP failure (the OAuth helpers return ``[]`` on any error -
    missing credentials included) and nothing is written - otherwise an outage
    would wipe the roster, or (measured 2026-08-25 in a clone with no secrets
    file) write an empty cache that then looks FRESH for an hour, and every
    name would look unused. The file is deliberately left alone so the next
    call retries."""
    from chargen import op

    age = cache_age(path)
    if age is not None and age < max_age_seconds:
        return False
    cache = load_cache(path)
    list_fn: Callable[[], list[JsonObj]] = op.existing_characters
    entries = list_fn()
    if not entries:
        logger.warning('opcache: empty listing from OP; keeping %d cached entries', len(cache))
        return False
    new_cache, stats = refresh(cache, lambda: entries, op.get_character_body)
    save_cache(new_cache, path)
    logger.info('opcache: refreshed %s (%s)', path, stats)
    return True


#: Names in use that Obsidian Portal cannot tell us about (a PC with no OP
#: record, a name the GM has promised to someone). One name per line, ``#``
#: comments allowed. Tracked in git, next to the pool, because it is the
#: campaign's overlay on a campaign-agnostic pool: the pool is NEVER depleted
#: by use (GM 2026-08-26) - a name picked for this campaign stays in the pool
#: for the next one, and exclusion happens here and in the roster cache.
#: Resolved like ``namepool.pool_dir``: the deploy bundle ``webapp/skills/name``
#: when present (the image has no ``.claude/``), else the skill dir in the repo.
_EXTRA_BUNDLED = _OPCACHE_DIR.parent / 'skills' / 'name' / 'used-names-extra.txt'
EXTRA_USED_PATH = (
    _EXTRA_BUNDLED
    if _EXTRA_BUNDLED.is_file()
    else _OPCACHE_DIR.parent.parent / '.claude' / 'skills' / 'name' / 'used-names-extra.txt'
)

_used_key: tuple[tuple[Path, int, int] | None, ...] | None = None
_used_names: frozenset[str] = frozenset()


def _stat_key(path: Path) -> tuple[Path, int, int] | None:
    try:
        st = path.stat()
    except FileNotFoundError:
        return None
    return (path, st.st_mtime_ns, st.st_size)


def used_given_names(path: Path = _CACHE_PATH, extra: Path | None = None) -> frozenset[str]:
    """Given names in use in this campaign: the last whitespace token of each
    roster character's full name from the cache (feature 200, FR-002:
    ``Bayushi no Daika Bokuden`` -> ``Bokuden``; a mononym is itself), plus the
    names listed in ``extra`` (see :data:`EXTRA_USED_PATH`). Memoized on both
    files' identity/mtime/size so the engine can call this per character at no
    cost. A missing cache contributes nothing; a missing extra file likewise."""
    global _used_key, _used_names
    if extra is None:
        extra = EXTRA_USED_PATH  # resolved at call time so tests can point it elsewhere
    key = (_stat_key(path), _stat_key(extra))
    if key != _used_key:
        names: set[str] = set()
        if key[0] is not None:
            for entry in load_cache(path).values():
                parts = _s(entry, 'name').split()
                if parts:
                    names.add(parts[-1])
        if key[1] is not None:
            for line in extra.read_text(encoding='utf-8').splitlines():
                word = line.split('#', 1)[0].strip()
                if word:
                    names.add(word)
        _used_names = frozenset(names)
        _used_key = key
    return _used_names


def refresh(
    cache: dict[str, JsonObj],
    list_fn: Callable[[], list[JsonObj]],
    body_fn: Callable[[str], JsonObj | None],
) -> tuple[dict[str, JsonObj], dict[str, int]]:
    """Return ``(new_cache, stats)``. Fetch a body only for ids that are new or
    whose ``updated_at`` changed; keep unchanged ids; drop ids absent from the
    list. A ``body_fn`` returning ``None`` (fetch failed) keeps the prior entry
    if there is one, else skips that id.

    Ordering is a caching contract, not cosmetics: the assembled cast block sits
    mid-prompt, and Gemini's implicit prefix caching only discounts tokens up to
    the first point of divergence - so a reshuffled block invalidates the cache
    for everything after it. Prior entries therefore keep their existing cache
    order (regardless of how OP happens to order its listing), and new ids are
    appended at the end, where they perturb the smallest possible suffix."""
    entries = list_fn() or []
    listed: dict[str, JsonObj] = {}
    for entry in entries:
        raw_id = entry.get('id')
        if raw_id:
            listed[str(raw_id)] = entry
    new_cache: dict[str, JsonObj] = {}
    fetched = kept = 0

    def _resolve(cid: str, entry: JsonObj) -> None:
        nonlocal fetched, kept
        prior = cache.get(cid)
        list_ts = _s(entry, 'updated_at')
        if prior is not None and _norm_ts(_s(prior, 'updated_at')) == _norm_ts(list_ts):
            new_cache[cid] = prior
            kept += 1
            return
        body = body_fn(cid)
        if body is None:
            if prior is not None:
                new_cache[cid] = prior
                kept += 1
            return
        new_cache[cid] = {
            'updated_at': _s(body, 'updated_at') or list_ts,
            'name': _s(body, 'name') or _s(entry, 'name'),
            'tags': _as_tags(body.get('tags')) or _as_tags(entry.get('tags')),
            'bio': _s(body, 'bio'),
            'game_master_info': _s(body, 'game_master_info'),
        }
        fetched += 1

    for cid in cache:  # existing ids first, in their established order
        if cid in listed:
            _resolve(cid, listed[cid])
    for cid, entry in listed.items():  # then new ids, appended at the end
        if cid not in cache:
            _resolve(cid, entry)
    dropped = sum(1 for cid in cache if cid not in new_cache)
    return new_cache, {'fetched': fetched, 'kept': kept, 'dropped': dropped}


def assemble_context(
    cache: dict[str, JsonObj],
    exclude_name: str | None = None,
    ids: frozenset[str] | None = None,
    heading: str = '# OTHER CAMPAIGN CHARACTERS',
) -> tuple[str, int]:
    """Assemble a campaign-characters prompt block, excluding a character by
    (case-insensitive) name. ``ids`` restricts the block to those cache ids
    (``None`` = all); ``heading`` titles the block. Returns ``(text, count)``;
    characters with no bio and no GM notes are omitted; empty -> ``('', 0)``."""
    excluded = (exclude_name or '').strip().lower()
    parts: list[str] = []
    for cid, entry in cache.items():
        if ids is not None and cid not in ids:
            continue
        name = _s(entry, 'name').strip()
        if excluded and name.lower() == excluded:
            continue
        bio = _s(entry, 'bio').strip()
        gm_info = _s(entry, 'game_master_info').strip()
        if not bio and not gm_info:
            continue
        block = [f'## {name}'.rstrip()]
        tags = _as_tags(entry.get('tags'))
        if tags:
            block.append('Tags: ' + ', '.join(tags))
        if bio:
            block.append(bio)
        if gm_info:
            block.append(gm_info)
        parts.append('\n'.join(block))
    if not parts:
        return '', 0
    return heading + '\n\n' + '\n\n'.join(parts), len(parts)


def get_campaign_context(
    exclude_name: str | None = None, *, now: float | None = None
) -> tuple[str, str, int]:
    """Return ``(snapshot_block, recent_block, count)`` for the prompt,
    TTL-guarded in memory.

    ``snapshot_block`` holds the characters present at process start (stable
    across the process lifetime, prompt-cache friendly); ``recent_block`` holds
    ids discovered by runtime refreshes since (appended near the prompt's end).
    ``count`` covers both. Loads the bundled cache as a base on first use,
    refreshes against OP no more than once per TTL window, and never raises -
    OP failure leaves the held cache (possibly empty) in place."""
    global _cache, _assembled_at, _baseline_ids
    import time

    from chargen import op

    moment = now if now is not None else time.monotonic()
    if _cache is None:
        # Read _CACHE_PATH at call time (not via load_cache's import-time
        # default) so path overrides in tests take effect.
        _cache = load_cache(_CACHE_PATH)
    if _baseline_ids is None:
        _baseline_ids = frozenset(_cache)
    if _assembled_at is None or (moment - _assembled_at) >= _TTL_SECONDS:
        _cache, _ = refresh(_cache, op.existing_characters, op.get_character_body)
        _assembled_at = moment
    recent_ids = frozenset(cid for cid in _cache if cid not in _baseline_ids)
    snapshot, n_snapshot = assemble_context(_cache, exclude_name, ids=_baseline_ids)
    recent, n_recent = assemble_context(
        _cache,
        exclude_name,
        ids=recent_ids,
        heading='# OTHER CAMPAIGN CHARACTERS (RECENT ADDITIONS)',
    )
    return snapshot, recent, n_snapshot + n_recent


def refresh_cache_file(path: Path = _CACHE_PATH) -> dict[str, int]:
    """Build-time refresh: load the file, refresh against OP, write it back.
    Called by ``make prepare-deploy``. First run = full pull; later = incremental."""
    from chargen import op

    cache = load_cache(path)
    new_cache, stats = refresh(cache, op.existing_characters, op.get_character_body)
    save_cache(new_cache, path)
    logger.info('opcache: refreshed %s (%s)', path, stats)
    return stats

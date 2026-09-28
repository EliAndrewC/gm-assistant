"""Name suggestions for the character-sheet app's generated NPCs (feature 213).

The sheet's combat tracker generates NPCs and asks ``GET /api/names`` for their names, because
the used-name set - the Obsidian Portal roster, the GM's manual list, the lineage names, the
sheet's own characters and NPCs - is assembled only here (``opcache.used_given_names``). The GM's
rules, from the sheet repository's ``combat-design/design.md``: the pool with the used-name and
within-batch rules (D10), male only (D16), Wave Men from the peasant pool and samurai-school NPCs
a samurai-eligible given name only (D26), and the cache refreshed when stale (4.6).

This module holds the parsing, the token check, the batch and the refresh; ``l7r.app`` holds
the HTTP handler. ``chargen`` is imported inside the functions, never at module level, because
``l7r.app`` must still import when ``chargen`` does not (see
``test_mount_application_handles_missing_chargen``).
"""

from __future__ import annotations

import hmac
import logging
import random as _random
import threading
from collections.abc import Mapping, Sequence

from l7r.names import GeneratedName

logger = logging.getLogger(__name__)

#: The largest batch one request may ask for. A fight bigger than this is not a thing the GM
#: runs, and the within-batch rule (no two names sharing a first letter) runs dry near 26 anyway.
MAX_COUNT = 30

#: Refresh the used-name cache when it is older than this: ``opcache.refresh_if_stale``'s own
#: default window. See spec 213 Decision 1 for why the request WAITS for the refresh.
MAX_AGE = 3600.0

#: Serializes refreshes within this process, so two NPC batches requested together do not both
#: walk Obsidian Portal; the second waits, then finds the cache fresh. The REPL keeps its own
#: lock (``l7r.repl.names``) - a different process, so sharing the object would buy nothing.
_refresh_lock = threading.Lock()


def parse_count(raw: str | None) -> int:
    """``count``: absent means 1; clamped to 1..MAX_COUNT; a non-integer raises ``ValueError``."""
    if raw is None:
        return 1
    return max(1, min(MAX_COUNT, int(raw)))


def parse_peasant(raw: str | None) -> bool:
    """``peasant``: absent or ``false`` is False, ``true`` is True; anything else raises."""
    if raw is None or raw.lower() == 'false':
        return False
    if raw.lower() == 'true':
        return True
    raise ValueError(f'peasant must be true or false, not {raw!r}')


def parse_avoid(raw: str | Sequence[str] | None) -> list[str]:
    """``avoid``: comma-separated (or repeated) names; stripped, empties dropped."""
    if raw is None:
        return []
    parts = [raw] if isinstance(raw, str) else list(raw)
    return [name.strip() for part in parts for name in part.split(',') if name.strip()]


def token_matches(header: str, configured: str) -> bool:
    """True when ``header`` is ``Bearer <configured>``. Constant-time over UTF-8 bytes, so a
    non-ASCII header is a mismatch rather than a ``TypeError``."""
    scheme, _, presented = header.partition(' ')
    if scheme.lower() != 'bearer':
        return False
    return hmac.compare_digest(presented.strip().encode(), configured.encode())


def suggest_names(
    count: int,
    *,
    peasant: bool,
    pool: Mapping[str, Sequence[GeneratedName]],
    used: frozenset[str],
    avoid: Sequence[str] = (),
    rng: _random.Random | None = None,
) -> list[str]:
    """Up to ``count`` male given names, built the way ``l7r.repl.names.names`` builds a batch:
    each pick excludes the used names (and names too similar to them) and is set-distinct from
    ``avoid`` and the picks before it. Fewer when the pool runs out.

    The caste set is filtered HERE and handed to ``pick_name`` with ``peasant=None``, deliberately
    not ``pick_name(peasant=False)``: that mode falls back to the WHOLE pool once the
    samurai-eligible names are exhausted, and D26 says a samurai-school NPC gets a
    samurai-eligible name ONLY (spec 213 FR-004, the fidelity review's round-1 finding).
    """
    from chargen import namepool

    male = tuple(pool.get('male', ()))
    if peasant:
        eligible = tuple(e for e in male if e.peasant)
    else:
        eligible = tuple(e for e in male if not e.peasant or e.samurai)
    caste_pool = {'male': eligible}
    picks: list[str] = []
    for _ in range(count):
        try:
            chosen = namepool.pick_name('male', caste_pool, used, [*avoid, *picks], rng=rng)
        except namepool.NamePoolExhausted:
            break
        picks.append(chosen.name)
    return picks


def refresh_used_names() -> bool:
    """Refresh the used-name cache if stale; True when it ran without raising.

    Synchronous on purpose (spec 213 Decision 1): 4.6 says the endpoint refreshes a stale cache,
    and on a cold boot the cache on disk is the deploy-time one, weeks old. A refresh that FAILS
    (Obsidian Portal or the sheet unreachable) is logged and the batch is picked against the last
    cache - a failure must never become an error response.
    """
    from chargen import opcache

    with _refresh_lock:
        try:
            opcache.refresh_if_stale(MAX_AGE)
        except Exception:  # network boundary: report, never fail the request
            logger.exception('sheetnames: used-name refresh failed; using the last cache')
            return False
    return True

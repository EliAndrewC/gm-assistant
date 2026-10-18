"""Who sees the shrine ledger's costs (FR-048, spec amendment 9).

The GM always does. So does a logged-in player who OWNS a character on the character-sheet app
that is in a gaming group and has the Commerce skill: both apps log in through Discord, and the
sheet's `GET /api/characters` lists each character's owner Discord id, group and skills. Such a
player sees the ledger read-only; its inputs stay the GM's (the template's `is_gm`).

Fails closed: no token, the sheet app down, a bad payload - nobody but the GM sees costs, and the
page still renders. The roster is cached (`TTL`) because the sheet app auto-stops on Fly and a
cold start would otherwise stall every page view; a failure is cached for `FAILURE_TTL` so an
outage costs one slow request a minute, not one per view.

The fetch is a few lines of urllib rather than `l7r.repl.rolls.sheet`, which wraps the same
endpoint: importing that package pulls in the whole REPL and `chargen` (2.8 s measured), which
the web process deliberately does not load at module level.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any

__all__ = ['CostAccess', 'commerce_owners', 'fetch_roster']

logger = logging.getLogger(__name__)

ROSTER_URL = 'https://l7r-character-sheet.fly.dev/api/characters'
SKILL = 'commerce'
TTL = 600.0
FAILURE_TTL = 60.0
TIMEOUT = 8.0


def commerce_owners(payload: Mapping[str, Any]) -> frozenset[str]:
    """Discord ids owning a grouped, non-NPC character with Commerce at rank 1 or more.

    Owner only: a character someone may merely edit is not theirs. A combat-tracker NPC has no
    gaming group, but `is_npc` is checked too so the rule never rests on that alone.
    """
    owners = set()
    for entry in payload.get('characters') or ():
        owner = str(entry.get('owner_discord_id') or '')
        grouped = entry.get('gaming_group_id') is not None
        rank = int((entry.get('skills') or {}).get(SKILL) or 0)
        if owner and grouped and not entry.get('is_npc') and rank >= 1:
            owners.add(owner)
    return frozenset(owners)


def fetch_roster(token: str) -> Any:  # pragma: no cover - the HTTP boundary
    request = urllib.request.Request(ROSTER_URL, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.load(response)


class CostAccess:
    """`allows(discord_id)`: may this non-GM viewer see the costs? Cached, thread-safe."""

    def __init__(
        self,
        token: Callable[[], str],
        fetch: Callable[[str], Any] = fetch_roster,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._token = token
        self._fetch = fetch
        self._clock = clock
        self._owners: frozenset[str] = frozenset()
        self._expires = float('-inf')
        self._lock = threading.Lock()

    def allows(self, discord_id: str) -> bool:
        return discord_id in self._current()

    def _current(self) -> frozenset[str]:
        # Held across the fetch, so concurrent page views wait for one fetch instead of each
        # making their own.
        with self._lock:
            now = self._clock()
            if now < self._expires:
                return self._owners
            token = self._token()
            if not token:
                logger.warning('shrine costs: no [character_sheet] roll_query_token; GM only')
                self._owners, self._expires = frozenset(), now + TTL
                return self._owners
            try:
                self._owners, self._expires = commerce_owners(self._fetch(token)), now + TTL
            except Exception as exc:  # noqa: BLE001 - every failure fails closed the same way
                logger.warning('shrine costs: character-sheet roster unavailable: %s', exc)
                self._owners, self._expires = frozenset(), now + FAILURE_TTL
            return self._owners

"""Client for the character-sheet app's roll-history endpoints.

**THESE ENDPOINTS DO NOT EXIST YET.** They are specified in the character-sheet
repository at `externally-queryable-roll-results.md`, written for a session in
that container to implement. This module is the whole of the dependency, so the
rest of the feature does not know or care whether they are there.

WHY THE ENDPOINT EXISTS AT ALL. The dice card a player pastes into Discord is
RENDERED from a `roll_history` row - the PNG is a lossy copy of structured data
the sheet app already holds. Reading the image back would be OCR of our own
output. Worse, the image cannot even be RECOGNIZED: clipboard pastes arrive as
`image.png` and so do memes (research.md R1). So the join is not a lookup, it is
the DETECTOR - a message with an image is a roll if and only if a recorded roll
exists for its author around its timestamp.

DEGRADATION IS THE FEATURE, NOT A FALLBACK. Every function here returns empty on
every failure - unset token, connection refused, 404 because the endpoint was
never built, malformed JSON - and records why. Nothing raises into the caller.
That is what makes FR-018 real: with no endpoint at all, no image resolves, every
TYPED roll still parses and is written, and the GM is told which image posts could
not be resolved. The feature is useful the day it ships and better the day the
endpoints land.
"""

from __future__ import annotations

import configparser
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_URL = 'https://l7r-character-sheet.fly.dev'
SECRETS = Path(__file__).resolve().parents[3] / 'development-secrets.ini'


@dataclass(frozen=True, slots=True)
class RecordedRoll:
    """One row of the sheet app's roll history."""

    character: str
    skill: str
    total: int
    actor_discord_id: str
    at: datetime
    rank: int | None = None


@dataclass(frozen=True, slots=True)
class SheetCharacter:
    """Who a Discord id plays, and what their ranks are RIGHT NOW."""

    name: str
    discord_id: str
    group: str = ''
    skills: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SheetResult:
    """What came back, and - when nothing did - why.

    `reason` is carried rather than logged and forgotten because it is what the GM
    is shown at the end of a conversation. "4 image posts could not be resolved:
    the roll endpoint returned 404" is actionable; silence is not.
    """

    rolls: tuple[RecordedRoll, ...] = ()
    characters: Mapping[str, SheetCharacter] = field(default_factory=dict)
    reason: str = ''

    @property
    def available(self) -> bool:
        return not self.reason


def query_token(path: Path | None = None) -> str:
    """The GM-equivalent read token for the sheet app's API.

    `path` defaults to `SECRETS` AT CALL TIME rather than as a bound default. That
    is not a style preference: a default argument is evaluated once at import, so
    `SECRETS` could not be redirected afterwards, and the tests that thought they
    were pointing this at a temp file were silently reading the real one. They
    passed only while no token existed anywhere, and started failing the moment one
    did - which is exactly backwards from what a test should do.
    """
    parser = configparser.ConfigParser()
    parser.read(path or SECRETS)
    return parser.get('character_sheet', 'roll_query_token', fallback='').strip()


def _get(url: str, token: str, timeout: float) -> Any:
    request = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _unavailable(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code == 404:
            return (
                'the character-sheet roll endpoint returned 404 - it is specified in '
                'externally-queryable-roll-results.md but not built yet'
            )
        return f'the character-sheet app returned {exc.code}'
    return f'could not reach the character-sheet app: {exc}'


def recorded_rolls(
    since: datetime,
    *,
    limit: int = 200,
    token: str | None = None,
    get: Callable[[str, str, float], Any] = _get,
    timeout: float = 20.0,
) -> SheetResult:
    """Rolls recorded at or after `since`. Empty, with a reason, on any failure."""
    resolved = token if token is not None else query_token()
    if not resolved:
        return SheetResult(
            reason='no [character_sheet] roll_query_token in development-secrets.ini'
        )
    query = urllib.parse.urlencode({'since': since.isoformat(), 'limit': limit})
    try:
        payload = get(f'{BASE_URL}/api/rolls?{query}', resolved, timeout)
    except Exception as exc:  # noqa: BLE001 - every failure degrades identically
        return SheetResult(reason=_unavailable(exc))
    return SheetResult(rolls=tuple(_as_roll(r) for r in payload.get('rolls') or ()))


def characters(
    *,
    token: str | None = None,
    get: Callable[[str, str, float], Any] = _get,
    timeout: float = 20.0,
) -> SheetResult:
    """Discord id -> character, with current ranks. Empty, with a reason, on failure."""
    resolved = token if token is not None else query_token()
    if not resolved:
        return SheetResult(
            reason='no [character_sheet] roll_query_token in development-secrets.ini'
        )
    try:
        payload = get(f'{BASE_URL}/api/characters', resolved, timeout)
    except Exception as exc:  # noqa: BLE001
        return SheetResult(reason=_unavailable(exc))
    found = {}
    for entry in payload.get('characters') or ():
        owner = str(entry.get('owner_discord_id') or '')
        if not owner:
            continue
        found[owner] = SheetCharacter(
            name=str(entry.get('name') or ''),
            discord_id=owner,
            group=str(entry.get('gaming_group_name') or ''),
            skills={str(k).lower(): int(v) for k, v in (entry.get('skills') or {}).items()},
        )
    return SheetResult(characters=found)


#: The sheet app labels a roll with its ring: `etiquette (air)`, `underworld
#: (water)`, `commune (air)`. The ring is display, not identity, and carrying it
#: through breaks anything that looks a skill up by name - MEASURED 2026-08-28
#: against the live endpoint: `record(68, "etiquette (air)")` returned 65 because
#: `RecordingRule.caps` is keyed on `etiquette`, so the GM's cap silently did not
#: fire and a 68 would have been written as 65 instead of 40. Silently wrong is the
#: worst failure this feature has, so the ring is stripped here, at the boundary
#: that knows the sheet's label format, rather than defended against everywhere
#: downstream.
_RING_SUFFIX = re.compile(r'\s*\([^)]*\)\s*$')


def canonical_skill(label: str) -> str:
    """The sheet app's roll label reduced to a bare skill name.

    Handles `skill:etiquette` and `knack:discern_honor` prefixes as well as the
    trailing ring.
    """
    return _RING_SUFFIX.sub('', str(label).split(':')[-1]).strip().lower()


def _as_roll(raw: Mapping[str, Any]) -> RecordedRoll:
    from l7r.repl.rolls.discord import parse_timestamp

    label = str(raw.get('label') or raw.get('roll_key') or '')
    return RecordedRoll(
        character=str(raw.get('character_name') or ''),
        skill=canonical_skill(label),
        total=int(raw.get('total') or 0),
        actor_discord_id=str(raw.get('actor_discord_id') or ''),
        at=parse_timestamp(str(raw.get('created_at') or raw.get('updated_at') or '')),
        rank=None if raw.get('skill_rank') is None else int(raw['skill_rank']),
    )

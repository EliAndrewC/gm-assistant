# Contract: the character-sheet client

**These endpoints DO NOT EXIST YET.** They are specified in the character-sheet repository at
`character-sheet/externally-queryable-roll-results.md`, written by this session for a session in
that container to implement. This contract is what `rolls/sheet.py` presents to the rest of the
feature, so the absence of the endpoints is contained in one module.

```python
recorded_rolls(since: datetime, limit: int = 200) -> list[RecordedRoll]
```
Wraps `GET /api/rolls?since=&limit=`. Returns rolls whose `updated_at` is at or after `since`,
ascending. Bearer token from `[character_sheet] roll_query_token`.

```python
characters() -> Mapping[str, SheetCharacter]
```
Wraps `GET /api/characters`, keyed by Discord id. Carries the character name, gaming group, and
CURRENT skill and knack ranks. Cached for hours - it changes rarely.

## Degradation is the point

Every function returns EMPTY on any failure - unset token, connection refused, 404 because the
endpoint was never built, malformed JSON - and records why. It never raises into the caller.

This is what makes FR-018 real: with no endpoint at all, `recorded_rolls` returns `[]`, no image
post resolves, every typed roll still parses and is written, and the GM is told which image posts
could not be resolved. The feature is useful on the day it ships and better on the day the endpoints
land.

## Rank resolution order

1. The rank the player typed (`@3`) - it is what they believe and what the GM sees in Discord
2. `skill_rank` on the matching recorded roll - correct AS OF THE ROLL
3. The character's current rank from `characters()` - correct NOW, which is not the same thing
4. `None`

Order 2 before 3 deliberately: ranks change when XP is spent, so the current rank can mis-state an
older roll. Recorded in the endpoint spec as a caveat for whoever implements it.

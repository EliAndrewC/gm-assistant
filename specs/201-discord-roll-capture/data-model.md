# Data model

Five entities. All are frozen dataclasses in `rolls/models.py` except `Conversation`, which is the
one piece of mutable state in the feature and lives behind a lock.

## Roll

One roll by one character. The unit everything else composes.

| field | type | notes |
|---|---|---|
| `character` | `str` | the PC or NPC name as it will appear in the line. Empty means unattributed - reported, never written (FR-020) |
| `skill` | `str` | canonical skill name from the vocabulary (`skills.py`), not the player's spelling |
| `total` | `int` | the roll AFTER the player's own bonuses. Never re-derived - we do not own the dice math |
| `rank` | `int \| None` | the character's rank in that skill; `None` when neither stated nor lookable (FR-016) |
| `source` | `"recorded" \| "typed"` | which path produced it. `recorded` wins on dedup (FR-009) |
| `message_id` | `str` | the Discord message, so any line can be traced back |
| `at` | `datetime` | the message timestamp, tz-aware UTC. Orders the line |

`total` is deliberately not decomposed into dice plus bonuses. The character-sheet app owns that
decomposition and the typed path frequently omits it (`38 Etiquette @3` states no dice at all).

## Contest

Two `Roll`s marked as opposing sides, plus what the GM's rule derives from them.

| field | type | notes |
|---|---|---|
| `left`, `right` | `Roll` | both totals kept UNROUNDED - the GM's rule is explicit |
| `winner` | `str \| None` | `None` on a tie |
| `margin` | `int` | `abs(left.total - right.total)` rounded DOWN to 5. Zero on a tie |

## Conversation

The only mutable state. At most one is open.

| field | type | notes |
|---|---|---|
| `npc` | `Mapping` | the matched OP character record - id, name, slug |
| `opened_at` | `datetime` | lower bound of the collection window (FR-003) |
| `channel_id` | `str` | which group's channel to read |
| `rolls` | `list[Roll]` | appended by the poller, read at close |
| `last_seen` | `str \| None` | the newest Discord message id already consumed, for incremental paging |
| `unresolved` | `list[str]` | messages the poller could not resolve, reported at close (FR-018) |

State: **closed -> open** (`begin_conversation`) -> **closed** (`end_conversation`, which writes;
or `abandon_conversation`, which does not). Opening while one is open is an error naming the open
NPC rather than silently replacing it.

## RecordingRule

The mapping from a raw total to the number written down. Exists as an entity because FR-013 requires
adding a rule to be a data change.

| field | type | notes |
|---|---|---|
| `increment` | `int` | rounding step, 5 everywhere so far |
| `caps` | `Mapping[str, int]` | per-skill ceiling applied BEFORE rounding. `{"etiquette": 40}` today |

A new capped skill is one entry in `caps`. That is the whole of SC-006.

## SkillVocabulary

The canonical skill names, read from `/host-l7r-repo/rules/02-skills.md` rather than copied (R6).
Supports exact match and unambiguous prefix match (`eti` -> `etiquette`), and reports an ambiguous
prefix rather than choosing.

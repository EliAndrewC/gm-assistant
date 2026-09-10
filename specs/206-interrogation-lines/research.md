# Research: Interrogation rolls grouped by line of questioning

No NEEDS CLARIFICATION markers remained in the spec. This file records the design decisions the
plan rests on, each with the alternatives that were priced, so the next reader knows they were
chosen rather than defaulted into (CLAUDE.md: "record a decision to accept a limitation, and the
alternatives that were declined").

## R1 - The rules text, and what it settles

**Source**: `/host-l7r-repo/rules/02-skills.md`, "### Interrogation" (line 212) and
"### Sincerity" (line 266).

**Found**: Interrogation is *"rolled once for each line of questioning"*. The NPC gets two free
raises to Sincerity when the interrogator is *"speaking to them casually rather than grilling
them"*, and two when *"they are telling a lie which they believe you are incapable of proving
wrong"*. GMs are *"encouraged to assign situational free raises to the interrogator when the other
person is scared, feels guilty, etc."* Meeting the Sincerity roll tells you whether they are
lying; +10 whether they are concealing; +20 their motivations.

**What it settles**:

- The unit of record is the line of questioning (FR-004, FR-008) - the rules say so directly.
- The GM's message described "two sets of conditional bonuses" and named only grilling; the rules
  supply the second, and it is secret by construction (noting "unprovable lie" raises on a line
  reveals that a lie was told). So only grilling is recorded, as a flag rather than a number
  (FR-003, FR-006). The GM accepted this resolution (gm-request.md).
- Situational raises to the interrogator reveal NPC state (scared, guilty), so the line carries no
  bonus on the player's side either (FR-003). This is the one place the feature departs from
  feature 202's "record the total after its own bonus" - deliberately, for this skill only.

## R2 - Lines of questioning are DERIVED from the rolls, not stored beside them

**Decision**: `Roll` gains `line: int | None` (a small integer id, unique within the
conversation) and `grilling: bool`. A line of questioning is *the set of interrogation rolls
sharing a `line` id*; its note is the shared `note`, its grilling flag the shared `grilling`.
There is no `Line` object on `Conversation`.

**Rationale**: the annotate menu stages `Decision`s and applies them only on a clean finish;
Ctrl-C throws the staged dict away. If lines lived in a second structure on the conversation,
creating one during the menu would have to be staged too, and discarding it on Ctrl-C would be a
second code path with its own bugs. With lines derived from rolls, a staged decision that says
"new line 3, grilling, note X" becomes real only when the roll it belongs to is applied - the
existing commit step - and vanishes with it on Ctrl-C. The menu's list of existing lines is
computed from `conv.rolls` overlaid with the staged decisions, which is the same overlay
`pending()` already does for "which rolls are still waiting".

**Alternatives priced**:

- *A `Line` dataclass in `Conversation.lines`, rolls pointing at it by index*: cleaner to read,
  but doubles the staging/abandon logic and makes "a line with no rolls" a state that can exist
  and must be filtered everywhere (FR-011 says such a line is not written). Rejected.
- *Group by note string, no id at all*: the simplest possible - two rolls with the same note are
  the same line. Rejected because it makes the join-or-new question meaningless (the GM would
  retype the note to join) and because a re-annotated note silently splits a line.

**Cost accepted**: the note and grilling flag are duplicated across every roll on the line. If a
future feature edits a line's note, it must edit every roll on it; the renderer reads them from
the line's first roll. Recorded in `rules.py` beside `render_interrogation`.

## R3 - Where a grouped line sits in the record

**Decision**: at the position of the line's FIRST roll in collection order, in sequence with the
conversation's other annotated lines (FR-010).

**Rationale**: feature 202's FR-014 - the record reads as the conversation happened. A line of
questioning began when its first roll was made; later rolls joining it do not move it.

**Alternatives priced**: all interrogation lines together after the Etiquette line (Etiquette's
own treatment). Rejected: Etiquette is a single round of introductions at the start; lines of
questioning are the conversation itself and interleave with open and contested rolls.

## R4 - The interrogation prompt replaces the kind prompt rather than extending it

**Decision**: for an interrogation roll, `annotate()` does not show
`Open, contested, discard, or open with bonus? [o/c/d/ob]`. It shows the existing lines (if any)
and asks `Join which line? (number, n for new, d to discard, blank to finish)`; with no lines,
`New line of questioning, or discard? [n/d, blank to finish]`. Then, in order: the rank if the
roll has none (FR-007), and for a new line `Grilling? [y/N]` and the note (FR-009).

**Rationale**: FR-002 and FR-003 forbid `c` and `ob` for this skill, and offering them only to
refuse them is a prompt that lies. The GM asked for "a menu such that when I am selecting
interrogation rolls, I can indicate whether a roll ... is part of the same topic ... or a new
topic" - the join-or-new question IS the kind prompt for this skill.

**Grilling default is No**: the rules make casual the default state ("speaking to them casually
rather than grilling them") and the GM's example shows one line of each. A blank answer means
not grilling; `y`/`yes` means grilling.

**Rank prompt accepts blank** as "no rank" (FR-007), so it is not `_number()` with a default; a
small `_optional_number()` sibling returns `None` on blank and re-asks on anything non-numeric.

## R5 - A roll already written as a contested interrogation line

**Decision**: ignored, not migrated. `render_lines` routes every interrogation roll through the
interrogation renderer regardless of `opposed_total`; on the next write the conversation's block
is REPLACED (feature 201's `bio.rewrite`), so the old contested line disappears.

**Rationale**: the only such rolls are in conversations open right now, at most one; a migration
path would be code with no second use. Recorded as an edge case in the spec.

## R6 - Regression baseline (constitution XIII)

Taken 2026-09-10 on unmodified `f2a0c885` in a detached worktree
(`git worktree add --detach <scratch>/base HEAD`), with main's gitignored
`development-secrets.ini` and `opcache/` copied in so fixture-reading tests behave as in the clone:

```
( cd <scratch>/base/webapp && pytest -q -n auto -p no:cacheprovider tests/ )
1248 passed, 23 warnings in 10.15s
```

Zero failures before; the merge bar is zero new failures after.

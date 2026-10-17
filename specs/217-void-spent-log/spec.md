# Feature 217: void points an NPC spends in a conversation, kept in the GM-only notes

**Request**: [gm-request.md](gm-request.md) (2026-10-17). **Status**: specified.

## Why

The GM marks an NPC's void point at the REPL in two ways, both inside an open conversation:
the called form `tact(vp)` / `tact(5, 3, vp)` (`vp * 2` for two), and the `[v]` answer at the
disagreement prompt when a tagged roll is off by exactly 1k1 or 2k2. Today that number lives
only on the in-memory `GmRoll` and is used for one thing: not mistaking the extra die for a
bigger ring. Nothing is written, so when a fight breaks out later the GM has no record of which
conversations already used the NPC's void points.

## User Scenarios & Testing

### Story 1 - a spend lands in the GM-only notes (P1)

`begin_conversation("Otsuki", "confrontation on the Imperial road")`, then `tact(vp)`. On the
watcher's next write, Otsuki's GM-only notes carry:

    Void points spent:
    - 2026-10-17 1 void point on tact 34 - confrontation on the Imperial road

`sincerity(vp * 2)` in the same conversation adds
`- 2026-10-17 2 void points on sincerity 41 - confrontation on the Imperial road`.

**Acceptance**: both spend forms (called `vp`, and `[v]` at the disagreement prompt) produce an
entry; the entry names the date the conversation opened, the count, the skill and the roll's
total, and the conversation title when there is one (no ` - ...` tail when there is none).

### Story 2 - the block is a log across conversations (P1)

The next conversation with Otsuki next month adds its own lines under the same heading and
leaves the earlier ones exactly as they were, so before a fight the GM reads every conversation
in which the NPC spent void.

**Acceptance**: a conversation only replaces the lines it wrote itself; lines from earlier
conversations survive untouched; the block's heading is created on the first spend and is not
created for a conversation that spent none.

### Story 3 - a mistaken roll spent nothing (P2)

The GM answers `[m]` (or Ctrl-C) at the disagreement prompt for a `tact(5, 3, vp)` roll: the roll
is a mistake and will be rolled again. That roll's void point is NOT logged; the re-roll's is.

### Story 4 - the GM sees the total at the close (P2)

`end_conversation()` prints, when the NPC spent any, `Otsuki spent 3 void points this
conversation (GM-only notes).` A conversation with no player rolls but a spend still writes the
block.

### Edge cases

- The sincerity roll that spends void stays in `Hidden rolls:` as well; the void block is about
  void, not about hiding the number, so its total appears in both GM-only places. Neither reaches
  the bio.
- `abandon_conversation()` writes nothing, as today; spends made in an abandoned conversation are
  thrown away with it (it is the wrong-NPC exit).
- A spend's total changes after it is logged (`_ + 5`, an oppose penalty): the entry shows the
  roll's current total, re-rendered each write.

## Requirements

- **FR-001** Every GM roll whose `void_points` is set while a conversation is open is noted on
  that conversation (both spend forms).
- **FR-002** The GM-only notes carry a `Void points spent:` block with one entry per such roll
  that is not marked a mistake, in the format of Story 1.
- **FR-003** The block is written by the same tick that writes `NPC numbers:` and `Hidden rolls:`
  (debounced, final write on close, never into the bio), and a change to it alone triggers a
  write.
- **FR-004** A conversation replaces only its own earlier entries; other entries are untouched
  (Story 2).
- **FR-005** `end_conversation()` reports the conversation's void total when it is non-zero.

Out of scope (not asked): tracking void recovery, the NPC's void maximum, or a REPL syntax for
spending void outside a roll.

## Review history

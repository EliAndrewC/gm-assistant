# Feature 217: void points an NPC spends in a conversation, kept in the GM-only notes

**Request**: [gm-request.md](gm-request.md) (2026-10-17). **Status**: implemented 2026-10-17.

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
    - 2026-10-17 1 void point on tact - confrontation on the Imperial road

`sincerity(vp * 2)` in the same conversation adds
`- 2026-10-17 2 void points on sincerity - confrontation on the Imperial road`.

The `[v]` answer comes in two wordings. "This roll spent a void point" is a spend on the roll
just made. "The previous roll spent 2 void points" says the roll the record was read from spent
them; that roll may be this conversation's or an older one's, so its entry says so:
`- 2026-10-17 2 void points on an earlier tact roll - confrontation on the Imperial road`.

**Acceptance**: both spend forms (called `vp`, and either `[v]` wording) produce an entry; the
entry names the date the conversation opened, the count, the skill, and the conversation title
when there is one (no ` - ...` tail when there is none). A conversation with no player rolls but
a spend still writes the block.

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

### Edge cases

- A sincerity roll that spends void appears in both `Hidden rolls:` and `Void points spent:`;
  neither reaches the bio.
- `abandon_conversation()` adds no final flush and no rollback: void lines the watcher has already
  written stay, exactly as `Hidden rolls:` and `NPC numbers:` lines do today.

## Requirements

- **FR-001** Every void spend the GM marks while a conversation is open is noted on that
  conversation: the called `vp` form, the `[v]` "This roll spent ..." answer, and the `[v]` "The
  previous roll spent ..." answer (count = `abs(found.void_points)`, entry worded "on an earlier
  <skill> roll" per Story 1).
- **FR-002** The GM-only notes carry a `Void points spent:` block with one entry per such roll
  that is not marked a mistake, in the format of Story 1.
- **FR-003** The block is written by the same tick that writes `NPC numbers:` and `Hidden rolls:`
  (debounced, final write on close, never into the bio), and a change to it alone triggers a
  write.
- **FR-004** A conversation replaces only its own earlier entries; other entries are untouched
  (Story 2).

Out of scope (not asked): tracking void recovery, the NPC's void maximum, or a REPL syntax for
spending void outside a roll.

## Review history

- **Round 1 (spec-fidelity, 2026-10-17): CHANGES REQUIRED.** Struck an unrequested close-time
  console report (old FR-005 / Story 4) and the roll's total in each entry (the approved line was
  date, title, skill and count); corrected the abandon edge case, which implied a rollback. Judged
  the mistake carve-out (Story 3) LEGITIMATE: `[m]` means the roll is redone, so its void point was
  never spent, matching `hidden._usable`. Round 1 also covered both spend forms; the "previous
  roll" `[v]` wording is now spelled out in Story 1 for round 2.
- **Round 2 (spec-fidelity, 2026-10-17): CHANGES REQUIRED.** Round 1 fixes confirmed. Logging the
  "previous roll" answer judged WITHIN the request (it is the only point an unmarked spend comes to
  light). FR-001 reworded to name all three spend forms, since the old wording ("whose
  `void_points` is set") missed the previous-roll branch, which never sets it.

# Feature Specification: NPC numbers backport (character sheet -> Obsidian Portal)

**Feature Branch**: none (main; `SPECIFY_FEATURE=226-npc-numbers-backport`)

**Created**: 2026-10-25

**Status**: Draft

**Input**: the GM's request, verbatim in [`request.md`](request.md): "when we create characters on the character
sheet, to backport any rings and stats we established back into obsidian portal so that e.g. whatever their Air ring
ends up being in the character sheet app gets backported to their Obsidian Portal page. Can we integrate that into the
process?"

## Background

An NPC's stats that have been used in play live in the **"NPC numbers:" block** of its Obsidian Portal (OP) GM-only
notes (feature 207, `webapp/l7r/repl/rolls/npcnumbers.py`): `- Air 4`, `- sincerity 3`, one per line. The REPL reads
that block so an NPC's tact or sincerity stays the same from session to session.

The character-sheet app builds combat NPCs and can be handed those recorded numbers (`recorded`), but nothing comes
back: the rings, attack, parry, skills and knacks it builds exist only on the sheet. The next time the GM rolls for
that NPC outside combat, the REPL does not know them.

Only gm-assistant writes to OP (character-sheet `CLAUDE.md`, repository table), so the sheet hands the numbers to
gm-assistant and gm-assistant writes them. The sheet already calls gm-assistant this way for NPC names (feature 213,
`GET /api/names`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A new combat NPC's stats land on its OP page (Priority: P1)

The GM generates a combat NPC on the sheet for a character who already has an OP record (say Bayushi no Daika Koharu,
whose block says Air 4, Water 3, sincerity 1, ...). When the sheet finishes building it, Koharu's OP block holds every
ring and stat the sheet built: all five rings, attack, parry, every skill and knack she has. The values she already had
are unchanged, and the GM sees on the sheet which OP record was updated and what changed.

**Why this priority**: it is the request.

**Independent Test**: post a built NPC's stats for a name that matches one OP character; read that character's GM-only
notes back; the block holds every posted stat, and the rest of the notes are byte-identical.

**Acceptance Scenarios**:

1. **Given** an OP character whose block has `Air 4` and `sincerity 1`, **When** the sheet sends Air 4, Earth 3, Fire 3,
   Water 3, Void 3, attack 3, parry 3, sincerity 1, iaijutsu 2, **Then** the block holds all nine, rings first, and the
   answer lists the seven that were added.
2. **Given** an OP character with no block, **When** the sheet sends its stats, **Then** a block is appended to the
   end of the GM-only notes and nothing else in them moves.
3. **Given** a block that already holds exactly what is sent, **When** the sheet sends it again, **Then** OP is not
   written at all and the answer says "unchanged".
4. **Given** a block with a stat the sheet does not send (a hand-written `heraldry 3` on a bushi with no Heraldry),
   **When** the sheet sends its stats, **Then** `heraldry 3` stays.

### User Story 2 - Rebuilt and returning NPCs update too (Priority: P2)

The GM rebuilds an NPC, or brings one back from the roster with more XP. Its stats rise, and OP follows.

**Why this priority**: "whatever their Air ring ends up being" includes the later builds; without this the OP page
falls behind the first time an NPC comes back stronger.

**Independent Test**: send a stat set, then a second set with Air one higher; the block says the higher value.

**Acceptance Scenarios**:

1. **Given** a block with `Air 4`, **When** the sheet sends Air 5, **Then** the block says `Air 5` and the answer
   reports `Air 4 -> 5`.

### User Story 3 - Nothing used in play is lost (Priority: P2)

A stat in the block was used at the table; the players have seen the NPC roll it. If the sheet sends a LOWER value for
it, the sheet's build has not honored what was recorded (the NPC was generated without its recorded numbers, or a
generator defect like character-sheet#3). Writing the lower value would make OP contradict play.

**Acceptance Scenarios**:

1. **Given** a block with `Air 4`, **When** the sheet sends Air 3 (and other new stats), **Then** `Air 4` stays, the
   other stats are written, and the answer reports a conflict: "Air: the sheet built 3, Obsidian Portal has 4 (used in
   play) - kept 4; rebuild the NPC with Air 4 recorded".

### User Story 4 - NPCs with no OP page are left alone (Priority: P3)

Most generated NPCs are nameless guards and bandits with no OP record. The backport writes nothing for them, creates no
page, and says so.

**Acceptance Scenarios**:

1. **Given** a name that matches no OP character, **When** the sheet sends its stats, **Then** nothing is written and
   the answer says "no Obsidian Portal record", with the nearest names.
2. **Given** a name that matches several OP characters, **When** the sheet sends its stats, **Then** nothing is
   written and the answer lists the candidates.

### Edge Cases

- **The GM's REPL has a conversation open with the same NPC** when the sheet writes. The REPL's next write must not
  put back its older copy of the block over the new numbers (today it renders its in-memory copy, which would).
- **OP is down or rejects the write**: the sheet's NPC is still created; the answer reports the failure; nothing is
  retried silently.
- **A stat name that cannot be a block line** (the block's line format is letters and spaces): sheet ids with
  underscores (`double_attack`) are written with spaces (`double attack`); anything else is refused by name in the
  answer, and the valid stats are still written.
- **Out-of-range values** (below 0 or above 6) and unknown fields are refused with a 400 before any OP call.
- **Unauthenticated or unconfigured**: 401 / 503 before any OP call, exactly as `/api/names`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: gm-assistant MUST accept a built NPC's name and stats from the character-sheet app and write them into
  the "NPC numbers:" block of the one OP character the name resolves to.
- **FR-002**: The stats are every ring (all five), attack, parry, and every skill and knack (school and foreign) the
  sheet built at rank 1 or more. Profession abilities are not stats and are not sent.
- **FR-003**: A stat new to the block is added; a stat equal to the block's is left; a stat HIGHER than the block's
  replaces it; a stat LOWER than the block's is NOT written and is reported as a conflict (User Story 3).
- **FR-004**: Block lines the sheet did not send are kept, in place; text outside the block is never changed.
- **FR-005**: When nothing would change, OP is not written.
- **FR-006**: The name is resolved by the same whole-name-token matching the REPL uses (`opsynth.match_character`);
  no match or several matches write nothing and report the nearest names or the candidates.
- **FR-007**: The answer always says what happened: the OP record matched (name and URL), the stats added, raised,
  unchanged and refused, and any conflict, in words the GM can read on the sheet.
- **FR-008**: The endpoint authenticates the caller with the bearer token the sheet already presents to gm-assistant
  (`[character_sheet] names_token`), failing closed (503 when unset, 401 when wrong), before parsing the body or
  reading OP.
- **FR-009**: The write reads the GM-only notes fresh immediately before writing, so an edit made since (by the GM or
  the REPL) is not lost.
- **FR-010**: The REPL's conversation writer MUST merge the block it read fresh with its own numbers instead of
  replacing the block with its in-memory copy, so a backport during an open conversation survives.
- **FR-011**: The character-sheet session is handed the caller by GitHub issue: send the stats after generating,
  rebuilding, and bringing back an NPC; never let a backport failure block or undo the NPC; show the GM the answer.
- **FR-012**: The caller is enabled only after character-sheet#3 is live (a recorded ring overshoots by one at 4th
  Dan). Before it, a recorded Air 4 builds to Air 5, FR-003 would write Air 5, and the next build would pin 5.

### Key Entities

- **NPC numbers block**: the parsable `NPC numbers:` heading and `- name value` lines in an OP character's GM-only
  notes (feature 207).
- **Backport request**: an NPC's name, its stats (name -> rank), and the sheet's character id (for the answer and the
  log only).
- **Backport answer**: status (`written`, `unchanged`, `no_record`, `ambiguous`, `failed`), the matched record, and the
  per-stat outcome.

## Success Criteria *(mandatory)*

- **SC-001**: For every generated, rebuilt or returning NPC with exactly one OP record, the OP block afterwards agrees
  with the sheet on every ring and stat the sheet built, except values kept under FR-003's conflict rule, each of which
  is reported.
- **SC-002**: No text outside the block, and no block line the sheet did not send, changes in any backport (checked
  byte-for-byte in tests on real recorded GM notes).
- **SC-003**: An NPC with no OP record, or an ambiguous name, produces zero OP writes.
- **SC-004**: A stat already in the block is never lowered by a backport.

## Assumptions

- **Same token as `/api/names`** (FR-008). The caller is the same principal (the sheet app) on the same server; a
  second secret would need the GM to copy a new value into both apps' secrets by hand for no change in who can write.
  Declined: a separate write secret (the sheet keeps one for `/api/conversation` because a different caller, the REPL,
  writes there).
- **Push, not pull.** gm-assistant's read API on the sheet (`/api/characters`) does not expose rings, and a pull would
  need a schedule; the sheet knows the moment a build changes.
- **Lowering is refused, not written** (FR-003). The GM's words are "whatever their Air ring ends up being in the
  character sheet app gets backported". A lower value can only come from a build that ignored a number already used in
  play, which the block exists to keep stable (feature 207); the conflict is reported with the fix (rebuild with it
  recorded). Raised for adjudication by `spec-fidelity`.
- **Existing NPCs are not backfilled** by this feature. Ones built before character-sheet#3 may carry the overshoot;
  the character-sheet session reported that those need regenerating by hand. A backfill can be run afterwards.
- The deployed toolkit already holds the OP credentials (the image carries `development-secrets.ini`), so it can write.

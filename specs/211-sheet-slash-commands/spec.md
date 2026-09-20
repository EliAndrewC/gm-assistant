# Feature Specification: More Discord roll commands - `/roll`, one command per skill, `/initiative`, and void points that really get spent

**Feature Directory**: `specs/211-sheet-slash-commands`

**Created**: 2026-09-20

**Status**: Planned. Amended for GM messages 2 and 3 and re-reviewed each time (see Review
history). Not implemented, and blocked by design until the character-sheet work ships.

**Input**: GM request 2026-09-20, three messages, verbatim in [gm-request.md](gm-request.md).

**THE CHARACTER-SHEET WORK SHIPS FIRST** (GM message 2). The GM runs that work in a separate
container and deploys it. **Task 1 here is to validate it was done** - behavior, not a changelog.
Nothing in this feature is built on a workaround for a defect that document asks to be fixed.

**WHO BUILDS IT - read first.** Every command below is implemented in
**<https://github.com/EliAndrewC/character-sheet>**, **by that repository's own Claude Code
session**, not by this one (GM message 3: *"I forgot that the commands themselves live in the
character sheet repo, so I do not want you to edit that tree directly ... fold the command layer
into the requirements document and then I will have the other session build all of it"*). It sits
there for the standing 2026-08-28 reason - code goes where the WRITE happens, `/etiquette` is
already there, and the dice math is never reimplemented outside it.

So this feature's own deliverables are three: **this specification**, the handoff document
`discord-slash-commands-requirements.md` at the root of that repository (which now carries the
command layer too, as its Part 2), and **gm-assistant's own roll-capture side** - User Story 6, the
only part of this that is code in this repository. Everything else here is a statement of what
should exist, verified after the fact.

## Why

Today one command exists, `/etiquette`, and it makes only the unconditional roll: no void points,
and nothing about it touches the sheet beyond the roll-history row. A player who wants to spend
void still has to open the sheet, and initiative cannot be rolled from Discord at all. The GM wants
the ordinary non-combat rolls of a session, and the start of a combat round, to be things a player
does from the channel everybody is already in - with the sheet kept true, so that Discord is a
second way in to the same character rather than a parallel set of books.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - `/roll` rolls any skill, with autocompletion (Priority: P1)

A player types `/roll`, starts typing a skill name, picks it from the completions Discord offers,
and the bot posts the roll for the character they are playing - the same dice card and text line
`/etiquette` posts today.

**Independent test**: in the test guild, `/roll skill:sinc` offers Sincerity; choosing it posts a
Sincerity roll for the invoker's character and writes a roll-history row indistinguishable from one
made on the sheet.

**Acceptance scenarios**:

1. **Given** a player with a character, **When** they type `/roll` and the letters `pre`, **Then**
   the completions include Precepts, and choosing it rolls Precepts.
2. **Given** the completions list, **Then** it offers every non-combat skill and no combat skill.
3. **Given** a skill typed by hand that matches nothing, **When** the command is submitted,
   **Then** the invoker alone sees a message saying so, and nothing is rolled or posted.

### User Story 2 - Every skill has its own command (Priority: P1)

`/precepts`, `/sincerity` and every other non-combat skill each roll that skill, exactly as `/etiquette` does now, so
the common case is one short command with no argument to fill in.

**Independent test**: every non-combat skill the sheet knows has a registered command of the same name; each
posts that skill's roll.

**Acceptance scenarios**:

1. **Given** the registered command set, **Then** there is one command per non-combat skill, plus
   `/roll` and `/initiative`, no command for any combat skill, and the total is under Discord's
   per-application limit of 100.
2. **Given** a non-combat skill added to the sheet later, **Then** re-running registration adds its
   command with no list edited by hand (the set is derived from the sheet's own skill table,
   excluding whatever the sheet treats as a combat skill).

### User Story 3 - Void points spent from Discord are spent on the sheet (Priority: P1)

`/roll` and every per-skill command accept a number of void points. The roll is made with them,
the post says so, and the character's void points on their sheet go down by that many. Nobody can
spend void they do not have.

**Independent test**: a character with 2 void points runs `/sincerity void:1`; the roll has the
extra die, the post names the spend, and opening the sheet shows 1 void point. `/sincerity void:3`
is then refused privately and the sheet is unchanged.

**Acceptance scenarios**:

1. **Given** a character with N void points available, **When** they roll with `void:k`, k <= N
   and within the sheet's per-roll limit, **Then** the roll gains what k void points give on the
   sheet, k points are deducted from the same pools in the same order the sheet deducts them, and
   every consequence the sheet attaches to spending void happens here too.
2. **Given** a request for more void than the character currently has, **Then** nothing is rolled,
   nothing is spent, nothing is posted to the channel, and the invoker alone is told how many they
   have.
3. **Given** a request above the sheet's per-roll void limit for that character, **Then** the same
   private refusal, naming the limit.
4. **Given** the same roll made on the sheet and through Discord with the same void spend,
   **Then** the formula, the deduction and the recorded history row agree.
5. **Given** the player has the sheet open in a browser while they spend void from Discord,
   **Then** the spend is not lost or undone by that open page.

### User Story 4 - `/initiative` starts the character's combat round (Priority: P1)

A player types `/initiative`. The bot rolls initiative for their character, posts the action dice,
and the character's sheet now shows those action dice, unspent, with the previous round's state
gone - exactly what rolling initiative on the sheet does.

**Independent test**: a character with leftover spent action dice runs `/initiative`; the post
lists the new action dice; opening the sheet shows those dice, all unspent, and none of the old.

**Acceptance scenarios**:

1. **Given** any character, **When** `/initiative` is run, **Then** the dice rolled and kept, and
   every school or profession adjustment to the resulting action dice, match what the sheet's own
   initiative roll would do for that character.
2. **Given** action dice or per-round state left from an earlier round, **Then** they are replaced
   and reset as the sheet's own initiative roll replaces and resets them; state the sheet keeps
   across rounds is kept.
3. **Given** the sheet is opened afterwards, **Then** the action dice are there and can be spent
   from the sheet in the normal way.
4. **Given** the sheet was already open in a browser, **Then** the new action dice are not lost or
   undone by that open page.

### User Story 5 - Three rolled school knacks get commands (Priority: P1)

`/oppose-social`, `/oppose-knowledge` and `/commune` roll those knacks for the invoker's character.
`/commune` costs a void point just to be made, which comes off the sheet like any other spend.

**Independent test**: a character with Commune and 1 void point runs `/commune`; the roll is posted
and the sheet shows 0 void points. With 0 void points, `/commune` is refused privately and nothing
is rolled.

**Acceptance scenarios**:

1. **Given** a character who has the knack, **When** they run `/oppose-social` or
   `/oppose-knowledge`, **Then** it rolls that knack exactly as the sheet rolls it, and records the
   roll the same way a skill command does.
2. **Given** a character who runs `/commune`, **Then** one void point is spent to activate it
   before any optional spend, and the post says so.
3. **Given** a character who cannot pay the activation point, **Then** the roll is refused
   privately: no dice, no deduction, no post.
4. **Given** `/commune void:k` on top of the activation point, **Then** the activation point is
   paid first and k is checked against what remains, as the sheet does.
5. **Given** a character who does NOT have the knack, **Then** the invoker alone is told so, and
   nothing is rolled.

### User Story 6 - The GM's roll capture still reads the bot's posts (Priority: P2, gm-assistant)

gm-assistant's roll capture (features 201-210) reads the character-sheet bot's posts. The new post
shapes - a roll that names a void spend, an initiative post - must not be misread.

**Independent test**: fixture posts in the new formats parse as the right skill and total, and an
initiative post parses as no skill roll at all.

## Requirements *(mandatory)*

- **FR-001**: A `/roll` command MUST exist with a skill argument that autocompletes as the player
  types, offering every non-combat skill the sheet defines.
- **FR-002**: Every non-combat skill the sheet defines MUST have its own slash command named for
  it, behaving as `/etiquette` does today.
- **FR-003**: The sheet's combat skills MUST NOT be offered by `/roll` or given their own commands
  in this feature. The source of truth for which skills are combat skills is the sheet's own data,
  not a list kept by this feature: attack and parry (which the sheet holds apart from its skill
  table), iaijutsu, and anything else the sheet marks or stores as combat. `/initiative` is the
  GM's own request and is not an exception to this. (Damage rolls and wound checks are not skills,
  so "roll any skill" never included them.)
- **FR-003a**: `/initiative` MUST NOT accept void points. The rules settle it: initiative is rolled
  "without spending void points or rerolling 10s" (`rules/03-combat.md`, Initiative, in
  <https://github.com/EliAndrewC/l7r>).
- **FR-004**: `/roll` and every per-skill command MUST accept a number of void points to spend,
  defaulting to none.
- **FR-005**: A void spend made through a command MUST be applied to the roll and deducted from the
  character's sheet as one all-or-nothing step: either the roll happens and the points are gone, or
  neither.
- **FR-006**: A command MUST refuse, privately and without rolling, a void spend greater than the
  character's currently available void points, or greater than the sheet's per-roll limit for that
  character.
- **FR-007**: Everything the sheet does when void is spent on that roll - which pool is drawn
  first, and any school consequence of spending - MUST happen identically for a Discord spend.
- **FR-008**: `/initiative` MUST roll initiative by the sheet's own formula for the character,
  apply the sheet's own adjustments to the resulting action dice, store them on the character as
  the current round's unspent action dice, and reset what the sheet resets at a new round.
- **FR-009**: The posted message MUST say what was spent (void) and, for initiative, list the
  action dice.
- **FR-010**: Discretionary bonuses applied after seeing a roll are OUT of scope, as the GM said:
  the player marks those on the sheet afterwards. The roll a command records MUST therefore be one
  the sheet can still amend afterwards in its usual way.
- **FR-011**: Who rolls (the invoker's grouped character, or a GM pin), who may be recorded, and
  private error replies MUST follow the rules `/etiquette` already follows. A command that changes
  the sheet MUST NOT let an invoker change a character they could not edit on the sheet itself.
- **FR-012**: A sheet page already open in a browser MUST NOT silently overwrite a void spend or
  action dice written by a command.
- **FR-013**: The roll rules MUST NOT be implemented a second time outside the character-sheet
  repository; where the browser holds logic the server now also needs, both MUST be pinned to the
  same test cases.
- **FR-014** (gm-assistant): roll capture MUST parse the new post formats correctly, pinned by
  fixtures of real posts.
- **FR-015**: `/oppose-social`, `/oppose-knowledge` and `/commune` MUST exist and roll
  `knack:oppose_social`, `knack:oppose_knowledge` and `knack:commune` respectively, following every
  rule in FR-004 through FR-011 that applies to a skill command.
- **FR-016**: `/commune` MUST spend one void point to activate, deducted from the sheet, before any
  optional void spend; a character who cannot pay it MUST be refused without rolling. An optional
  spend on the same command MUST be checked against what remains after the activation point.
- **FR-017**: A command for a knack the character does not have MUST refuse privately rather than
  roll something.
- **FR-018**: NO other school knack and no school ability is added by this feature; neither is
  Otherworldliness, which the GM deferred to a later feature by name.
- **FR-019**: This feature MUST NOT work around any defect named in the character-sheet
  requirements document - a workaround in the bot is not an acceptable substitute (GM message 2:
  *"We should not implement any kludgy workarounds when we can instead fix the character sheet
  app"*). If any **blocking** requirement (that document's Parts 1 and 2) turns out not to have
  been delivered, the work STOPS and the GM is told. The stop-rule covers those parts only: the
  audit (Part 4) and the non-blocking API addition (Part 3) are reported on, never a reason to
  halt.
- **FR-020**: This session MUST NOT write or change any application code, test, configuration or
  other file in the character-sheet tree (GM message 3). The single file it writes there is the
  handoff requirements document at that repository's root, left uncommitted for that repository's
  own session to commit. Anything else this feature needs from that app is expressed as a
  requirement in that document, never as an edit.

## Decisions the request left open

Each is cheap to change after the fact; the plan proceeds on the stated reading.

1. **"void points and such."** Answered by the GM in message 2: the other pre-roll bonus is
   Otherworldliness, and it is deferred by name. So `void` is the only option on a skill command in
   this feature, and `/commune`'s activation point is the one other thing that touches the void
   pools.
2. **`/roll` completes skills only**, not knacks. The GM said "roll any skill", and named the
   three knacks he wants as their own commands rather than as `/roll` entries. The other rollable
   knacks are held for a later feature by his instruction, so putting these three into the
   completions would advertise a category this feature does not cover.
3. **Commune takes no element argument.** The sheet pins Commune to the character's School Ring;
   the rules text said "the Ring of the element of the spirits you are questioning". The GM settled
   it in message 3 - the app is right and the rules were simply behind - so no command option is
   needed. This session also made the matching edit to `rules/05-school_knacks.md` in
   `EliAndrewC/l7r`, since the GM said he had been meaning to and had not had time; that edit is an
   **uncommitted working-tree change** awaiting his own commit, and keeping or reverting it is his
   call. Nothing in this decision depends on it - the app already behaves this way.
4. **Togashi Ise Zumi's two initiative variants**: `/initiative` rolls the default variant, the
   same "a slash command has nobody to ask, so it takes the plain roll" rule the sheet repository
   already applies to the Merchant's `/commerce`. An optional `variant` argument is the declined
   alternative - declined because it would show for every player to serve one school.
5. **A GM rolling on a pinned test character** spends that character's void like anybody else;
   the existing rule that such rolls leave no history row is unchanged.

## Offers, not requirements

- Completions could show the character's rank ("Sincerity (3)"). Not asked for, so not specified;
  raised with the GM once the feature works.

## Review history

Independent `spec-fidelity` review (constitution XVI), against gm-request.md as written.

- **Round 1 - CHANGES REQUIRED** (2026-09-20). Building it in the character-sheet repository, the
  per-roll void cap, FR-012 and the roll-capture story (then numbered 5, now 6) were all found
  faithful. Four changes: FR-001/FR-002
  said "every skill", which by the rules includes attack and parry - the one thing the GM excluded
  (now "non-combat" throughout); FR-003 swapped the GM's class "combat skills" for "combat rolls"
  and ended in "and the like" (now the GM's class, with the sheet's data as source of truth); void
  on initiative was listed as open when the rules text answers it (now FR-003a); and rank-in-
  completions was an unrequested addition presented as a decision (now an offer).
- **Round 2 - FAITHFUL** (2026-09-20). All four changes confirmed resolved, and the two external
  claims the requirements rest on were checked at source rather than taken on trust: the skill list
  in `rules/02-skills.md` is Social and Knowledge only (so attack and parry genuinely sit outside
  it), and `rules/03-combat.md` Initiative reads "without spending void points or rerolling 10s"
  (so FR-003a is the rules, not a carve-out). Nothing missing against the request, nothing added
  beyond the sheet-write consequences the GM's own parity standard implies.

GM message 2 amended the request (three rolled knacks, Otherworldliness deferred, the
character-sheet handoff, the ship-order dependency), so a second cycle was run over the amended
spec AND the companion requirements document, against both messages.

- **Message 2, round 1 - CHANGES REQUIRED** (2026-09-20). Message 2 was found fully carried, the
  requirements document was found to contain both halves the GM asked of it, and its reading of
  "you need not do a full audit / the character-sheet session should perform a full audit" as a
  DELEGATION rather than a reduction was upheld. Two changes, both about a dependency being drawn
  wider than the GM drew it: one sentence in the audit section attributed a scope limit to the GM
  that he never stated (reworded to limit the FIXING, not the LOOKING); and the API addition
  (current void, action dice, cap on `GET /api/characters`) was filed as blocking when no
  requirement in this spec actually reads it over HTTP - it moved to a non-blocking section, and
  FR-019's stop-rule is now scoped to the blocking requirements only, so a thin audit write-up
  cannot halt this feature.

GM message 3 settled Commune's ring and reassigned the command layer to the character-sheet
repository's own session, so a third cycle was run over the amended spec and the handoff document.

- **Message 3, round 1 - CHANGES REQUIRED** (2026-09-20). All three messages were found carried,
  and the handoff document's Part 2 was checked FR by FR and found to have moved the command layer
  across without changing what any command does - including every judgment call (skills-only
  completion, the Togashi default variant, a GM on a pin still spending void, the activation point
  first). Four changes, three of them about a claim being stated more strongly than the facts
  support: the header still said two messages; FR-020's blanket "MUST NOT edit that tree" banned
  the one write message 3 requires, the handoff document itself; the handoff document's scope line
  enumerated its owned parts in a way that left the GM's own API sentence unowned; and both
  documents described this session's edit to the GM's rules file as an accomplished published fact
  when it is an uncommitted working-tree change in a repository this session may not commit.

## Success Criteria *(mandatory)*

- **SC-001**: A player can make any non-combat skill roll, with or without void, without opening
  their sheet, and the sheet's void count is right the next time anybody looks.
- **SC-002**: A player can start their combat round from Discord and then spend the resulting
  action dice on the sheet.
- **SC-003**: No command can take a character's void below zero or above what the sheet permits
  per roll - demonstrated by tests, not by inspection.
- **SC-004**: For the same character state and the same dice, the sheet and the command produce the
  same roll, the same deduction and the same action dice - pinned by shared test cases.
- **SC-005**: gm-assistant's capture reads every new post format correctly.
- **SC-006**: A character can roll all three named knacks from Discord, and `/commune` cannot be
  made without a void point to pay for it.
- **SC-007**: No part of this feature compensates for a defect the character-sheet requirements
  document asks that app to fix.

# Feature Specification: More Discord roll commands - `/roll`, one command per skill, `/initiative`, and void points that really get spent

**Feature Directory**: `specs/211-sheet-slash-commands`

**Created**: 2026-09-20

**Status**: Planned, reviewed FAITHFUL. Not implemented - the work is done in the character-sheet repository.

**Input**: GM request 2026-09-20, verbatim in [gm-request.md](gm-request.md).

**WHERE THIS IS BUILT - read first.** The commands are implemented in
**<https://github.com/EliAndrewC/character-sheet>**, not in this repository. That is the standing
decision of 2026-08-28 (recorded in both repositories' CLAUDE.md): code goes where the WRITE
happens, the existing `/etiquette` command already lives there, and the dice math is never
reimplemented outside it. Every sheet-affecting requirement below - spending a void point, setting
action dice - is a write to the sheet's own database, which settles it. This directory is the
planning record, written here because this is where the GM asked; [plan.md](plan.md) is grounded in
a read of the character-sheet code at commit `6c4dd9c` and is meant to be carried into a session
opened in that repository. The one piece that IS gm-assistant work is User Story 5.

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

### User Story 5 - The GM's roll capture still reads the bot's posts (Priority: P2, gm-assistant)

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

## Decisions the request left open

Each is cheap to change after the fact; the plan proceeds on the stated reading.

1. **"void points and such."** Read as: the choices a player makes BEFORE a skill roll. On the
   sheet today, for a skill roll, void is the only one (the roll menu offers the roll and its void
   submenu, nothing else). So the one option is `void`. If the GM meant something further - a
   declared TN, say - it is one more option on the same commands.
2. **`/roll` completes skills only**, not knacks. The GM said "roll any skill"; rollable
   non-combat knacks (`/discern-honor`) are a natural next step and nothing here blocks them, but
   they were not asked for and are not added.
3. **Togashi Ise Zumi's two initiative variants**: `/initiative` rolls the default variant, the
   same "a slash command has nobody to ask, so it takes the plain roll" rule the sheet repository
   already applies to the Merchant's `/commerce`. An optional `variant` argument is the declined
   alternative - declined because it would show for every player to serve one school.
4. **A GM rolling on a pinned test character** spends that character's void like anybody else;
   the existing rule that such rolls leave no history row is unchanged.

## Offers, not requirements

- Completions could show the character's rank ("Sincerity (3)"). Not asked for, so not specified;
  raised with the GM once the feature works.

## Review history

Independent `spec-fidelity` review (constitution XVI), against gm-request.md as written.

- **Round 1 - CHANGES REQUIRED** (2026-09-20). Building it in the character-sheet repository, the
  per-roll void cap, FR-012 and User Story 5 were all found faithful. Four changes: FR-001/FR-002
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

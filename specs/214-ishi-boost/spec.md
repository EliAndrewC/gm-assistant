# Feature 214: the Isawa Ishi 3rd Dan boost, recorded with the roll it boosts

**Request**: [gm-request.md](gm-request.md) (two messages, 2026-10-03). **Status**: specified.

## Why

Tadashi's player is an Isawa Ishi. Third Dan (`rules/04-schools.md`, Isawa Ishi): *"After another
character makes a roll for which void points may be spent, you may spend one void point to roll Xk1
and add the result to their total, where X is your precepts skill. You may only do this once per
roll."* The GM wants that roll captured like every other roll, ATTACHED to the roll it boosts, and
added BEFORE the recording rules round it: a 13 Etiquette boosted by 8 is a 21 and is written as 20,
never as the already-written 10 plus 8.

## The shape, in one paragraph

The sheet app gains two ways to roll the technique - a Discord MESSAGE command run on the roll being
boosted, and the slash command `/ishi-3rd-dan-technique` - which roll Xk1 for the invoker's
character, spend the void point and post the result. gm-assistant's conversation watcher recognizes
a boost (from either command, from a pasted dice card, or typed), works out its target from the
message command or from a Discord reply, and adds it to that roll's raw total. A boost with no
target, or one that cannot be resolved to exactly one roll, is held, and `annotate()` asks which
roll it goes on, from a list of every roll in the conversation, annotated or not.

## Who builds what

- **gm-assistant** (this repository): recognition, targeting, the arithmetic, `annotate()`, the
  conversation's close rules. FR-001 to FR-012.
- **character-sheet** (<https://github.com/EliAndrewC/character-sheet>), by that repository's own
  Claude Code session, from a requirements document this session writes at
  `discord-design/ishi-boost-requirements.md` and leaves uncommitted (the 211 / 212 pattern) -
  since 2026-10-04 the issue <https://github.com/EliAndrewC/character-sheet/issues/2> instead, where the two sessions coordinate.
  This session cannot deploy that app. FR-013 to FR-018 (FR-017 deleted).

## User Scenarios & Testing

### User Story 1 - boost a roll by pointing at it (P1)

Jimen posts `13 etiquette`. Tadashi's player right-clicks it, Apps, "Ishi 3rd Dan boost". The sheet
bot posts `**Isawa Tadashi**: **8** Isawa Ishi 3rd Dan, boosting <link to Jimen's message>`. The
REPL prints that the boost landed on Jimen's etiquette (13 -> 21), and the next write records Jimen's
etiquette as 20.

**Acceptance**: (1) the boost lands on the roll the command was run on, with no GM input; (2) the
written value is computed from raw 13 + 8, never from a written 10; (3) a line already written to
Obsidian Portal is REPLACED with the boosted value on the next write.

### User Story 2 - a boost posted as a reply (P1)

Tadashi's player rolls the technique on the sheet page and pastes the dice card, or types `8 ishi`,
as a Discord REPLY to Jimen's roll. Same outcome as story 1.

### User Story 3 - a free-floating boost (P1)

Tadashi's player runs `/ishi-3rd-dan-technique`, or posts the card or the typed roll without
replying. The REPL prints that the boost is waiting. `annotate()` offers it, and choosing it lists
every roll in the conversation - annotated and not - in an arrow-key menu; the GM picks Jimen's
etiquette and it is boosted exactly as in story 1.

### User Story 4 - only once per roll (P2)

A second boost aimed at a roll that already has one is NOT added. It is held, and the REPL says why;
`annotate()` offers it with the already-boosted rolls left off the list.

### Edge cases

- The replied-to message holds several rolls (`30 investigation@3, 36 Interrogation@3`), or none
  that this conversation collected (a roll from before it opened, a chat message): held.
- The boost is the roller's own (Tadashi boosting Tadashi): the rule says ANOTHER character, so it
  is held and the REPL says why.
- The boosted roll is contested: the boost raises that side's raw total before the margin is taken.
  An interrogation roll: the exact written total includes it. An Oppose Social / Oppose Knowledge
  roll: the NPC's penalty is re-derived from the boosted total. A roll under Withdrawn: the ceiling
  still applies to the boosted total, as it does to any bonus.
- The conversation is closed when the boost is posted: nothing is collecting, so it is not seen.
  Recorded below as an accepted limitation.

## Requirements

### gm-assistant

- **FR-001** A boost MUST be recognized from: the sheet bot's message for either new command; a
  player's pasted dice card whose recorded roll is the Isawa Ishi technique (`roll_key`
  `spend_vp_xk1:isawa_ishi`); and a typed message giving a number beside "Ishi". Each carries the
  booster and the Xk1 total. A boost is never collected as a roll of some skill.
- **FR-002** The target MUST be taken from the message command's target message where there is
  one, else from the Discord reply the boost was posted as. A target that is exactly one roll
  collected by this conversation, by a different character, with no boost yet, is boosted with no
  GM input, and the REPL prints `+ Tadashi's Ishi 3rd Dan: +8 to Jimen etiquette (13 -> 21)`.
- **FR-003** A boost MUST add to the target's RAW total, so every recording rule - rounding to 5,
  the Etiquette cap, sheet ceilings, the contest margin, the exact interrogation total - applies to
  the boosted value. The bio is rewritten on the normal debounce, replacing what was written.
- **FR-004** Once per roll: a roll MUST NOT carry more than one boost.
- **FR-005** Every boost that is not applied by FR-002 MUST be held, with a printed reason.
- **FR-006** `annotate()` MUST offer each held boost. Choosing one lists every attributed,
  undiscarded roll in the conversation, annotated or not, except rolls that already carry a boost
  (FR-004); the GM picks one, or discards the boost. Staging, Ctrl-C and finish
  behave as for rolls.
- **FR-007** A held boost MUST keep `end_conversation()` from closing, as an unannotated roll does.
  The forced (interpreter-exit) close MUST name each held boost it is dropping.
- **FR-008** `cancel_boost()` MUST take back the most recent applied boost (or the named PC's) and
  return it to held, so a mis-aimed boost can be re-aimed in `annotate()` or discarded.
- **FR-009** The written line formats MUST NOT change: a boosted roll reads like any roll of its
  total.
- **FR-010** A boost on an Oppose Social / Oppose Knowledge roll MUST re-price the NPC's affected
  rolls, as a late oppose roll does (feature 208).
- **FR-011** A boost on an interrogation roll on a line of questioning MUST re-run the private
  who-won comparison, and a newly-detected verdict waits for the GM as any other does (2026-09-29).
- **FR-012** The REPL docs (`rolls/CLAUDE.md`) MUST describe the feature.

### character-sheet (specified in the handoff document)

- **FR-013** A Discord MESSAGE command, "Ishi 3rd Dan boost", and a slash command
  `/ishi-3rd-dan-technique` with no options. Both resolve the invoker's character as the 211
  commands do.
- **FR-014** Both refuse privately, with nothing rolled or spent, unless the character is an Isawa
  Ishi of 3rd Dan or higher with a void point available; otherwise they roll the existing
  `spend_vp_xk1` formula (Precepts k1), spend the one void point, and record the roll, in one
  commit.
- **FR-015** The public reply is `**<Name>**: **<total>** Isawa Ishi 3rd Dan`, followed for the
  message command by `, boosting <jump link to the target message>`.
- **FR-016** The recorded roll keeps the target message id, and `GET /api/rolls` returns it as
  `target_message_id` (null when there is none).
- **FR-017** (Deleted in review round 1: a refusal of a boost aimed at a boost message was not
  asked for; such a boost's target is not a collected roll, so FR-005 holds it.)
- **FR-018** Registration as for the 211 commands; deployment by the GM's character-sheet session.

## Decisions (each made by the session, each cheap to change)

1. **A message command instead of a reply-to slash command.** Discord drops the reply reference
   from a slash command, so `/ishi-3rd-dan-technique` "as a reply" would always arrive free-floating.
   The GM approved the substitution (message 2). The slash command stays, for the free-floating case.
2. **The boost is folded into `Roll.total`, with the amount and booster kept beside it** for
   `cancel_boost()` and the once-per-roll check. `total` is already the roll's total after the
   player's own bonuses and rounding is done at render time, so every consumer is right with no
   second code path. Declined: a separate field added at each of the dozen render sites, which
   would have to be remembered at every new one.
3. **A typed boost needs the word "Ishi" beside its number** (`8 ishi`, `Ishi 3rd Dan: 8`). "3rd
   Dan" alone also names the Ide Diplomat's subtracting technique, which is not this feature.
4. **The target link is read from the bot's message (the jump link) as well as from
   `/api/rolls`.** A roll the GM makes on a pinned test character is not recorded by the sheet app,
   so the link is the only thing that makes the command testable without a real player.
5. **"A roll for which void points may be spent" is left to the GM.** The sheet app cannot judge a
   hand-typed target, and every roll a conversation collects is a skill or knack roll, which can
   take void points; the exception (a Discordant roller) is the GM's to notice. A boost aimed at
   another boost's message is not refused by the sheet app either: its target is not a collected
   roll, so it lands in `annotate()`.

## Accepted limitation

**A boost posted after `end_conversation()` is not seen.** The watcher runs only while a
conversation is open, and the raw totals are not kept after it closes. Cost: the GM adds such a
boost by hand. Priced and declined: persisting every conversation's raw rolls so a closed one could
be reopened and rewritten - a second store of state for a case the GM's own description places
inside the conversation ("we record the etiquette roll in Obsidian Portal. And then someone says...").

## Success criteria

- **SC-001** 13 Etiquette + an 8 boost is written as 20 whether the boost lands before or after the
  first write.
- **SC-002** No roll is ever written with two boosts.
- **SC-003** Every pre-existing rolls test passes unchanged.

## Review history

- **Round 1 - CHANGES REQUIRED** (2026-10-03). Every clause of both messages found carried; the
  message-command substitution, once per roll, the held cases, `cancel_boost()` (the GM's standing
  `cancel_*` direction), Decision 5 and the accepted limitation upheld. Two changes: (1) FR-017, the
  sheet app refusing a boost of a boost, was unrequested and contradicted Decision 5 - deleted, here
  and in the handoff document; (2) FR-006 left the booster's own rolls out of the `annotate()` list,
  against "both rolls that have already been annotated and rolls that have not" - so a self-boost
  could only be discarded. Now only already-boosted rolls are left out; the self-boost is still
  HELD with its reason, and the GM decides in the menu.
- **Round 2 - FAITHFUL** (2026-10-03). Both round-1 changes confirmed, in the spec and in the
  handoff document (B2.3, Part 3), with nothing new introduced; every clause of both messages
  traced to a requirement and every requirement to the request, the approved plan or a standing
  GM direction.

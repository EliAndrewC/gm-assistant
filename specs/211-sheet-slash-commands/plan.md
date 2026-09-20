# Implementation Plan: `/roll`, per-skill commands, three rolled knacks, `/initiative`

**Feature**: `specs/211-sheet-slash-commands` | **Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

**BUILT IN <https://github.com/EliAndrewC/character-sheet>.** Every path below is in that
repository unless it says gm-assistant. Grounded in a read of it at commit `6c4dd9c` (2026-09-20),
which is bind-mounted in this container at `/host-l7r-repo/character-sheet` - the same tree the
GM's character-sheet container works in.

**THIS FEATURE STARTS AFTER THE SHEET FOUNDATION SHIPS** (GM message 2). The rules this feature
needs on the server, and the concurrency bug it would otherwise trip over, are specified in
`discord-slash-commands-requirements.md` at the root of the character-sheet repository. The GM's
sequence: that work is implemented and deployed by his character-sheet session; then this feature
is built on it. **Task 1 here is validating it landed** - by behavior, not by changelog - and the
answer to a missing piece is to say so, never to work around it (FR-019).

## What moved out of this plan

The first draft carried three large design sections - a server-side void spend, a server-side
initiative, and a fix for the open-tab overwrite. Those are now the character-sheet requirements
document's R1, R2 and R4, because they are that app's rules and that app's bug, not this feature's.
What is left here is the part that is genuinely about slash commands.

The file-and-line detail behind those findings is preserved in that document (its Part 0), so
nothing measured was lost in the handoff.

## What exists (measured at `6c4dd9c`, not remembered)

| piece | where | state |
|---|---|---|
| interactions endpoint | `app/routes/discord.py` | verifies, rolls inline, answers deferred (type 5), renders the card in a background task with retry. Handles interaction type 1 (ping) and 2 (command) only |
| command -> roll | `app/services/discord_commands.py` | `roll_key_for_command` maps any id in `game_data.SKILLS` to `skill:<id>`; `resolve_character` (GM pin, else the owned character in a gaming group); `_record` follows `should_record_roll` |
| server roller | `app/services/roll_engine.py` `execute_roll` | the unconditional roll only |
| registration | `scripts/register_discord_commands.py` | `--skills all` already registers one command per `SKILLS` entry; default is `etiquette` alone. No options on any command |
| skills | `game_data.SKILLS` | exactly the 18 non-combat skills. Combat lives in a separate `COMBAT_SKILLS`; iaijutsu is a knack. **Measured: the two are disjoint**, so a command set derived from `SKILLS` satisfies FR-003 by construction |
| the three knacks | `game_data.SCHOOL_KNACKS` + `dice.py` `build_knack_formula` | `oppose_social` (Water), `oppose_knowledge` (Air), `commune` (School Ring, via `SCHOOL_RING_KNACK_IDS`). All three already produce `knack:<id>` formulas; none is in `NON_ROLLABLE_KNACKS` |
| Commune's cost | `dice.py` l.1072 `requires_void_point=(knack_id == "commune")` | the flag exists server-side; only the BROWSER charges it (`_dice_js.html` `voidActivationCost`, `computeVoidOptions(reserve)`). Requirement R3.2 moves the charge to the server |
| read-only GM API | `app/routes/gm_api.py` | `GET /api/rolls`, `GET /api/characters`, bearer `ROLL_QUERY_TOKEN`. Requirement R5.1 adds current void, action dice and the per-roll cap to the character payload |

## Design

### D1. The command set

| command | rolls | options |
|---|---|---|
| `/roll` | any non-combat skill, chosen by autocompletion | `skill` (required, autocomplete), `void` (optional int) |
| one per skill - `/etiquette`, `/precepts`, `/sincerity`, ... | `skill:<id>` | `void` |
| `/oppose-social`, `/oppose-knowledge` | `knack:oppose_social`, `knack:oppose_knowledge` | `void` |
| `/commune` | `knack:commune` | `void` (on top of the activation point) |
| `/initiative` | `initiative` | none - FR-003a, the rules forbid void on it |

23 commands against Discord's per-application cap of 100.

The per-skill set is DERIVED from `game_data.SKILLS`; the knack set is an explicit allow-list of
exactly three ids, because the GM held the rest back by name (FR-018). A guard test asserts both:
registered names == `SKILLS` + the three knacks + `{roll, initiative}`, and no id from
`COMBAT_SKILLS` is reachable. So a future move of attack into `SKILLS`, or a fourth knack added
casually, turns the gate red instead of quietly registering a command.

`roll_key_for_command` grows a second branch: a hyphenated command name maps to the underscored
knack id (`oppose-social` -> `knack:oppose_social`). Discord requires lowercase names with no
spaces, which is why the command is hyphenated and the roll key is not.

### D2. Autocomplete (interaction type 4)

`routes/discord.py` gains a branch: type 4 -> respond type 8 with up to 25 choices,
**synchronously** - Discord does not allow deferral for autocomplete and requires an answer in 3
seconds, which a dict filter meets easily. Match is case-insensitive prefix first, then substring,
over skill names; 18 skills fit under the 25-choice ceiling with nothing typed. Choice `value` is
the skill id, `name` is the skill's name. (Rank in the label is an offer to the GM, not part of
this feature - see the spec's "Offers".) An autocomplete request never errors to the user.

`/roll` completes **skills only**. The three knacks have their own commands and the rest of the
knacks are deferred, so listing any of them would advertise a category this feature does not cover.

The submitted value is re-validated on the type-2 request, since a player can ignore the
completions and type free text: unknown -> ephemeral `CommandError`.

### D3. Rolling with void - a thin caller over the sheet's own services

Once requirement R1 lands, this feature implements no void rule of its own. `run_roll_command`
grows an optional void count and becomes a caller:

1. resolve the character (unchanged),
2. build the formula (unchanged),
3. compute the **activation cost** - 1 for `knack:commune` via the formula's existing
   `requires_void_point`, otherwise 0,
4. ask the sheet's void service to reserve `activation + requested`, which refuses when the
   character cannot pay or the request exceeds their per-roll cap,
5. roll with the requested spend,
6. commit the deduction and the `roll_history` row in ONE transaction.

A refusal raises `CommandError` before any dice are rolled, so the spec's all-or-nothing (FR-005)
is structural rather than a rollback. Refusal text names the number: "Commune costs a void point
and you have none", "You have 1 void point; you asked to spend 3".

**Ordering matters and is not arbitrary**: the activation point is paid off the top and the
optional spend is checked against what remains - matching `computeVoidOptions(reserve)`, so a
character whose cap is 3 but who holds 2 points can put exactly 1 into a Commune roll. Leave a
comment at the point of change saying so; this is the kind of ordering a later edit silently
inverts.

### D4. Knack availability

A character who does not have the knack has no `knack:<id>` formula at all - `build_all_roll_formulas`
emits formulas only for knacks they hold - so `execute_roll` already returns `None`. That becomes an
ephemeral "you do not have the Commune knack" rather than a generic failure (FR-017).

### D5. `/initiative`

Once requirement R2 lands, this is a caller too: ask the sheet for an initiative roll and a
start-of-round, then post the result. This feature implements no part of the keep-lowest rule, the
school adjustments, or what a new round resets.

The post: `**Name** rolls initiative - action dice: 2, 5, 7`, plus the dice card with
`show_total: false` (the renderer already supports this for initiative payloads).

### D6. Post formats, and why they are shaped that way

| roll | posted line |
|---|---|
| plain skill | `**Name**: **31** Sincerity@3` (unchanged) |
| with void | `**Name**: **38** Sincerity@3 (1 void)` |
| commune | `**Name**: **24** Commune (Water) (1 void to activate)` |
| initiative | `**Name** rolls initiative - action dice: 2, 5, 7` |

The parenthesized suffix is deliberate: gm-assistant's capture strips `(...)` spans before parsing
(`webapp/l7r/repl/rolls/parse.py`, `_BREAKDOWN`), so a void note cannot be misread as a second
roll. The initiative line puts no bare number in front of a skill word, so `_CLUSTER` has nothing
to match. Both are asserted by fixture rather than trusted to this paragraph.

## Where this feature's code gets written, and by whom

The commands live in the character-sheet repository, which this container has mounted but must not
run git against (project rule: edits under `/host-l7r-repo` are legal, git writes are not). So the
assumption is: **gm-assistant's session edits that working tree and the GM commits**, exactly as it
already does for `l7r.md`.

The alternative - folding the command layer into the requirements document so the GM's
character-sheet session builds all of it - is cheaper in coordination and costs this feature its
reason to exist. It is worth one line from the GM before T002 starts, and nothing before T001
depends on the answer. **Either way, two sessions must not edit that tree at the same time**; T001
checks that the sheet session is finished before anything here touches a file.

## Constitution check (gm-assistant's, as far as it reaches)

- **XVI (literal thing)**: no exceptions carved. The knack allow-list is exactly the GM's three,
  and FR-018 records what is being held back and on whose instruction.
- **XIV (fix defects where you find them)**: the two findings are not deferred, they are specified
  to the app that owns them, which is the only place either can be fixed correctly.
- **X / no second implementation**: after R1 and R2 this feature contains no dice or void rule of
  its own. That is the whole point of the handoff.
- **Record the why / declined alternatives**: D1's allow-list, D3's ordering, D6's post shapes, and
  the section above on who edits what.

## Rollout

0. **The GM's character-sheet session implements the requirements document and deploys.** Not this
   feature's work.
1. **T001 validation.** Behavior checks against the deployed app. A missing requirement stops the
   feature and is reported (FR-019).
2. Per-skill commands with `void`, registered to the test guild ("Robot Role Call").
3. The three knack commands, `/commune` last since it is the one with an activation cost.
4. `/roll` autocomplete.
5. `/initiative`.
6. Register globally (about an hour to propagate).
7. gm-assistant: capture fixtures for the new post shapes.

## Open items for the GM (none block T001)

- Who writes the command layer - this session editing the mounted tree, or the character-sheet
  session from an expanded requirements document? See the section above.
- Commune's ring: the sheet pins it to the School Ring, the rules text says the element being
  questioned. Raised as open question 1 in the requirements document.

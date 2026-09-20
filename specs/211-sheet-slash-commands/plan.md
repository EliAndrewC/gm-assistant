# Implementation Plan: `/roll`, per-skill commands, `/initiative`, and void spends that reach the sheet

**Feature**: `specs/211-sheet-slash-commands` | **Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

**BUILT IN <https://github.com/EliAndrewC/character-sheet>.** Every path below is in that
repository unless it says gm-assistant. Grounded in a read of commit `6c4dd9c` (2026-09-20). That
repository does not use spec-kit; it keeps design documents (`import-design/`,
`profession-design/`) and a long CLAUDE.md. Carry this file and [tasks.md](tasks.md) into a session
there; the natural home is a `discord-design/` directory beside the others.

## Summary

Three things are easy and one is not. Registering 18 per-skill commands is a flag that already
exists. `/roll` with autocomplete is one new interaction type. The void option on a skill roll is
`rolled += n; kept += n` on a formula the server already builds. **What is not easy is that void
spending and initiative are today implemented in the BROWSER** - the server has never deducted a
void point or computed an action die - and that an open sheet tab saves its whole local tracking
state back to the server, so it will overwrite whatever a command wrote. Most of this plan is about
those two facts.

## What exists (measured, not remembered)

| piece | where | state |
|---|---|---|
| interactions endpoint | `app/routes/discord.py` | verifies, rolls inline, answers deferred (type 5), renders card in a background task with retry. Handles type 1 (ping) and type 2 (command) only |
| command -> roll | `app/services/discord_commands.py` | `roll_key_for_command` already maps ANY id in `game_data.SKILLS` to `skill:<id>`; `resolve_character` (pin, else owned+grouped); `_record` follows `should_record_roll` |
| server roller | `app/services/roll_engine.py` `execute_roll` | the unconditional roll only. Docstring says why: "no void spends ... a slash command has nobody to ask" - this feature changes that premise for PRE-roll choices, which an option can carry |
| registration | `scripts/register_discord_commands.py` | `--skills all` already registers one command per `SKILLS` entry; default is `etiquette` only. No options on any command |
| skills | `game_data.SKILLS` | 18, all social/knowledge. Combat rolls (attack, parry, ...) are not in `SKILLS`, so "leave out combat skills" is already true of the table the commands derive from |
| initiative formula | `app/services/dice.py` `build_initiative_formula` | rolled/kept plus FLAGS (`kakita_phase_zero`, `shinjo_4th_dan`, `hiruma_4th_dan`, `togashi_athletics_extra_die`, `mantis_4th_dan_athletics_die`) that "the client applies after rolling" |
| initiative post-processing | `_dice_js.html` ~l.2759-2818 | keeps LOWEST dice, applies the flags, builds `[{value, athletics_only?, mantis_4th_dan?}]`, calls `setActionDice` |
| new-round reset | `_tracking_js.html` `setActionDice` | replaces `actionDice` (all `spent: false`), `resetMantisRound()`, clears `kakita_5th_dan_used`. Does NOT clear `precepts_pool` |
| void allocation | `static/js/roll_math.js` `allocateVoidSpend` | temp first, then regular, then worldliness; reports `short` |
| void consequences | `_dice_js.html` `deductVoidPoints` | Ide 5th Dan (temp VP back), Yogo Warden 3rd Dan (heals light wounds), Matsu 3rd Dan (banks wound-check bonuses) |
| void per-roll cap | `app/routes/pages.py` ~l.752-778 | `void_spend_config`: cap = lowest ring (shugenja: lowest ring - 1); `worldliness_max` from the knack. Built inline in the page route, not callable |
| sheet state | `models.Character` | `current_void_points`, `current_temp_void_points`, `action_dice` JSON, `adventure_state` JSON |
| tab save | `_tracking_js.html` `save()` -> `POST /characters/{id}/track` | posts the tab's ENTIRE local tracking state, including void and action dice |

## Design

### D1. Commands and options

- Per-skill: one command per entry in `game_data.SKILLS`, 18 today, each with one optional integer
  option `void` (min 0, max 10; the real limit is enforced server-side because it is per-character).
  **Measured 2026-09-20**: `SKILLS` holds exactly the 18 non-combat skills; the combat ones live in
  a separate `game_data.COMBAT_SKILLS` and iaijutsu is a knack, so the two tables are disjoint.
  Deriving the command set from `SKILLS` therefore satisfies FR-003 by construction rather than by
  a filter somebody has to remember - and the guard test asserts the disjointness directly, so a
  future move of attack into `SKILLS` turns the gate red instead of quietly registering `/attack`.
- `/roll`: required string option `skill` with `autocomplete: true`, plus the same `void`.
- `/initiative`: no options (spec FR-003a - the rules forbid void on initiative - and Decision 3).
- 20 commands against a cap of 100. The registration script's default becomes the full set, derived
  from `SKILLS` - a guard test asserts registered names == `SKILLS` + `{roll, initiative}` and that
  no combat roll key is reachable, so the list is never hand-maintained.

### D2. Autocomplete (interaction type 4)

`routes/discord.py` gains a branch: type 4 -> respond type 8 with up to 25 choices, synchronously
(no deferral is allowed for autocomplete, and it must answer in 3 s - it is a dict
filter). Match = case-insensitive prefix first, then substring, over skill names. 18 skills
fit under the 25-choice ceiling with nothing typed. Choice `value` is the skill id; `name` is the
skill's name. (Showing the character's rank in the label is an offer to the GM, not part of this
feature - spec "Offers".) An autocomplete request never errors to the user.

The submitted value is validated again on the type-2 request (a user can type free text and
ignore the completions): unknown -> ephemeral `CommandError`.

### D3. Void on a skill roll - move the rule to the server, once

New `app/services/void_spend.py` (pure, 100% covered):

- `void_spend_config(character_data) -> dict` - EXTRACTED from `pages.py`, which then calls it.
  This is the no-second-implementation rule applied inside the repo: the page and the bot read the
  cap from one function.
- `allocate(count, temp, regular, worldliness_avail) -> Allocation` - Python mirror of
  `allocateVoidSpend`. It is five `min()` calls; like the total cap in `roll_engine.py` it cannot
  be shared across the language boundary, so it is pinned the same way: the cases in
  `tests/js/roll_math.test.js` are asserted verbatim in `tests/test_void_spend.py`.
- `apply_spend(character, allocation, school_abilities) -> None` - mutates the model: the three
  pools, then the Ide / Yogo / Matsu consequences. **RESEARCH FIRST (T001, T002)**: whether worldliness
  may fund a plain skill roll, and where `matsuBankedWcBonuses` persists, were not settled by this
  read. Read `executeRoll`'s void branch (~l.1970-2090) end to end before writing this.

`execute_roll` gains `void_spent: int = 0`: `rolled += n`, `kept += n`, `formula["void_spent"] = n`
- exactly the three lines the browser runs (`_dice_js.html` l.5973-5976), with the 10k10 overflow
handled by whatever the formula layer already does for it (verify; do not invent). The payload
gains the same `void_spent` marker the browser's payload carries, so the dice card and the
roll-history page render a Discord spend identically.

Order inside `run_roll_command`, all in ONE transaction: resolve character -> build config ->
refuse if `void > cap` -> allocate -> refuse if `short` -> roll -> apply spend -> record -> commit.
A refusal raises `CommandError` before any dice are rolled, so FR-005's all-or-nothing is
structural, not a rollback. Refusal text names the number: "You have 1 void point; you asked to
spend 3."

Post text: `**Name**: **31** Sincerity@3 (1 void)`. The parenthesized suffix is deliberate -
gm-assistant's capture strips `(...)` spans before parsing (`parse.py` `_BREAKDOWN`), so the
existing parser reads this line correctly today.

### D4. Initiative - same move

New `app/services/initiative.py` (pure): `action_dice_from_roll(formula, dice, rng) -> list[dict]`
mirroring the browser block: sort kept ascending -> Hiruma (-2, min 1) -> Shinjo (highest := 1) ->
Kakita (10 -> 0) -> re-sort -> Togashi extra athletics die (one more d10, `athletics_only`) ->
Mantis fixed value-1 die. `roll_dice` keeps HIGHEST today; initiative keeps LOWEST - add a
`keep_lowest` parameter rather than negating values. Pinned against the browser by extracting the
browser block into a `roll_math.js` function (`initiativeActionDice`) with a shared case table, the
pattern the repo already uses for the total cap. That extraction is the one browser-side change
this feature makes to existing behavior, and it is a pure move.

`start_round(character, dice)` - the server's `setActionDice`: `action_dice = [{..., spent:
False}]`, clear the Mantis round keys and `kakita_5th_dan_used` from `adventure_state`, leave
`precepts_pool` alone. **RESEARCH FIRST (T003)**: enumerate every key `resetMantisRound()` touches
and where each persists; the JS is the specification.

The post: `**Name** rolls initiative - action dice: 2, 5, 7` plus the dice card with
`show_total: false` (the renderer already supports this for initiative payloads). No number sits
directly before a skill word, so gm-assistant's `_CLUSTER` has nothing to match; T025 proves it
with a fixture rather than trusting this sentence.

Recorded as roll key `initiative` with `action_dice` in the payload, the shape the browser already
posts.

### D5. The open-tab overwrite - the real risk (FR-012)

`save()` posts the tab's whole tracking state. A player with the sheet open who runs
`/sincerity void:1` and later clicks anything that saves will write their stale void count back,
silently refunding the point. Same for action dice. Discord-side writes make a latent
last-writer-wins design into a visible bug.

Chosen: **a revision counter on tracking state.** `Character.tracking_rev` (int). `/track`
requires the rev the tab loaded; a mismatch returns 409 with the current state, and the tab
adopts the server's values and tells the player ("updated from Discord"). Every server-side writer
(the two new services) bumps it. Declined alternatives, with reasons:

- *Field-level PATCH instead of whole-state POST* - the right long-term shape, but it rewrites
  every tracking call site in a 5,000-line template. An overhaul; out of proportion here.
- *Polling / server-push so tabs stay fresh* - reduces the window, does not close it, and a Fly
  machine that scales to zero should not be held open by polls.
- *Do nothing, document it* - fails the GM's plain requirement that the spend "actually" lands.

The counter also fixes the same bug between two browser tabs, which exists today.

### D6. Authorization (FR-011)

`resolve_character` returns a character the invoker OWNS or one the GM pinned, so the invoker can
always edit it; no new path to someone else's sheet is opened. Asserted by test rather than assumed:
the spend path calls the same can-edit predicate the `/track` route uses, so a future change to
`resolve_character` (say, editors rolling for a character) cannot quietly become a write hole.

### D7. gm-assistant side (User Story 5)

After the sheet work is deployed and real posts exist: save one real post of each new shape as a
fixture under `webapp/l7r/repl/rolls/`, assert skill/total/rank parse and that the initiative post
yields no roll. `conversation.py` already recognizes the sheet bot as author. Expected code change:
none; expected deliverable: the fixtures that prove it.

## Constitution check (gm-assistant's, as far as it reaches)

- **XVI (literal thing)**: no exceptions carved; the six open decisions are in the spec and the
  spec is fidelity-reviewed.
- **X / no second implementation**: D3 and D4 extract-and-share inside the owning repo; mirrors
  across the JS/Python boundary are pinned to shared case tables.
- **Record the why / declined alternatives**: D5.
- **Guidelines as tests**: the registered-command set, the void ceiling and the mirror parity are
  each an assertion, not a sentence.

## Rollout

1. Land D5 (tracking rev) first and alone - it is a fix to existing behavior and is testable
   without Discord.
2. D3 + per-skill commands with `void`, registered to the test guild ("Robot Role Call").
3. `/roll` autocomplete.
4. D4 `/initiative`.
5. Register globally (about an hour to propagate); then the gm-assistant fixtures (D7).

## Open items for the GM (none block starting)

- Decision 1: does "and such" mean anything beyond void?

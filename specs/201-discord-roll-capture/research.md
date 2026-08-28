# Research: what the real Discord corpus contains

Measured 2026-08-28 against 1,400 real messages (700 from each channel; Monday
`case-of-the-mondays` back to 2025-06-25, Tuesday `a-team` back to 2026-06-30), read with the
project's read-only bot token. The raw corpus is cached at `webapp/opcache/discord-history.json`
(gitignored); the committed fixture is `webapp/tests/fixtures/discord/messages.json` - 615 messages,
every one that contains a digit or an image attachment, with author ids and display names
pseudonymized. Pure chatter is excluded: it is trivially rejected by any parser and is the players'
private conversation, not test data.

## R1. The filename cannot identify a dice card - so the join is the detector

Clipboard pastes arrive as `image.png` (204 of them). The sheet app's download path yields
`l7r-roll.png` (22). But ordinary images in the same channels are *also* `image.png`, along with
`Z.png`, `9k.png`, `Untitled.jpg`, `DO9RO_1XcAAK8oE.png`. No filename test, and no image-content
test short of OCR, separates a roll from a meme.

**Decision**: never classify an image. Ask the character-sheet app whether a roll exists for that
author within the match window. A hit means it was a dice card; a miss means it was a picture. This
is the single strongest reason the endpoint is worth building, and it makes FR-008's "ignore
silently" correct rather than lossy - an unmatched image is *evidence of nothing*.

## R2. Typed rolls are a primary path, and the split is per player

204 image posts against ~99 typed roll messages. The division is by PERSON, not by group: on
Tuesday four players post images almost exclusively while one types (34 typed / 6 images); on
Monday two players are text-first (33 and 23) while three are image-first (32, 28, 18). Any design
that treats typed rolls as a fallback gets a third of the data wrong for everyone, and nearly all of
it wrong for three specific players.

## R3. The observed typed forms, including the ones found late

The first survey found the obvious shapes:

```
38 Etiquette @3
23 Investigation@2
52 law@3 to argue that under the circumstances...
43 Interrogation@3 (38 + 5 Discerning)
10->10->10->4  10->8 5 4=61+5=66 Sincerity@1
10->9 8 +5 Streetwise = 32 Law@2
10->7 10->7 8 8 +15 65@4 Intimidation        (rank before the skill)
15 etiquette (24, limited by Withdrawn)      (cap already applied by the player)
15@1                                          (no skill named)
30 investigation@3, 36 Interrogation@3: ...   (two rolls, one line)
```

A second pass over the messages that had a number but *no* `@rank` found forms the first pass had
misfiled as non-rolls, which is why the fixture is not pre-labeled by regex:

```
24 eti            22 eti           (abbreviated skill names)
35 Interrogation                    (no rank at all)
67 after boni                       (total, no skill, prose)
roll of 36, +2h, maybe +5 hayato, spending 4 3rd dans and 5 conv = 68
31+15acting+10 for two free raises from saved free raises in spirit encounter +4 conv
27      15      53      25      17  (bare numbers, skill supplied by conversational context)
```

A third pass, over a two-day window pulled live, found two more:

```
20 Underworld at 2                  ("at N" as a spoken alias for "@N")
26@3 Etiquette                      (total@rank, THEN the skill name)
47 Etiquette@3 assuming streetwise counts
6 9 6 9        1, 1, 2, 5.  Sigh    (loose dice, not totals - must NOT parse)
```

`26@3 Etiquette` and `65@4 Intimidation` confirm the `<total>@<rank> <skill>` order, which in turn
explains `@27 Tact`: the player typed the `@` from habit with no rank to give, and 27 is the total.
The magnitude rule in R4 reads all three correctly without a special case.

**Decision**: require a recognized skill name adjacent to the number. A bare number is NOT parsed as
a roll - see R5 for why that is a correctness requirement and not conservatism.

## R4. `@N` is overloaded; the rules settle it

`@N` almost always means the character's skill RANK. One observed message reads `@27 Tact`, where
27 is plainly a total.

Skills are capped at rank 5 (`rules/01-character_creation.md:49`: *"Every skill begins at 0 and must
be raised 1 point at a time, to a maximum of 5"*), and the one knack that raises a rank mid-roll
also stops at five (`rules/05-school_knacks.md:139`). So:

- `@N` where N <= 5 -> rank
- `@N` where N >= 10 -> total
- 6 <= N <= 9 -> genuinely ambiguous; surfaced to the GM, never guessed

The gap is deliberate. No observed total is below 10, and no rank can exceed 5, so the band between
them is empty in practice - but it is empty by luck rather than by rule, so the parser reports
rather than assumes.

## R5. The negatives are adversarial, which is what makes the corpus worth keeping

Messages that contain numbers and are NOT rolls include:

```
We started this one on 06/20/2023
Looks like the Hidden Way Campaign ended on 22 December 2022
There were 85 sessions in the Tuesday group's Karmic Inquisitors Campaign.
Wakku rn is Fire 5, Air 4, Water 6, Void 5, and 8 Earth (15 serious able to be taken)
It doesn't look like the Unkept disadvantage is tracking the -10 to Culture
It worked!  >>> xky(6, 5)  [1, 3, 4, 6, 7, 8]  28
```

Note the last one: the GM's own REPL output, pasted into the channel, containing dice and a total.
And note `Wakku rn is Fire 5, Air 4, ...` - ring names with numbers, which a loose
`<number> <word>` rule would read as five rolls. These are the reason SC-003 is stated as a
measurable outcome over the whole corpus rather than a handful of unit tests.

## R6. The skill vocabulary comes from the rules, not from a hand-kept list

`rules/02-skills.md` "## Skill List" holds the canonical 18: bragging, etiquette, intimidation,
sincerity, sneaking, tact, Acting, Interrogation, Manipulation (social); culture, heraldry,
investigation, law, precepts, strategy, Commerce, History, Underworld (knowledge). Combat adds
attack and parry (`rules/03-combat.md:23`).

**Decision**: derive the list by reading that section, rather than copying it here. The project
already treats those files as canonical for any rules question, and a copied list is a second
source that goes stale silently. Abbreviations (`eti`) resolve by prefix match against that list,
with an ambiguous prefix reported rather than guessed - the same discipline as R4.

The character-sheet app has its own `SKILLS` registry plus `_SKILL_ALIASES` and a fuzzy matcher
(`app/services/import_match.py`). We deliberately do NOT reach for it: that is the rules ENGINE, it
lives in another repository, and the typed path must work when that app is unreachable. The skill
list is data available in the l7r repo already mounted here; the engine is not.

## R7. The GM's own rolls are NPC rolls

The GM posted 14 rolls on Monday and 6 on Tuesday. A contested roll is scored from both sides, so
filtering the GM out would silently discard half of every contest. Nothing in the pipeline may treat
the GM's Discord id as special.

## R8. Rounds are tight, which makes time-bounded grouping viable

The etiquette round the GM cited as the motivating example spans 33 seconds end to end (5 rolls,
01:53:39 to 01:54:12), four pasted images and one typed message. Grouping by conversation open/close
is comfortably coarse enough; no per-round heuristic is needed.

## Open question for the GM (does not block implementation)

Bare-number messages (`27`, `15`, `53`) and skill-less totals (`67 after boni`) are rolls whose
skill is supplied by conversational context a parser cannot see. They are currently dropped with a
report. If they turn out to be common enough to matter, the cheap fix is for the GM to name the
skill when opening the conversation, so a bare number inherits it - but that is a rule the GM
should choose, not one this feature should assume.

## R9. `before` and `after` are mutually exclusive in the Discord API

Verified live: passing both `after` and `before` to `GET /channels/{id}/messages` silently honors
only one - a request bounded at both ends returned 100 messages running hours past the `before`
value. Discord treats `around`/`before`/`after` as alternatives, not as a range.

**Decision**: fetch with `after` alone and bound the far end client-side. A conversation's start
time converts directly into a snowflake - `((unix_ms - 1420070400000) << 22)` - so no message id is
needed to begin polling from the moment the GM opened the conversation. Verified against the
motivating etiquette round: a synthesized snowflake for 01:53:00Z returned the round starting at
01:53:39Z.

This also means paging is one-directional and naturally incremental, which suits a poller: keep the
last seen message id, ask for everything after it, stop when the page comes back short.

## R10. "Directly underneath the portrait" has a concrete anchor

Verified against the live campaign. A character's public `bio` opens with a Textile file embed
carrying the full-body portrait:

```
[[File:1515940  | class=media-item-align-none | Tsuruchi.png]]
```

**Decision**: the roll line is spliced immediately after that embed line, which is literally what
the GM asked for. When a record has no embed, the line goes at the top of the bio - the spec's
existing edge case, now confirmed as the real fallback rather than a hypothetical one.

Two API facts found while establishing this, both of which cost a wrong turn first:

- `op.get_character_body()` takes the character **id**, not the slug. A slug returns 404 from an
  otherwise-healthy endpoint. `discern_honor` already passes the id correctly; this note exists so
  the next reader does not diagnose a 404 as a broken endpoint the way this session briefly did.
- The characters LIST endpoint returns `bio`, `description` and `game_master_info` as KEYS but
  leaves them EMPTY for every character - 0 of 119 populated. The body fields only arrive from the
  per-character fetch. A design that assumed one list call could supply bios would appear to work
  (the keys are present) and silently see nothing anywhere.

## R11. Measured end to end against the live channel, with the endpoint absent

Run 2026-08-28 against the GM's motivating etiquette round (Tuesday channel,
2026-08-12 01:53:39-01:54:12Z, five rolls in 33 seconds), reading Discord live and stubbing only
the character-sheet client to report what it will actually report until the endpoint is built:

```
fetched 6 live messages in the window
rolls captured: 1
  ShosuroAjo: etiquette 38 (rank 3, typed)
LINE: ShosuroAjo etiquette: 35
unresolved (5):
  ! recorded rolls unavailable (endpoint not built yet)
  ! image from originaljack at 01:53:39 could not be resolved
  ! image from Queen of Rats and Crows at 01:53:58 could not be resolved
  ! image from auxarc at 01:54:09 could not be resolved
  ! image from HamburgerOfJustice at 01:54:11 could not be resolved
```

This is the intended shape of the degraded mode, not a shortfall: the typed roll is captured and
correctly recorded as 35, and each unresolvable image is named with its poster and time so the GM
can transcribe those four by hand exactly as they do today. When
`/api/rolls` exists, the same run yields all five and the line becomes the GM's full example.

Worth stating plainly because it sets expectations for the first live test: **until the
character-sheet endpoint ships, this feature captures roughly a third of the rolls** - the typed
ones - and tells the GM precisely which ones it missed.

## R12. The line's ORDERING - inferred, then CONFIRMED

The GM's single worked example reads `35 / 25 / 25 / 20 / 15` - perfectly descending. Five rolls
land in descending order by chance about once in 120 times, so `render_open` was written to sort
highest-first, against the competing reading that `Sadakichi / Moriko / Jimen / Tetsuro /
Toshihiro` was a habitual party order.

**Confirmed by the GM 2026-08-28**: *"ordering rolls from highest to lowest is intentional"*. The
inference was correct. It is now an instruction rather than a guess, recorded at the sort in
`rules.py` so nobody restores posting order.

## R13. There is no contested etiquette roll, so the cap's scope is not a gap

The fidelity review flagged that FR-011 caps OPEN etiquette only - the GM's literal scope - while
the GM's stated reason (politeness has a ceiling) would seem to apply to a contested etiquette roll
too, and suggested confirming it.

**The GM closed it rather than narrowing it** (2026-08-28): *"there is no contested etiquette so
that can't happen."* The uncovered case does not exist in the game, so the scoping needs no guard
and no follow-up. Recorded because the question looks live to anyone reading the rule, and this is
the kind of thing that gets "fixed" by a later session that has not asked.

## R14. Attribution has exactly one source, and it is the endpoint

The parser reads a typed roll without any character-sheet endpoint, but it cannot say WHOSE roll it
is - all Discord gives is an account id. Checked 2026-08-28 for an existing source:

- The sheet's public index page (already scraped by `chargen/sheetroster.py`) carries character
  names and gaming groups, but no owner Discord ids.
- Obsidian Portal holds no Discord ids at all.

**The GM's ruling** (2026-08-28): *"The L7R character sheet app knows who plays whom."* So
`/api/characters` is the source, and it is on the critical path for BOTH input paths rather than
just the image one - which raises its priority above where this feature's plan first placed it.

`[discord_players]` in the gitignored secrets remains as a testing stopgap only. It is explicitly
NOT to be maintained by hand, and should be deleted once the endpoint ships.

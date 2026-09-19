# `l7r.repl.rolls` - Discord rolls into an NPC's Obsidian Portal record

The GM plays online; players post their rolls in Discord; the GM used to transcribe them into the
NPC's record by hand. This package removes the transcription. At the prompt:

```python
>>> begin_conversation("Otsuki")
Talking to Otsuki, watching every monitored channel. Rolls until end_conversation().
>>> end_conversation()
Otsuki: Sadakichi / Moriko / Jimen / Tetsuro / Toshihiro etiquette: 35 / 25 / 25 / 20 / 15
```

**One argument is the whole interface.** With no channel named, a conversation watches EVERY
monitored channel, so a roll posted anywhere lands - the two live game channels belong to groups
that play on different nights, so watching both cannot mix two sessions in practice. Pass a channel
(`begin_conversation("Otsuki", "test")`) only to narrow it, which is really for the scratch server.
Cursors are kept PER CHANNEL, and one unreadable channel never hides another's rolls.

Which NPC the players are talking to is the ONE thing that cannot be inferred, so it is the one
thing the GM says. `end_conversation()` writes immediately - no confirmation step, because a
"does this look right?" prompt would put back the manual step the feature exists to remove.

**A background watcher polls while the conversation is open** (`start_watching`, a daemon thread on
`shell.py`'s warm-cache pattern). It prints each roll the moment it sees one and updates the
Obsidian Portal record on a debounce - the GM's own shape: *"it would be nice to see something
indicating that the roll was seen, and then maybe we debounce so that within 2 minutes we update
with the latest set of rolls."* The FIRST write is immediate (seeing the line appear once proves
the path works); everything after it coalesces on `WRITE_DEBOUNCE_SECONDS`. Each write REPLACES the
conversation's previous lines via `bio.rewrite` rather than stacking another line under the
portrait, and a conversation spanning several skills writes one line per skill.

| file | holds |
|---|---|
| `models.py` | `Roll`, `Contest`, `RecordingRule`, `Conversation`. Pure data. `Roll.total` is deliberately NOT decomposed into dice plus bonuses - the character-sheet app owns the dice math and we never reimplement it. |
| `rules.py` | The GM's RECORDING rules (not game rules): round down to 5, cap Etiquette at 40 before rounding, contested keeps both totals raw and rounds only the margin, and only the PERSONAL name is written (`Tsuruchi Jimen` -> `Jimen`, `personal_name`). The GM's reasoning for the cap is in the module docstring - **do not delete it**, the rule is meaningless without it. `render_open` reproduces the GM's shorthand exactly. |
| `skills.py` | The skill vocabulary, READ from `/host-l7r-repo/rules/02-skills.md` rather than copied, so a rename in the rules reaches us - plus the single-word school knacks that declare a ring (`05-school_knacks.md`; `31 pontificate` parsed to nothing until feature 207), each skill's ring, and which are advanced. Unambiguous prefixes resolve (`eti` -> `etiquette`); an ambiguous one is reported, never guessed. |
| `parse.py` | Hand-typed rolls. The forms are wilder than they look - see the module docstring for the fifteen real shapes. A number is a roll ONLY when a real skill name sits beside it; that one rule kills nearly every false positive, and the three that survived it are each pinned by a test. |
| `bio.py` | Splices lines directly under the `[[File:...]]` portrait embed. `rewrite` swaps this conversation's previous block for its current one - the watcher writes repeatedly, so appending would stack a line per poll. Removing a line takes the blank line spliced with it, or the body grows a newline every write. |
| `discord.py` | Read-only REST. The bot holds permissions 66560 (View Channel + Read Message History) and there is no code here that could post. Snowflakes are synthesized from a timestamp; `before`/`after` are mutually exclusive in the API, so the far end is bounded in Python. |
| `sheet.py` | The character-sheet app's roll-history client. **THOSE ENDPOINTS DO NOT EXIST YET** (spec: `character-sheet/externally-queryable-roll-results.md`). Every failure degrades to empty with a reason; nothing raises. |
| `console.py` | (Feature 210: while a menu is open it is the console's OVERLAY - an announcement erases the whole list, prints, and redraws it unmoved; and `asking()` makes a typed roll prompt redraw as ITSELF rather than as `>>> `, a defect found on the way.) `print_above` - writes from the watcher thread WITHOUT stomping the prompt: `\r\x1b[K` erases the prompt line, the message goes there, then the prompt and whatever the GM had typed are redrawn beneath it. TTY only; a pipe gets a plain print. |
| `annotate.py` | The `annotate()` menu. **What it asks depends on the skill's MODE** (`modes.py`, feature 207): always-open skills are asked only what the roll was for; default-open ones arrive with open SELECTED and a two-press keystroke undoes it; manipulation and sneaking go straight to the opposing roll (`f` = 15 no roll made, `n` = nobody opposed it, `t` = type a total); acting takes a HIDDEN opposing roll and an outcome; everything else keeps open (`o`), contested (`c`), discard (`d`), open with a bonus (`ob`); an INTIMIDATION roll is then asked how the NPC appeared (feature 209). A GM roll TAGGED with the opposing skill is paired without asking. An INTERROGATION roll reaches the menu only when it is on no line (join a declared line, or discard) or has no rank. Ctrl-C discards EVERYTHING staged in that run, which is the literal reading of the GM's "not save anything" and the behavior most likely to sting. Blank finishes and commits. |
| `modes.py` | What each skill's roll MAY be - one mode per vocabulary entry, and a test that reads the rules file fails when a skill has none. Also the default OUTCOMES and the manipulation default of 15. Written out rather than derived: each row is a ruling. |
| `npcnumbers.py` | PURE. The NPC's rings and ranks: the `NPC numbers:` block in the GM-only notes, reading a pool into ring + rank (less school dice and declared void points), the disagreement and its void point answer, and the acting/history automatic raises. Schools with an extra die are PARSED from the rules. |
| `npcskills.py` | `tact`, `sincerity`, ... at the prompt: `xky(5, 3) - tact` tags a roll, `tact()` / `tact(2)` / `tact(5, 3)` / `tact(vp)` roll for the NPC. The disagreement prompt, where Ctrl-C is an ANSWER (the roll was a mistake). `acting(2)` and `history(3)` record and never roll. |
| `lines.py` | `new_line_of_questioning`, `grilling`, `detected`, and `cancel_grilling` / `cancel_detected` (feature 208). Replaces 206's join-or-new menu. |
| `hidden.py` | PURE. The `Hidden rolls:` block in the GM-only notes - each line's Sincerity roll, each acting roll's opposing investigation - and the advisory who-won arithmetic. **Nothing here may reach the bio**; `tests/test_rolls_hidden.py` renders both halves from one conversation and checks. |
| `oppose.py` | PURE. Feature 208: a player's Oppose Social / Oppose Knowledge taxes the NPC's later Air / Water rolls. The penalty in effect is DERIVED from the conversation's rolls (highest live oppose roll at or before the moment - never stored, never summed); `for_line` is the one retroactive case; `settle` re-prices tagged GM rolls when an oppose roll is collected late. |
| `menu.py` | Feature 210: the arrow-key list every CHOICE prompt uses (`ask_choice`). `Picker` is the pure state and drawing; `choose` is the key loop; `interactive(ask)` decides whether a prompt is a menu at all. An `Option.key` is the answer the GM would have TYPED, which is why call sites have no second code path. |
| `keys.py` | The two-press undo: one key read in cbreak mode BEFORE readline gets the line, then handed back as the line's first character. |
| `conversation.py` | The only stateful module: open, collect, close, write, plus the background watcher. `_tick` is one poll - collect, announce, maybe write - split out so the debounce is testable without threads. Boundaries are injected as callables, the way `discern_honor` takes `characters=` / `get_body=` / `update=`. |

## What a written line looks like, and the two orders that must stay different

```
Tetsuro / Toshihiro / Sadakichi / Jimen / Moriko etiquette: 30 / 20 / 20 / 15 / 15
10 tact: Jimen - asking how much money Fumitake owed
Jimen vs Otsuki precepts: 41 vs 28, Jimen wins by >=10 arguing it is wrong to lie to a magistrate
Jimen vs Otsuki sincerity vs interrogation: 30 vs 30, Otsuki wins by <5 denying he was ever there
interrogation (grilling): 37@2 Jimen / 24@1 Moriko - what Fumitake ordered his escorts to do
interrogation: 25@2 Jimen - what Fumitake thinks of Tsuruchi
```

**Personal names only** (GM 2026-09-02). The full name is what joins a Discord account to a
character, dedups a pasted card against a typed roll, and matches the sheet bot's `**Name**:`
prefix - so it is trimmed at the moment of WRITING and nowhere earlier. The rule is the naive
last-token one and it is naive on purpose; the reasoning, including why there is no roster lookup,
is in `rules.py`'s module docstring.

**The annotated open line leads with the number; the contested line leads with the pairing.** The
GM asked for `{roll} {skill}: {name} {annotation}` for the open rolls specifically, and `41 vs 28`
says nothing until you know who the two sides were. **Do not harmonize these**; both shapes are
pinned by tests that say so.

**The open line separates its note with ` - `; the contested line does not** (GM 2026-09-09,
reversing 2026-09-02 for the open line only: *"I had initially thought that I did not want a
hyphen, but now I think I do"*). A bare open roll with no note takes no dash. On the contested
line the GM's fix for the margin running into the note was to give the clause a VERB - `Jimen wins
by >=10 arguing ...` - so the `wins` is doing the work a dash would. Do not add one beside it.

**The NPC's skill is never asked for, and a tie is not always a tie.** Six skills form three fixed
pairs - interrogation/sincerity, manipulation/tact, investigation/sneaking - and the first of each
**takes the tie**, recorded as a win in the smallest band (`wins by <5`) rather than as a draw.
Every other skill contests itself, where a tie is real. Because the pairing is total, the opposing
skill is DERIVED from the player's at render time (`opposing_skill`) rather than stored on the roll
or prompted for; `annotate()` prints it beside the free-raise line so the GM can see what was
assumed. `CONTESTED_PAIRS` in `rules.py` is the one place to add a fourth pair - both lookups are
derived from it - and carries the rules citations plus the one place the rules text reads the other
way. When the two skills differ, BOTH are named on the line, so a tie-break does not read as a
contradiction.

## Rolls are HELD until the GM says what they were for

Feature 202. A bare `Jimen precepts: 25` read back months later tells the GM nothing, so a roll of
any skill except Etiquette is collected but NOT written until `annotate()` gives it a note.
Etiquette is exempt because those rolls are presumed to be introductions - one entry in
`rules.EXEMPT_FROM_ANNOTATION`, the same shape as a cap.

**Two opposite rules for closing, and they must not be harmonized.** A manual `end_conversation()`
RAISES `NotAnnotated` and leaves the conversation open; the interpreter-exit path calls the same
function with `force=True` and SAVES the bare rolls, because losing them is worse. The GM asked for
both in those terms. `render_lines(..., include_unannotated=True)` is what lets the forced path
write what the normal path holds back - measured: without it, `force` skipped the raise and then
wrote nothing at all, which is the exact opposite of what it is for.

The GM's own opposing rolls come from `xky` - see `l7r/repl/gmrolls.py` and `DiceTotal` in
`l7r/repl/dice.py`. `xky(7, 4) + 8` captures the bonus, and `_ + 15` afterwards updates the SAME
roll rather than making a second one. Rolls are buffered whether or not a conversation is open,
because the GM's usual order is to roll the NPC's side FIRST and open the conversation after.

**A contested annotation defaults to the free raises the rules grant** - one per point of skill
difference, +5 each (`rules/02-skills.md:64` and :66). The player's skill comes from the rank the
character-sheet app recorded when it has one; the NPC's is inferred from their pool as ASKED for
(above ten dice `actual_xky` turns the excess into a flat bonus, so the capped pool infers wrong).
Both bonuses are offered per side and both can be overridden - the GM warned the inference is *"not
completely reliable"*.

**An OPEN roll's bonus is a fourth menu entry, `ob`, not a question on every open roll** (GM
2026-09-09: *"this is not as common. So instead of always asking every time we add an open roll
... an open with bonus option"*). `o` never asks; `ob` (or `b`) asks `Bonus to <name>? [0]` and
the line shows the total after it, rounded like any open roll. `annotate._kind` is where `ob`
survives the one-letter collapse that turns `open` into `o`.

**Two things `annotate()` deliberately does NOT do** (GM 2026-09-09): it returns nothing - the old
count was echoed at the prompt as an unlabeled number after the summary line - and its answers stay
OUT of the readline history (`ask_quietly` takes each line back off as `input()` returns, only when
the length grew, since readline never records a blank line). Every `annotate()` prompt goes through
`ask_quietly`; a new prompt that calls `input()` directly puts the answers back in the history.

**INTERROGATION IS WRITTEN ALONE, EXACT, RANKED AND GROUPED - never against the GM's Sincerity
roll** (feature 206, GM 2026-09-10). The leak: *"if someone knows how high the NPC rolled on
sincerity, then they would know whether the 'doesn't seem to be holding anything back' result
represents truthfulness or if that is simply because the interrogator didn't roll high enough."*
So `annotate()` never offers `o/c/d/ob` for an interrogation roll. (206's own prompt - join which
line, or start a new one, then grilling and the topic - was REPLACED by feature 207: lines are
declared with `new_line_of_questioning`, and the menu now sees an interrogation roll only when it
is on no line or has no rank. See the feature 207 section below.) The written line is `interrogation[ (grilling)]: 37@2 Jimen /
24@1 Moriko - <topic>: <outcome>`: the raw total (no rounding, no bonus on either side - the NPC's raises for
an unprovable lie and the interrogator's for a scared subject both reveal NPC state, and only
grilling is public), the rank as `@N` so the number reads without the other side, rollers highest
first as Etiquette does, one line per line of questioning because the rules roll the skill *"once
for each line of questioning"*. **Lines are DERIVED from the rolls** (`Roll.line` id + `grilling`
flag; `rules.lines_of_questioning`), not stored beside them, so the menu's staging and Ctrl-C need
no second code path; the cost is the topic and flag duplicated on every roll of a line. A held
interrogation roll is written bare (`interrogation: 37@2 Jimen`) by the exit path only. Full
reasoning and the declined alternatives in `specs/206-interrogation-lines/research.md`.

**Bonuses are kept PER SIDE and never netted.** A bonus to the NPC raises the NPC's total; it never
lowers the player's. The GM's reason: a player who rolled 30 against an opponent's free raises still
rolled 30, and flattening that to "-10 to the player" destroys information that matters even when
the margin is identical.

## Feature 207: modes, hidden opposition, and the NPC's remembered numbers

```
>>> begin_conversation("Fumitake")
  on record for Fumitake: Air 3, sincerity 5
>>> acting(2)                                  # records; never rolls
>>> new_line_of_questioning("Chizuru's death", sincerity())
  Fumitake sincerity: 8k3
  +10 acting 2
Line of questioning: Chizuru's death - sincerity roll kept in the GM-only notes
  + Tsuruchi Jimen: interrogation 37 @2
  = Jimen 37 vs sincerity 48 (+10 not grilling, +15 free raises): not detected
>>> detected("Jimen", "he is lying about the hour")     # any time; he gets his own line
>>> xky(5, 3) - tact                            # records tact 2; a later 6k3 stops and asks
```

Public bio - **no hidden number, ever**:

```
interrogation: 24@1 Moriko - Chizuru's death: nothing hidden detected
interrogation: 37@2 Jimen - Chizuru's death: he is lying about the hour
acting: 32@1 Jimen - posing as a rice factor: no signs of the persona being seen through
25 sneaking: Jimen - blending into the crowd          <- always contested, nobody opposed it
```

GM-only notes:

```
NPC numbers:
- Air 3
- sincerity 5
- acting 2

Hidden rolls:
- 2026-09-19 sincerity 48 (+10 not grilling) - Chizuru's death: Jimen 37@2 not detected
```

**This REVERSES one rule of feature 206, on the GM's word.** 206 wrote the Sincerity roll NOWHERE;
it now goes to the GM-only notes. The PUBLIC half of 206 is untouched: alone, exact, ranked,
grouped - and now grouped BY OUTCOME, so a PC who detected something stands apart. The default
outcome is written whether the NPC was truthful, lied well, or was never rolled for; that sameness
is the point and `test_the_line_reads_the_same_with_and_without_a_sincerity_roll` pins it.

**The who-won is ADVISORY and private.** It is printed in the terminal (never screen-shared, GM
2026-09-19) and written to the GM-only block, and it NEVER sets the public outcome: the raises the
GM hands out as a line of questioning goes on are not known to the tool. `detected()` is how the
public outcome changes.

**Only the tool applies the casual +10**, from the line's grilling flag; `grilling()` takes it back
retroactively. Whatever the GM adds to a roll by hand is never adjusted.

**`sincerity(8, 3)` and `xky(8, 3) - sincerity` differ in ONE thing**: only the called form adds the
automatic raises (acting -> sincerity, intimidation; history -> culture, law, strategy; never
sneaking or heraldry, which are conditional). The `+ 10` the GM types onto an `xky` roll IS the
acting bonus, so the tag adding it again would count it twice.

**Nothing is recorded or checked without an open conversation** - a tag made outside one only marks
the roll. The fidelity review struck a draft that recorded such rolls when the next conversation
began: the numbers could land on the wrong NPC's permanent record.

**One NPC at a time**, by the GM's ruling for now. A later feature will track several, which is why
a tag holds no NPC and the numbers live on the `Conversation`.

Reasoning, declined alternatives and one recorded dead end (the pty test that hung) are in
`specs/207-roll-modes/research.md`.

## Feature 208: oppose rolls take effect by themselves

```
  + Tsuruchi Jimen: oppose social 32 @3
  = Fumitake takes -6 oppose social (Jimen 32) on every Air roll from here on
>>> tact()
  Fumitake tact: 5k3
  -6 oppose social (Jimen 32): 12
```

Public bio - bare, in sequence, nothing asked: `30 oppose social: Jimen`. GM-only:
`sincerity 48 (+10 not grilling, -6 oppose social) - topic: ...`.

**The tool OWNS this penalty; the GM never subtracts it by hand.** It lands on the called form
(`tact()`), the tagged form (`xky(5, 3) - tact`), and - at the moment `annotate()` pairs it - an
untagged roll or a typed total, because pairing is when its ring becomes known. This is NOT
feature 207's called-form-only rule for the acting/history raises: that rule exists because the GM
types the acting `+ 10` by hand, and nobody types this. The manipulation default of 15 is not a
roll and pays nothing.

**It is kept APART from the GM's bonus** (`GmRoll.penalty`, SET and never added), so re-deriving it
cannot subtract it twice, and a line of questioning reads the Sincerity roll `unpenalized` and
applies the LINE's penalty - which is also what makes the one retroactive case work: an Oppose
Social made part way through a line comes off that line's Sincerity roll (*"basically the same as
... not grilling to grilling"*), while a line that had already ended is left alone.

**Air and Water are the GM's statement (`oppose.TARGET_RINGS`), not read from the rules.** Each
knack's `**Ring:**` header is the ring it is ROLLED with, which is the OTHER ring. The rules text is
only checked at `begin_conversation`, and a disagreement is printed while the penalty still applies.

**Time is message time**, as for lines of questioning: the watcher lags by up to a poll, so
`conversation.collect` calls `oppose.settle` to price NPC rolls already made under a late-seen
oppose roll, and says which moved.

**Only these two two-word knacks are in the vocabulary** (`skills.MULTIWORD_KNACKS`), read by a
phrase pass that runs BEFORE the one-word cluster and blanks what it claims. `double attack` and
the rest stay out until someone rules on their `annotate()` mode.

**`cancel_*` takes back an effect that began by itself** (GM 2026-09-19, shown that a mistyped
oppose roll had no way back: *"if we had some kind of cancel_* functions for stuff like that it would
be good"*). `cancel_oppose("Jimen", "social")` (the name and the knack are each needed only when ambiguous - it NEVER guesses, because a PC may hold a good roll of the other knack and a canceled roll cannot be put back), `cancel_grilling()`,
`cancel_detected("Jimen")`. Each returns the conversation to EXACTLY the state before the mistake,
and the tests assert that by comparing the rendered lines. The derivation already ignored a
`discarded` oppose roll, so canceling one is a flag plus `settle`. NOT built: canceling a declared
line of questioning - what happens to the rolls already on it is a real question, put to the GM.

Three things that review struck, recorded in `specs/208-oppose-penalties/spec.md`: a tool-written
note on the public line, reading the ring mapping from the rules text, and a discard command the
session had built before the GM asked for one (it came back as `cancel_oppose` once they had).

## Feature 209: an intimidation line says how the NPC APPEARED

```
30 intimidation: Jimen - threatening to have him arrested: Fumitake appeared unsettled
```

After what the roll was for, `annotate()` asks `How did Fumitake appear?` - stoic, unsettled,
rattled or shaken (`modes.APPEARANCES`, the GM's words; pick by number, the word, or an unambiguous
start - a bare `s` asks again). **APPEARED, never "was" or "felt"** (GM 2026-09-19: *"rather than
asserting that they actually did feel that way"*): an NPC can put on a face, and the intimidation
thresholds are hidden from the players by rule. **The choice is REQUIRED and has no default**, which
is unlike the rest of this menu, where a blank line finishes: the thresholds are set per scene, so
the number cannot say which state it was, and the note has already been typed by then. It is asked
LAST, in `_decide`, so it follows every way the roll can be recorded (open, `ob`, the rare contest)
and never follows a discard. Stored in `Roll.outcome`, the field interrogation and acting use for
what the players got; `rules.appeared_text` renders it and only for intimidation. The prompt
always names the NPC, and that is right: the GM ruled (2026-09-19) that an NPC only ever rolls
intimidation as the opposing side of a PC's CONTESTED roll, so the roll being annotated is always
the PC's - do not add a "who appeared?" question.

## Feature 210: choices are made with the arrow keys

```
  Open, contested, discard, or open with bonus?
  > open  [o]
    contested  [c]
    discard  [d]
    open with a bonus  [ob]
    finish - keep what is staged
```

Up / Down move (wrapping), Enter chooses, and the list then collapses to one line - the question
and the chosen row - so the scrollback reads as a record. **Typing MOVES the highlight; Enter
chooses**: `o` Enter, `ob` Enter, `12` Enter all still work keystroke for keystroke. A letter
choosing instantly was declined - it breaks `ob` (its `o` would already have chosen "open") and
every two-digit row.

**A prompt is a menu only when the answers come from the REAL terminal**: stdin and stdout are ttys
AND the `ask` in use was registered with `menu.terminal_asker` (the package's own quiet `input`,
and the `_ask` wrappers in `lines.py` / `npcskills.py`). A test or script that supplies its own
`ask` is ALWAYS asked the typed question - which is why every scripted test that predates the
feature passes unmodified, and why a test never hangs waiting for an arrow key even when pytest is
run from a terminal. **A new choice prompt calls `menu.ask_choice(ask, question, title, options)`**
with the typed `question` as its fallback; a new `ask` wrapper that reads the terminal must be
registered or its prompts stay typed.

**The row that starts highlighted is whatever a bare Enter means at that prompt today**: "part of
this line" at the join-or-discard question (the GM's Enter-per-roll habit; opening on "discard"
would be data loss), "leave it for now" at the no-lines interrogation question, "mistake" at the
disagreement prompts (also what Ctrl-C means there). Where a blank line finished, there is an
explicit `FINISH` row.

**NOT converted, on purpose**: free text (what a roll was for, a bonus, a typed total, a rank) and
the MIXED prompt - "what was it for?", which takes a note but also `c` / `ob` / `d`. A list cannot
hold a free-text row; the GM approved leaving it typed, and the two-press undo still lives there.

**At a terminal the typed enumeration is NOT printed** (`annotate._listed`, and the `[m] ... [r]`
line in `npcskills`): the menu is the list, and printing both showed everything twice.

`tests/test_rolls_menu.py` drives a real pseudo-terminal for the key loop, and a whole
`annotate()` run with scripted arrow keys for the call sites.

## Two things that will bite you

**A pasted dice card cannot be recognized as one.** Clipboard pastes arrive as `image.png` and so
do memes, alongside `Z.png`, `9k.png`, `Untitled.jpg`. There is no filename or content test. A
message with an image is a roll if and only if the character-sheet app has a recorded roll for that
author around that timestamp - **the join IS the detector**, which is why the endpoint is worth
building and why an unmatched image is ignored silently rather than reported.

**A slash-command roll is posted BY THE BOT, not by the player.** A real `/etiquette` post comes
from author `1490400739934212116` with content `**Roll Tester**: **23** Etiquette@1`, so joining on
`actor_discord_id` finds nothing - the player is named in the message body instead, and
`bot_roll_character` is what reads it. The markdown matters too: `**23**` glued to the number
stopped the parser matching at all until emphasis was stripped.

**The typed path is primary, not a fallback.** 204 image posts against ~99 typed, split by PLAYER
rather than by group: two Monday players and one Tuesday player type almost everything. It is the
path that still PARSES with no endpoint at all - though see below, it cannot attribute without
one.

## Attribution needs the endpoint, and this is the honest limit today

**The character-sheet app is the source of truth for who plays whom** (GM 2026-08-28), and it is
the ONLY source: the sheet's public index page carries character names and groups but no owner
Discord ids (checked 2026-08-28), and Obsidian Portal has no Discord ids at all. So
`/api/characters` is on the critical path for BOTH input paths, not just the image one - the parser
reads a typed roll perfectly well without it, but cannot say whose roll it is.

`[discord_players]` in `development-secrets.ini` (`<discord_id> = <Character Name>`) exists as a
stopgap for testing before that endpoint ships. It is NOT meant to be maintained by hand:
`sheet.characters()` takes over the moment the endpoint exists, and the fallback should then be
deleted rather than left to drift.

## Testing

```
( cd webapp && pytest -n auto tests/test_rolls_rules.py tests/test_rolls_parse.py \
    tests/test_rolls_skills.py tests/test_rolls_models.py tests/test_rolls_bio.py \
    tests/test_rolls_discord.py tests/test_rolls_sheet.py tests/test_rolls_conversation.py \
    tests/test_rolls_corpus.py tests/test_rolls_annotate.py tests/test_rolls_followup.py \
    tests/test_rolls_interrogation.py tests/test_rolls_modes.py tests/test_rolls_npcnumbers.py \
    tests/test_rolls_npcskills.py tests/test_rolls_lines.py tests/test_rolls_hidden.py \
    tests/test_rolls_keys.py tests/test_rolls_annotate_modes.py tests/test_rolls_oppose.py \
    tests/test_rolls_menu.py )
```

`test_rolls_keys.py` drives a REAL pseudo-terminal. The undo keys must be written to it AFTER it is
in cbreak mode - in canonical mode a queued Backspace is eaten as an erase and the read blocks
forever (it hung the suite once).

`test_rolls_corpus.py` is the one that matters most: it sweeps 615 real messages and pins the
number of rolls found (`EXPECTED_ROLLS`). **That constant is a regression fixture, not a target** -
when it moves, read the diff before editing it. It has already earned its keep once, catching a
roll that was being counted twice.

Hand-check against the live channels (read-only, safe):

```
./scripts/repl.py 'begin_conversation("Otsuki", "tuesday"); conversation_status()'
```

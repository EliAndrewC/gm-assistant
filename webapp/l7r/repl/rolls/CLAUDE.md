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
| `rules.py` | The GM's RECORDING rules (not game rules): round down to 5, cap Etiquette at 40 before rounding, contested keeps both totals raw and rounds only the margin. The GM's reasoning for the cap is in the module docstring - **do not delete it**, the rule is meaningless without it. `render_open` reproduces the GM's shorthand exactly. |
| `skills.py` | The skill vocabulary, READ from `/host-l7r-repo/rules/02-skills.md` rather than copied, so a rename in the rules reaches us. Unambiguous prefixes resolve (`eti` -> `etiquette`); an ambiguous one is reported, never guessed. |
| `parse.py` | Hand-typed rolls. The forms are wilder than they look - see the module docstring for the fifteen real shapes. A number is a roll ONLY when a real skill name sits beside it; that one rule kills nearly every false positive, and the three that survived it are each pinned by a test. |
| `bio.py` | Splices lines directly under the `[[File:...]]` portrait embed. `rewrite` swaps this conversation's previous block for its current one - the watcher writes repeatedly, so appending would stack a line per poll. Removing a line takes the blank line spliced with it, or the body grows a newline every write. |
| `discord.py` | Read-only REST. The bot holds permissions 66560 (View Channel + Read Message History) and there is no code here that could post. Snowflakes are synthesized from a timestamp; `before`/`after` are mutually exclusive in the API, so the far end is bounded in Python. |
| `sheet.py` | The character-sheet app's roll-history client. **THOSE ENDPOINTS DO NOT EXIST YET** (spec: `character-sheet/externally-queryable-roll-results.md`). Every failure degrades to empty with a reason; nothing raises. |
| `console.py` | `print_above` - writes from the watcher thread WITHOUT stomping the prompt: `\r\x1b[K` erases the prompt line, the message goes there, then the prompt and whatever the GM had typed are redrawn beneath it. TTY only; a pipe gets a plain print. |
| `annotate.py` | The `annotate()` menu - which roll, open or contested, what it was for. Ctrl-C discards EVERYTHING staged in that run, which is the literal reading of the GM's "not save anything" and the behavior most likely to sting. Blank finishes and commits. |
| `conversation.py` | The only stateful module: open, collect, close, write, plus the background watcher. `_tick` is one poll - collect, announce, maybe write - split out so the debounce is testable without threads. Boundaries are injected as callables, the way `discern_honor` takes `characters=` / `get_body=` / `update=`. |

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

The GM's own opposing rolls come from `xky` while a conversation is open - see `l7r/repl/gmrolls.py`
and `DiceTotal` in `l7r/repl/dice.py`. `xky(7, 4) + 8` captures the bonus, and `_ + 15` afterwards
updates the SAME roll rather than making a second one.

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
    tests/test_rolls_corpus.py )
```

`test_rolls_corpus.py` is the one that matters most: it sweeps 615 real messages and pins the
number of rolls found (`EXPECTED_ROLLS`). **That constant is a regression fixture, not a target** -
when it moves, read the diff before editing it. It has already earned its keep once, catching a
roll that was being counted twice.

Hand-check against the live channels (read-only, safe):

```
./scripts/repl.py 'begin_conversation("Otsuki", "tuesday"); conversation_status()'
```

# `l7r.repl.rolls` - Discord rolls into an NPC's Obsidian Portal record

The GM plays online; players post their rolls in Discord; the GM used to transcribe them into the
NPC's record by hand. This package removes the transcription. At the prompt:

```python
>>> begin_conversation("Otsuki", "tuesday")
Talking to Otsuki. Rolls from now until end_conversation().
>>> end_conversation()
Otsuki: Sadakichi / Moriko / Jimen / Tetsuro / Toshihiro etiquette: 35 / 25 / 25 / 20 / 15
```

Which NPC the players are talking to is the ONE thing that cannot be inferred, so it is the one
thing the GM says. `end_conversation()` writes immediately - no confirmation step, because a
"does this look right?" prompt would put back the manual step the feature exists to remove.

| file | holds |
|---|---|
| `models.py` | `Roll`, `Contest`, `RecordingRule`, `Conversation`. Pure data. `Roll.total` is deliberately NOT decomposed into dice plus bonuses - the character-sheet app owns the dice math and we never reimplement it. |
| `rules.py` | The GM's RECORDING rules (not game rules): round down to 5, cap Etiquette at 40 before rounding, contested keeps both totals raw and rounds only the margin. The GM's reasoning for the cap is in the module docstring - **do not delete it**, the rule is meaningless without it. `render_open` reproduces the GM's shorthand exactly. |
| `skills.py` | The skill vocabulary, READ from `/host-l7r-repo/rules/02-skills.md` rather than copied, so a rename in the rules reaches us. Unambiguous prefixes resolve (`eti` -> `etiquette`); an ambiguous one is reported, never guessed. |
| `parse.py` | Hand-typed rolls. The forms are wilder than they look - see the module docstring for the fifteen real shapes. A number is a roll ONLY when a real skill name sits beside it; that one rule kills nearly every false positive, and the three that survived it are each pinned by a test. |
| `bio.py` | Splices the line directly under the `[[File:...]]` portrait embed. Idempotent, and preserves existing bio text byte for byte. |
| `discord.py` | Read-only REST. The bot holds permissions 66560 (View Channel + Read Message History) and there is no code here that could post. Snowflakes are synthesized from a timestamp; `before`/`after` are mutually exclusive in the API, so the far end is bounded in Python. |
| `sheet.py` | The character-sheet app's roll-history client. **THOSE ENDPOINTS DO NOT EXIST YET** (spec: `character-sheet/externally-queryable-roll-results.md`). Every failure degrades to empty with a reason; nothing raises. |
| `conversation.py` | The only stateful module: open, collect, close, write. Boundaries are injected as callables, the way `discern_honor` takes `characters=` / `get_body=` / `update=`. |

## Two things that will bite you

**A pasted dice card cannot be recognized as one.** Clipboard pastes arrive as `image.png` and so
do memes, alongside `Z.png`, `9k.png`, `Untitled.jpg`. There is no filename or content test. A
message with an image is a roll if and only if the character-sheet app has a recorded roll for that
author around that timestamp - **the join IS the detector**, which is why the endpoint is worth
building and why an unmatched image is ignored silently rather than reported.

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

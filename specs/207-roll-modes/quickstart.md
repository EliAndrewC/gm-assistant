# Quickstart: feature 207

## Automated

```
( cd webapp && pytest -n auto tests/test_rolls_modes.py tests/test_rolls_npcnumbers.py \
    tests/test_rolls_npcskills.py tests/test_rolls_lines.py tests/test_rolls_hidden.py \
    tests/test_rolls_keys.py tests/test_rolls_annotate_modes.py tests/test_rolls_interrogation.py \
    tests/test_rolls_skills.py tests/test_rolls_corpus.py )
```

## By hand, at the real prompt (`./scripts/repl.py`)

Use the scratch channel so nothing lands on a live game: `begin_conversation("<an NPC>", "test")`.
Every write goes to that NPC's record, so pick one you do not mind carrying a test block, or
`abandon_conversation()` at the end (nothing is written on abandon except what the debounce
already sent).

1. `xky(5, 3) - tact` -> "recorded for <NPC>: Air 3, tact 2".
2. `xky(6, 3) - tact` -> stops: tact 2 recorded, this roll says 3. Press Ctrl-C: "marked as a
   mistake", the repl stays up.
3. `xky(6, 4) - tact` -> the `[v] This roll spent a void point` answer is offered.
4. `tact()` rolls 5k3; `tact(vp)` rolls 6k4 with no prompt.
5. `acting(2)` records and rolls nothing; `sincerity()` then prints `+10 acting 2`;
   `xky(8, 3) - sincerity` does not.
6. `new_line_of_questioning("a topic", sincerity())`, post `37 interrogation @2` in the test
   channel, wait for the `+` line and the private `=` comparison.
7. `grilling()` twice: the second says it was already recorded.
8. `detected("<PC>", "what they caught")`, then `conversation_status()`: that PC is on their own line.
9. Post `44 history`, run `annotate()`: the prompt reads `open - what was it for?`. Press Backspace
   twice on the empty line: the four-way question appears. Run it again and type a letter first:
   the letter is on the line and editable.
10. Post `41 manipulation @3` after a `tact()` roll: `annotate()` shows the pairing and asks only
    for the note.
11. Open the NPC on Obsidian Portal: the bio carries no sincerity or investigation number; the
    GM-only notes carry `NPC numbers:` and `Hidden rolls:`.

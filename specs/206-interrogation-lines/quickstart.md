# Quickstart: Interrogation rolls grouped by line of questioning

## What the GM sees

Two players roll Interrogation on the same topic, then one of them opens a second topic. At the
REPL:

```
>>> annotate()
Rolls waiting to be annotated for Otsuki:
  1. Tsuruchi Jimen interrogation 37 @2  (21:14:02)
  2. Moriko interrogation 24 @1  (21:14:40)
  3. Tsuruchi Jimen interrogation 25 @2  (21:20:11)
Which roll? (number, or blank to finish) > 1
  Tsuruchi Jimen interrogation 37 @2  (21:14:02)
  New line of questioning, or discard? [n/d, blank to finish] > n
  Grilling? [y/N] > y
  What was the line of questioning? > what Fumitake ordered his escorts to do
  staged: interrogation (grilling): 37@2 Jimen - what Fumitake ordered his escorts to do
Rolls waiting to be annotated for Otsuki:
  1. Moriko interrogation 24 @1  (21:14:40)
  2. Tsuruchi Jimen interrogation 25 @2  (21:20:11)
Which roll? (number, or blank to finish) > 1
  Moriko interrogation 24 @1  (21:14:40)
  Lines of questioning so far:
    1. (grilling) what Fumitake ordered his escorts to do
  Join which line? (number, n for new, d to discard, blank to finish) > 1
  staged: interrogation (grilling): 37@2 Jimen / 24@1 Moriko - what Fumitake ordered his escorts to do
  Tsuruchi Jimen interrogation 25 @2  (21:20:11)
  Lines of questioning so far:
    1. (grilling) what Fumitake ordered his escorts to do
  Join which line? (number, n for new, d to discard, blank to finish) > n
  Grilling? [y/N] >
  What was the line of questioning? > what Fumitake thinks of Tsuruchi
  staged: interrogation: 25@2 Jimen - what Fumitake thinks of Tsuruchi
Annotated 3 roll(s).
```

A hand-typed roll (no rank recorded) gets one extra question before the line questions:
`Jimen's interrogation rank? [none] > 2`. Blank writes the roll with no `@`.

What reaches Obsidian Portal:

```
interrogation (grilling): 37@2 Jimen / 24@1 Moriko - what Fumitake ordered his escorts to do
interrogation: 25@2 Jimen - what Fumitake thinks of Tsuruchi
```

The GM's own Sincerity roll (`xky(6, 3) + 10` before or during the conversation) is never offered
and never written.

## How to verify

Reference module first, then the sweep:

```
( cd webapp && pytest -q -n auto tests/test_rolls_interrogation.py )
( cd webapp && make done )
```

Hand-check at the REPL without Discord: open a conversation with the scratch channel, type the
three rolls into it as the players would (`Jimen interrogation 37`, etc.), run `annotate()` as
above, and read the bio block back with `conversation_status()`.

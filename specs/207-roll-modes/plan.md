# Implementation Plan: Roll modes - what each skill may be, and what stays hidden

**Feature**: `specs/207-roll-modes` | **Date**: 2026-09-19 | **Spec**: [spec.md](spec.md)

## Summary

Three things that share one idea - the tool should already know what kind of roll it is looking at:

1. `annotate()` reads a per-skill MODE instead of asking `o/c/d/ob` of everything, with a real
   keystroke undo for the defaults it selects.
2. Interrogation and acting have a HIDDEN opposing roll: lines of questioning are declared by
   function, the public line gains an outcome, and the hidden numbers go to the GM-only notes.
3. The GM's own rolls are TAGGED with a skill (`xky(5, 3) - tact`, or `tact()`), which remembers
   the NPC's rings and ranks between sessions, checks later rolls against them, and lets
   `annotate()` pair opposing rolls by itself.

## Technical Context

- Python 3.14, stdlib only (`termios`/`tty`/`select` for the key read). No new dependency:
  prompt_toolkit was priced for the keystroke and declined (spec, Story 3).
- All code under `webapp/l7r/repl/` (100% coverage, mypy --strict). Boundaries - Obsidian Portal,
  Discord, the terminal - stay injected callables, the package's existing convention.
- The rules repository is READ (`02-skills.md`, `04-schools.md`, `05-school_knacks.md`,
  `11-non_pc_schools.md`) for: the vocabulary, each skill's ring and advanced flag, and which
  schools roll an extra die on which skill. None of those lists is written into code.

## Constitution Check

- **V. Protecting the GM's Writing**: PASS - no SOURCE block touched. The two rules-file edits were
  made on the GM's explicit instruction and are theirs to commit.
- **VI. Verify Before Reporting Done**: PASS - each phase runs its own test file; one full gate at
  the end; a scripted end-to-end run of the repl functions against fakes before the push.
- **IX. Setting Integration**: PASS - every game fact is read from or cited to the rules files.
- **X. Python Discipline**: PASS - ruff, format, mypy --strict, 100% coverage; new modules kept
  well under 1,000 lines by splitting (`modes`, `npcnumbers`, `hidden`, `keys`, `npcskills`,
  `lines`), and `annotate.py` is watched for the same limit.
- **XIII. No Known Regressions**: PASS - baseline `make done` on unmodified HEAD in the clone before
  the first edit; the corpus count (`EXPECTED_ROLLS`) is a regression fixture and every change to
  it is read and explained (Story 2).
- **XIV. Fix Defects Where You Find Them**: APPLIES - pontificate/athletics not being captured was
  found while scoping and is fixed here; manipulation silently falling back to OPEN when the GM has
  no recent rolls likewise.
- **XVI. Fidelity**: the spec-fidelity verdict is recorded in spec.md "Review history" before any
  code; FR-007a's narrowing of "each previous interrogation roll" was put to the reviewer by name.
- **XVIII. Guards**: no new hook. The one list-shaped safety property (every vocabulary entry has
  a mode) is a test that reads the rules file, not a hand-kept copy.
- I, II, III, VII, VIII, XI, XII, XVII: not applicable (no UI, pool, generated prose, kanji,
  historical claim or README).

## Design

### Modules

| file (under `webapp/l7r/repl/`) | holds |
|---|---|
| `rolls/skills.py` (grown) | vocabulary + single-word school knacks that declare a ring; `skill_rings()` and `advanced_skills()` read from `02-skills.md` |
| `rolls/modes.py` (new) | the MODE table and `mode_of()`; the default outcomes; the manipulation default of 15 |
| `rolls/npcnumbers.py` (new) | PURE: the GM-only "NPC numbers" block (parse / render), school extra dice derived from the rules text, school detection on an OP record, `infer()` a roll into ring + rank, `compare()` into a `Disagreement` with its void point answer, the acting/history automatic raises |
| `rolls/hidden.py` (new) | PURE: the GM-only "Hidden rolls" block - entries for this conversation replaced in place, older ones untouched |
| `rolls/keys.py` (new) | the two-press undo: a pure decoder over an injected byte reader, plus the thin termios boundary |
| `rolls/npcskills.py` (new) | `SkillTag` (`roll - tact`, `tact()`, `tact(2)`, `tact(5, 3)`, `tact(vp)`), `VoidPoints` (`vp`, `vp * 2`), the disagreement prompt with Ctrl-C caught |
| `rolls/lines.py` (new) | `new_line_of_questioning`, `grilling`, `detected`, the private comparison |
| `rolls/annotate.py` (changed) | dispatch on mode; pre-pairing; the 15 and nobody entries; acting; the reduced interrogation branch |
| `rolls/rules.py` (changed) | outcome on the interrogation line, grouped BY OUTCOME; the acting line |
| `rolls/conversation.py` (changed) | loads the NPC's numbers at begin; attaches interrogation rolls to the current line; persists both GM-only blocks on the same debounce as the bio; one lock around collect |
| `gmrolls.py` / `dice.py` (changed) | `GmRoll` gains `tagged`, `mistake`, `void_points`, `checked`, `paired`; `DiceTotal.__sub__` hands a tag to the tag (duck-typed, so `dice.py` still imports nothing from `rolls/`) |

### Decisions

- **D1 - Lines stay DERIVED on the rolls** (206's R2), plus a small declared list on the
  conversation. A roll attached to a line carries the line's id, description and grilling flag as
  206's rolls do, so rendering, staging and Ctrl-C keep ONE code path; the conversation's
  `lines` list exists because a declared line may have no rolls yet and owns the hidden Sincerity
  roll. `grilling()` rewrites the flag on every roll of the line.
- **D2 - `Roll.outcome`** is per roll; a written line is a (line, outcome) group. Empty means the
  default, so SC-004 (identical whether or not Sincerity was rolled) holds by construction.
- **D3 - Attach by MESSAGE time** against the line declaration times; a roll older than the first
  declaration is never attached silently. `new_line_of_questioning` collects once, synchronously,
  before prompting, so a roll posted seconds earlier is asked about there; one that still arrives
  late is asked about in `annotate()`.
- **D4 - One lock around collect.** The watcher thread and a GM-triggered collect must not both
  advance `last_seen`; today only `end_conversation` collects outside the watcher and it stops the
  watcher first.
- **D5 - The tag is duck-typed in `DiceTotal.__sub__`** (`other.tag_roll(self)`), keeping the
  import order `gmrolls` <- `dice` <- `rolls/*` that `gmrolls.py`'s docstring explains.
- **D6 - A rank of 0** rolls ring-k-ring without rerolling tens, and an ADVANCED skill at 0 takes
  -10 (`02-skills.md`: "If you roll any skill which you have at 0 ..."). The called form applies
  it; inference reads 0 when rolled equals kept.
- **D7 - School detection is mechanical** (GM: "look for those strings mechanically"): a school
  name from the rules matching a whole tag, or a whole line of the description or GM-only notes,
  case-insensitively. When it changes an inference the tool says which school it found.
- **D8 - Knacks in the vocabulary** are the single-word knacks whose rules entry declares a ring
  other than N/A - a derivable reading of "rollable". Multi-word knacks cannot be typed as one
  word beside a number, which is the parser's rule.
- **D9 - GM-only writes ride `_tick`**: same debounce, same first-write-immediate rule, one fetch
  of the body per write. A failed GM-only write never blocks the bio write (Story 10.3).
- **D10 - A tag made with no conversation open** only marks the roll; nothing is recorded or
  checked (fidelity review round 1).

## Phases

0. Baseline gate on unmodified HEAD.
1. Vocabulary + modes + rules-derived tables (`skills`, `modes`, `npcnumbers` pure half). Corpus
   count re-read.
2. Tagged rolls and NPC numbers (`gmrolls`, `dice`, `npcskills`, conversation load + persist).
3. Rendering: outcomes, acting line, hidden block.
4. Lines of questioning: declare, attach, prompt, grilling, detected, private comparison.
5. `annotate()`: modes, keys, pickers, pre-pairing, acting.
6. Namespace, banner, CLAUDE.md indexes, scripted end-to-end run, full gate, push.

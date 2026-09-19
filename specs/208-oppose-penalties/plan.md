# Implementation Plan: Oppose Social / Oppose Knowledge penalties

**Feature**: `specs/208-oppose-penalties` | **Date**: 2026-09-19 | **Spec**: [spec.md](spec.md)

## Summary

Capture the two two-word knacks, and DERIVE the penalty in effect from the conversation's rolls
rather than storing one: the highest live oppose roll of the matching knack made at or before the
moment in question. One definition yields no-stacking, no effect on earlier rolls, and the GM's
one retroactive case (a line of questioning still in progress) as a second, line-shaped question.

## Technical Context

Python 3.14, `webapp/l7r/repl/rolls/` (pure logic at 100% coverage, mypy --strict, ruff). No new
dependency. No UI. Boundaries (Discord, Obsidian Portal) are untouched; the only new I/O is one
read of the rules file for a consistency check.

## Constitution Check

- **V (the GM's writing)**: nothing in `/host-l7r-repo` is edited; the rules are read only.
- **VI (verification)**: one artifact first - `tests/test_rolls_oppose.py` - then the whole rolls
  suite, including the 615-message corpus count, then `make done` once.
- **X (code quality)**: new module `oppose.py` is pure and fully covered; no file passes ~1,000
  lines (`annotate.py` is the largest at ~780).
- **XII / record the why**: each decision is recorded where the rule lives - `oppose.py`'s module
  docstring, `rolls/CLAUDE.md` "Feature 208", and the spec's "Decisions the request left open".
- **XIII (no regressions)**: `EXPECTED_ROLLS` in the corpus test must not move.
- **XVI (fidelity)**: three review rounds recorded in spec.md "Review history". Two things the
  session had built were struck and removed from the code as well as the spec.

## Design

| piece | where | note |
|---|---|---|
| vocabulary | `skills.MULTIWORD_KNACKS`, `load_knacks`, `_abbreviates` | only the two oppose knacks; `opp soc` resolves per word; a bare `oppose` stays AMBIGUOUS |
| parsing | `parse._PHRASE` | a pass of its own BEFORE the one-word cluster, blanking what it claims - ordering comment at the point of change |
| derivation | `oppose.py` | `in_effect` / `for_skill` / `for_line` / `settle` / `penalize`; `TARGET_RINGS` is the GM's statement, `rules_disagreement` only checks it |
| the GM's roll | `gmrolls.GmRoll.penalty` | apart from `bonus`; SET, never added; `unpenalized` for lines |
| NPC rolls | `npcskills.taxed` | called AND tagged forms |
| pairing | `annotate._taxed` | untagged roll or typed total, priced on the NUMBER so Ctrl-C leaves nothing behind |
| lines | `hidden.compare` / `entries` | reads `unpenalized`, applies `for_line` - never twice |
| arrival | `conversation.collect` (settle) and `announce_oppose` (terminal) | message time, not poll time |
| the record | `rules.WRITTEN_BARE`, `modes.AUTOMATIC` | bare open line in sequence; never pending |

## A change outside the feature's own files, and why

`DiceTotal._shift` now returns the ENTRY's total rather than `int(self) + delta`. They were always
equal before; with a penalty that can land on a recorded roll after its value was handed out
(`settle`), the old form would echo a number nothing holds.

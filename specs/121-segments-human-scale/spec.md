# 121 - the gate's segment files come down to human scale

**Status**: implementing
**Motivation**: GM, 2026-08-17, after asking what the next file-splitting candidate was and being
shown the census: *"Start by doing the CLAUDE.md refactor, then move on to
segments_05_fields_and_funerary, then segments_08_town_and_fire, and so on, until all 13 of the
files you identified have been split up."*

## Why

Constitution Principle X clause 13: a source file past ~1,000 raw lines becomes a package of
subfiles with its own `CLAUDE.md` index, because the cost being managed is context-window tokens -
loading a huge file to use one part of it.

`check_village/segments_*.py` is the last large concentration in the skill, and by some distance:

| | lines | share of `l7r/diagram/` Python |
|---|---|---|
| the 13 `segments_*.py` files | 28,326 | **45%** |
| everything else in `check_village/` | 3,532 | 6% |
| the whole rest of the engine | 30,657 | 49% |

Every one of the 13 is over the bar (1,406 to 2,661 lines; mean 2,179). The load pattern is the
worst case the clause exists for: the MEDIAN segment is **5 lines**, so diagnosing one gate failure
means opening ~2,200 lines to read five of them. The `settlement/` campaign (features 112-120) has
already brought every module in that package under 1,000; nothing else in the skill is close.

The same census found the clause-12 residue the engine no longer has: **15 segment functions are
over 150 lines**, topping out at `_seg_0555_007__execution_ground_outside_the_settlement` at 293.
`future-work.md` records "no standing clause-12 candidate", which was scoped to the ENGINE and is
true there; the gate was never measured.

## Why this is cheap NOW and would not have been before

Feature 109 made the registry DERIVE itself, and that removed the only thing that made a segment's
file placement load-bearing:

- `registry.py::_segment_functions` discovers segments by globbing `segments_*.py` in the package
  directory. A new file matching the glob is picked up with no roster to edit.
- `registry_analysis.py::_derive_fields` AST-scans `pkg_dir.glob("*.py")` - same story.
- **Execution order comes from the numeric key in the FUNCTION NAME** (`_ordered_names`), plus the
  `_PLACEMENTS` table. Not from the file, and not from file order.

So a split that (a) moves whole segment functions, (b) changes no name, and (c) preserves definition
order within each new file cannot change the registry, the order, or any verdict. That is a much
stronger safety argument than features 114-120 had, and it is why 13 files can go in one feature.

## Scope

**In:**

1. Each of the 13 `segments_*.py` files becomes 2-4 contiguous sub-files, cut at segment
   boundaries, each under ~900 lines.
2. `__init__.py`'s star-import block, `check_village/CLAUDE.md`'s index, and
   `tests/check_village/CLAUDE.md`'s mapping rule updated.
3. The two test modules over the bar (`test_segments_05_*` 1,044, `test_segments_08_*` 1,140) split
   along the same theme cuts.

**Out, deliberately:**

- **Decomposing the 15 over-150-line segment functions.** It is a real finding and it is recorded
  in `future-work.md` by this feature, but it changes check BODIES where this feature changes only
  which file text sits in - and mixing them would destroy the byte-identity oracle that makes the
  move provable. Its own feature.
- **`tests/check_village/_builders.py`** (1,537 lines). Its own index entry already carries the
  justification for staying one file ("a cohesive builder library, loaded only when writing
  fixtures"), which is a recorded decision, not an oversight. Re-opening it is not this feature.
- **The 11 test modules under the bar.** The mapping rule relaxes to the segment GROUP
  (`segments_05*`) rather than the file, so they keep working unchanged.

## Success criteria

- **SC-001** No `check_village/segments_*.py` file exceeds 1,000 lines. (41 files, 600-900 each.)
- **SC-002** `GATE_SEGMENTS` is identical before and after: same names, same order, same
  `free`/`writes`/`checks`/`needs`/`meta`/`always` on every one of the 1,376 rows.
- **SC-003** Every moved line is byte-identical to its original. The only text this feature is
  allowed to author is: each sub-file's docstring, its pruned import block, and the two index docs.
- **SC-004** `make done` green - ruff, format, mypy --strict, pytest, 100% coverage - with no new
  regressions against a detached-worktree baseline (Principle XIII).
- **SC-005** `tests/fixtures/gate_check_names.json` unchanged (it pins the derived check names, so
  an untouched pin is independent evidence for SC-002).

# Phase 0 Research: settlement/_geom.py -> settlement/_geom/

Seven decisions. Each records what was chosen, why, and what was rejected - the pattern features
110-116 used, and the reason their successors did not re-derive the same ground.

## R1. The partition axis: what a session comes here to CHANGE

**Decision**: eleven submodules - `base`, `primitives`, `overlap`, `indexes`, `seatmemo`, `labels`,
`ways`, `walls`, `extents`, `curves`, `village`. Full member assignment in `data-model.md`.

**Rationale**: an 89-member census finds eight populations that share nothing but feature 025's
positional cut. The axis that predicts a READ is the subject, not the size:

- a session tightening the caption standoff opens `labels.py` (~145 lines) and needs none of the
  spatial indexes;
- a session changing the wellhead's drawn extent opens `extents.py` (~120) and needs none of the
  curve machinery;
- a session chasing an index staleness bug opens `indexes.py` (~245) - which carries the two
  measured post-mortems that make that bug legible - and needs no manifest reader at all.

Cut by size instead and each of those tasks straddles two files, which is strictly worse than the
status quo: the reader loads two headers, two docstrings and two halves of one subject.

**Alternatives considered**:

- **Three big files (math / manifest-readers / everything else).** Rejected: `indexes` + `seatmemo`
  + `curves` in one "everything else" bucket is 475 lines with three unrelated post-mortems in it,
  and it re-creates the problem at two thirds scale.
- **A file per member group of roughly equal size (~5 x 260).** Rejected on 116's stated rule: a
  partition tuned for equal files has to cut a cluster that no task cuts. Concretely it would put
  `SeatMemo` in with half the label ladder.
- **Splitting `_geom` by CALLER instead (a `settlement/geom_for_fields.py` and so on).** Rejected:
  the same predicate has many callers - `seg_dist` has 30+ - so a caller-keyed partition duplicates
  or arbitrarily assigns the most-used members, which is how two correct helpers for one question
  get started (the skill's `CLAUDE.md` records that exact failure with `edge_gap`/`_fr_gap`).

**Two placements a reader would otherwise re-litigate, decided here:**

- **`walls.py` holds the torii-vs-wall predicates** (`torii_halfbox`, `torii_seat_on_wall`,
  `torii_wall_conflicts`, the two pitch constants and the doctrine bank), even though
  `settlement/shrines_wells/torii.py` exists. At THIS level a torii has exactly one geometric rule -
  it must not stand in a wall - and both predicates are computed from `wall_runs()`. The arch glyph,
  the avenue count, the stride and the threshold all live in `shrines_wells/torii.py` and are
  untouched. Filing the clearance predicates with the arches would put them in a module that cannot
  see the walls they are about.
- **`base.py` holds two things that are not geometry**: the import-time main-tree guard and the
  land/crop palette. Neither belongs in a geometry package on subject grounds; both are what every
  other submodule (or, for the palette, `core.py`) needs FIRST, and the guard must run on any import
  of the package. Isolating them at the top of the dependency order costs nothing and makes the
  layering rule statable in one line.

## R2. The re-export surface: star imports, not a mixin and not a roster

**Decision**: `settlement/_geom/__init__.py` is `from .base import *` and so on for all eleven
submodules, plus an explicit `as`-alias block for the underscore names.

**Rationale**: features 025 and 112-116 all composed a MIXIN class, because every one of those files
was a class body. `_geom` is module-level functions, so there is no class to compose and the
equivalent is a re-export surface. Principle X clause 14 settles how those are written in this repo:
a hand-written 89-line import roster restates what the submodules already declare, so it is DERIVED,
not maintained. Feature 027 collapsed `check_village/__init__.py` from 3,148 lines to 63 exactly this
way, with zero consumer changes, and probe-verified the one property that makes it safe under
`mypy --strict`: a star-imported PUBLIC name counts as explicitly re-exported even under
`no_implicit_reexport`, so no `__all__` is needed (`specs/027-init-star-imports/research.md` R1).

**The hazard the stars introduce, and where it goes**: a name bound in two submodules is silently
shadowed by whichever star import runs last - no error from Python, ruff or mypy. Clause 14's own
prescription is that the roster's safety property moves into a guard test proven to fire, which is
what `contracts/surface.md` specifies and `tests/check_village/test_surface.py` already does for the
027 package.

**Underscore names must be listed explicitly** - `import *` does not carry them. **All seven** are
listed, not just the four with external consumers (`_assert_not_main_tree`, read by
`settlement/__init__.py` and through it by `check_village/common_01_geometry.py`; `_union_area` by
`homestead_parts.py`; `_signed_area` by `rolling.py`; `_aabb_gap` by `structures/servants.py`).
`_rect_ring`, `_box_hits_run` and `_VILLAGE_POP_DIST` have no consumer outside the package today and
are re-exported anyway, so the census is a single list rather than a list with a footnote.

**That "anyway" was not theoretical, and the guard is what proved it.** The first draft of the block
listed six, on the reasoning above minus `_VILLAGE_POP_DIST` - and the surface census failed on its
very first run, naming exactly that name. The package imported cleanly, `mypy --strict` passed, ruff
passed, and all 713 tests in `tests/settlement/` + `tests/tools/` passed; a name that resolved before
the split had silently stopped resolving. It is the clearest possible demonstration of the property
clause 14 asks for in exchange for deriving a roster: the safety moves into a guard, and the guard
has to actually bite. Recorded here rather than quietly fixed, because the near-miss is the evidence.

**Alternatives considered**:

- **A 89-line explicit roster** (what `settlement/__init__.py` does for its own surface). Rejected by
  clause 14 - it is the exemplar of the shape the clause exists to stop.
- **Keep `_geom.py` as a thin shim that re-exports from a new package.** Rejected: a module and a
  package of the same name in one directory is a shadowing hazard, and FR-006 deletes the file for
  that reason. The lineage does the same (`shrines_wells.py` was deleted, not shimmed).
- **Convert `settlement/__init__.py`'s own 58-line `_geom` roster to stars in the same pass.**
  Rejected as scope: that is feature 027's job applied one level up, it touches a file this feature
  otherwise leaves alone, and it would put a second question inside this feature's byte-identity
  oracle.

## R3. The transformer's slicing rule

**Decision**: reuse the lineage's rule - each member's block is
`lines[previous node's end .. this node's end]`, not `lines[node.lineno .. end]`.

**Rationale**: that span carries decorator lines, blank lines and any comment written ABOVE the
member. In this project a comment above a member is usually researched grounding, and this file is
the densest example in the engine: the plank-abutment research (14 lines), the torii pitch ruling
(12), the label standoff ladder's calibration (35), the caption-size ruling (18), the yard-glyph
collision post-mortem (16), the ward arc-length closure note (9). Slicing by `node.lineno` drops
every one of them silently, and a "pure move" that loses a why-comment is not pure. The rule is
inherited rather than re-invented precisely because it is the part a fresh implementation gets wrong
(116's transformer docstring says so, having been the fifth to inherit it).

**Verification, not trust**: `quickstart.md` step 7 counts comment lines before and after and demands
zero lost. No decorated member exists in this file (the census finds none), so 116's decorator hazard
is inapplicable here - recorded so the next reader does not go looking for it.

## R4. The unnamed module-level statement

**Decision**: an unnamed top-level statement folds into the PRECEDING named member's block; the
transformer refuses if there is no preceding member.

**Rationale**: features 112-116 sliced a class body of nothing but `def`s, so their transformers
could refuse on any unnamed member. A module top level is different: this one holds `import` lines
(which become the copied header) and one bare call - `_assert_not_main_tree()` on line 35, the
import-time main-tree guard. It has no name to key a partition on. Dropping it would disarm the guard
while every test still passed, because every test already runs inside a clone - the exact
"a check that never runs looks exactly like a check that passes" shape the skill's `CLAUDE.md`
documents. Folding it into `_assert_not_main_tree`'s block makes the call travel with its definition
into `base.py`, which is both correct and the only placement that needs no special case downstream.

**Why the guard still fires for a submodule import**: importing `settlement._geom.overlap` imports
the package `settlement._geom` first, whose `__init__` star-imports `base`, which runs the call.
There is no import path into the package that bypasses it. FR-005 and the test in
`contracts/surface.md` pin this rather than assuming it.

## R5. Comment banks that cross a module line

**Decision**: exactly one bank MOVES between modules; exactly four sentences are re-pointed. Both
lists are exhaustive, derived by grepping every positional word in the file.

**The bank that moves**: lines 452-467, "A TORII STANDS CLEAR OF EVERY WALL" - the doctrine block
that explains the rule `torii_seat_on_wall` and `torii_wall_conflicts` implement. It physically
precedes `_rect_ring`, which is a pure corner-ring helper heading for `overlap.py`, so the slicing
rule would carry a 16-line torii ruling into the collision-predicates module and away from the two
functions it documents. The transformer lifts it out of `_rect_ring`'s block and prepends it to
`torii_seat_on_wall`'s, in `walls.py`.

**The four sentences re-pointed** (every one comment-only, and enumerated in `tasks.md` so "edited"
cannot quietly mean "rewritten"):

| line | text | why | becomes |
|---|---|---|---|
| 233 | "the same discipline as `paddy_wet_rings` below" | `seg_in_ellipse_core` -> `primitives.py`, `paddy_wet_rings` -> `extents.py` | "...as `paddy_wet_rings` in `extents.py`" |
| 291 | "the same discipline as torii_wall_conflicts above" | the ways bank -> `ways.py`, the referent -> `walls.py` | "...as `torii_wall_conflicts` in `walls.py`" |
| 383 | "the label standoff ladder below" | `box_gap` -> `overlap.py`, the ladder -> `labels.py` | "...the label standoff ladder in `labels.py`" |
| 466 | "read the SAME wall_runs() / torii_wall_conflicts() below" | after the bank moves, `wall_runs` is ABOVE it in the same file | "...read the SAME `wall_runs()` / `torii_wall_conflicts()` in this module" |

**Deliberately NOT touched**: line 55 ("PLANK_ABUTMENT above" - same module), line 585 ("the builders
below" - same module), lines 408-409 (geometry, not position), and the four inside `Indexed`/
`SeatMemo` docstrings (same class). A grep for positional words returns fifteen hits; eleven are
correct as they stand and stay byte-identical.

## R6. Annotations are lazy here, and the partition must not read them as dependencies

**Decision**: partition by RUNTIME references only, and state the layering rule
(`base` <- `primitives` <- `overlap` <- {`indexes`, `labels`, `ways`, `walls`, `extents`, `curves`};
`seatmemo` and `village` depend on nothing) in the package index.

**Rationale**: the file has no `from __future__ import annotations`, yet `indexed_grid` annotates
`-> PointGrid` ~140 lines before `PointGrid` is defined. That is legal only under Python 3.14's
deferred annotation evaluation (PEP 649), which the project pins. The consequence for a partition is
specific and cuts both ways: an annotation-only reference is NOT an import dependency (treating it as
one invents cycles that do not exist), while a runtime reference IS (missing one produces a
`NameError` at call time, on a path some map may not take). Both names land in `indexes.py` here, so
the trap does not fire in this feature - but the next member added to the package can hit it, which
is why the layering rule is written into the index rather than left implicit. `mypy --strict` is the
backstop for the reverse error: a name used in an annotation and never imported fails the typecheck.

## R7. `tools/cache_audit.py`'s mutation target

**Decision**: `TARGET = settlement/_geom/curves.py`, and the audit gains one measured line per trial
reporting whether the mutation actually MOVED any artifact.

**Rationale**: the audit mutates a random numeric literal inside a function body of `TARGET` and
demands a cached sweep and a `--no-cache` sweep agree. A directory cannot be read as text, so leaving
the target on `settlement/_geom.py` crashes it exactly as the pre-025 target did - the comment above
`TARGET` records that incident, found by feature 026's mandatory run.

**Measured, not guessed.** Coverage over the two live scripted hamlets the audit sweeps (`inashiro`,
`sawada`), mapped onto the planned modules, counting the literals the audit would actually consider
(`1 < abs(value) < 10000`, inside a function body, single-line):

| module | candidate literals | of those, on an EXECUTED line |
|---|---|---|
| `curves` | 35 | 9 |
| `overlap` | 25 | 8 |
| `walls` | 21 | 8 |
| `ways` | 20 | 3 |
| `labels` | 19 | 12 |
| `extents` | 13 | 3 |
| `seatmemo` | 5 | 0 |
| `indexes` | 4 | 4 |
| `primitives` | 2 | 1 |
| `base`, `village` | 0 | 0 |

`labels` has the highest executed SHARE (12 of 19) and was the first candidate. It was rejected on
what its literals DO: they are the fold constants of `label_tilt`/`linear_tilt` (45.0, 90.0, 180.0),
and the overwhelming majority of pool captions are level, where a perturbed fold constant rounds back
to exactly 0.0 and moves nothing. A mutation that changes no byte makes a trial that passes without
testing anything. `indexes` fails the same test harder and for a deeper reason: its literals are
PREFILTER pads and the grid cell size, and the prefilter family's defining property is that widening
it cannot change a verdict.

`curves` has the most candidate literals in the package (35), nine of them executed, and every one
moves drawn geometry directly - the fillet cut-back and its 35% cap, the bend's step count, the
organic densify pitch, the jitter amplitudes. Fillets are on every hamlet's channels and organic
outlines are on every hamlet's fields.

**The audit change that makes this checkable rather than argued.** Today a vacuous mutation (one on
a line no map executes, or one that rounds away) prints exactly the same `[OK ]` as a mutation that
genuinely exercised the key. That is the "a check that never runs looks exactly like a check that
passes" shape, one level up, in the very tool that exists to keep the cache honest. The audit already
snapshots artifacts twice per trial; it now also snapshots the CLEAN baseline once, before the loop,
and prints `moved N artifacts` per trial. A run whose trials all report `moved 0` is a run that
proved nothing, and now says so. `tools.cache_audit` is deliberately outside the coverage `source`
list (it is a by-hand audit), so this adds no test debt.

**Alternatives considered**:

- **Make `TARGET` a list, or pick a module at random per trial.** Rejected for this feature: it
  changes what the audit IS (its trials would no longer be comparable run to run) and it is not
  needed - one well-chosen file gives the audit a mutation site with teeth, which is all the property
  requires.
- **Filter the candidate sites by coverage.** Rejected: it would make the audit depend on a coverage
  run of the pool, which is most of the cost of the audit itself, to buy what the `moved N` line
  reports for free.

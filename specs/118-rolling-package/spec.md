# Feature Specification: settlement/rolling.py -> settlement/rolling/ Package Split, and roll_village Decomposed into Stages

**Feature Branch**: none - this project stays on `main` (CLAUDE.md, GM 2026-07-27). Active feature
is declared with `export SPECIFY_FEATURE=118-rolling-package` and
`export SPECIFY_FEATURE_DIRECTORY=specs/118-rolling-package`.

**Created**: 2026-08-17

**Status**: Implemented 2026-08-17, in two commits (split, then decomposition - research R6).

Final per-file line counts: `roll.py` 300, `fit.py` 267, `farmsteads.py` 229, `place.py` 208,
`seeds.py` 159, `bundle.py` 132, `__init__.py` 39 (1,197 -> largest 300). `roll_village` 256 -> a
60-line orchestrator over seven `_roll_*` stages; the largest function anywhere in the package is
now `_bundle_geom` at 81 lines, so the engine has no function over the ~150-line bar and no standing
clause-12 candidate.

Oracle: every `pool/` artifact regenerated in a scratch copy and hashed against a pre-split
baseline - **893/893 byte-identical, 28/28 generators, frozen legacy maps included** (`--frozen-ok`,
which is load-bearing: all three `roll_village` callers are frozen). Run TWICE, once per commit,
and the second run compares against the ORIGINAL pre-split baseline rather than the intermediate.
`settlement/core.py` byte-unchanged; ZERO consumer files changed. Both guard assertions proven RED
against synthetic breakage before being trusted, each naming the exact member.

Independently verified beyond the plan's asks: all 43 members compared text-for-text against the
pre-split file (only `_farmsteads_legacy` differs, by the documented annotation), and the 30-call
main-stream sequence inside `roll_village` compared before/after (identical).

**Input**: User description: "Please refactor rolling.py - which is over a thousand lines of code -
to comport to our documented conventions for function and file size."

## Why this file, and why BOTH clauses

`settlement/rolling.py` is 1,197 raw lines and holds `roll_village` at 256 lines. It is the only
module in the engine that is over the bar on **both** halves of constitution Principle X:

- **Clause 13 (files, RAW lines):** 1,197 against a ~1,000 bar. This is the seventh file in the
  `settlement/` tree to cross it; six have already been cut (`fields/` 112, `city/` 113,
  `structures/` 114, `civic_grounds/` 115, `shrines_wells/` 116, and the tree itself by 025), and a
  concurrent session is cutting `_geom.py` as feature 117.
- **Clause 12 (functions, LOGIC UNITS):** `roll_village` is **117 statements**, which is nowhere
  near clause 12's ~500 "suspect" threshold - so the constitution's own measure does NOT call it a
  defect, and this spec does not claim otherwise. What calls it is the project's own converged
  practice: `future-work.md` records `roll_village` as "the largest function in the engine at 256
  lines - the only one left over the ~150-line bar features 112/115 converged on", and names it
  **the next clause-12 candidate** by name. Feature 115 set the precedent by decomposing
  `_stable_yard` (335 lines -> longest stage 85).

The GM's request names function size and file size together, so both halves are in scope. They are
also cheaper together than apart: the split has to touch every member of the class anyway, and
`roll_village` is the member whose destination module is otherwise a 257-line file holding exactly
one function.

**The read-cost argument, concretely.** `rolling.py` is not a residue bucket like `structures.py`
or `civic_grounds.py` - it is one long chain, from "roll a whole village from a seed" down to "does
this rect touch a ditch". But the chain has clearly separable links, and a session almost never
needs two of them:

- adding a settlement FORM (a new `*_seeds` generator) reads none of the bundle solver;
- changing what a bundle IS (garden beds, the kura, appurtenance caps) reads none of the fit
  predicates and none of the flush;
- tuning a fit predicate (the sun corridor, the water keep-out) reads no geometry construction;
- changing what `farmsteads()` DRAWS reads none of the rolling entry point.

Today each of those loads all 1,197 lines. The heaviest documentation in the module compounds it:
`roll_village`'s band-pitch post-mortem (~30 lines), the windbreak derivation note, the `_kura_side`
draw-time-decision block and the `_sun_corridor_ok` research grounding are all correct, all must be
preserved verbatim, and all are paid for by every reader of the file.

## The safety property this feature rests on, measured before it was promised

`future-work.md` says a decomposing session must **measure the RNG surface first**, because a
`roll_village` stage split that perturbed the main `random` stream would re-roll maps. An AST walk
over the function reports every `random.*` / `knob_rng` / `resolve` call site:

| call site | stream |
|---|---|
| 6 x `self.resolve(...)` knobs, `knob_rng(self.seed, "water_source_position")` | dedicated, `scope_seed`-derived |
| `random.Random((self.seed ^ 0x1A7D) & 0xFFFFFFFF)` (land-use overlay) | dedicated, seeded from `self.seed` |
| `random.Random((self.seed * 2654435761) & 0xFFFFFFFF)` (cluster seeds) | dedicated, seeded from `self.seed` |
| `random.Random(self.seed * 977 + 13)` (torii count) | dedicated, seeded from `self.seed` |

**`roll_village` itself makes ZERO draws from the main stream.** Every generator it constructs is
seeded deterministically from `self.seed`. The main-stream draws all happen inside the engine
methods it calls (`lane`, `try_place`, `farmsteads`, `place_wells`, `village_grove`, `hinterland`,
`bridges`), so output is preserved by anything that preserves the ORDER of those calls - which a
verbatim text move into stage methods does. This is the opposite of what `future-work.md` guessed
("its draw density is likely much higher and the answer may well go the other way"), and knowing it
is what makes this a safe refactor rather than a re-roll.

The second pre-flight check `future-work.md` prescribes - an AST walk for nested `FunctionDef`s -
reports exactly **one** closure, `to_screen`, over six frame values (`ccx`, `ccy`, `alx`, `aly`,
`tdx`, `tdy`). That is one shared lattice, not eight, and it is handled by making the frame an
explicit value object.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Behavior-preserving package split (Priority: P1)

A session opens the engine to change one link of the rolling chain and loads only that link.
`settlement/rolling.py` becomes `settlement/rolling/`, six submodules plus a composed
`RollingMixin`, indexed by a `CLAUDE.md` with a "look here when" row each. Nothing above the
directory knows: `settlement/core.py`'s `from .rolling import RollingMixin` still resolves and the
file stays byte-unchanged, and every pool generator, test and tool that reaches these methods
through `self.` or through `settlement.Settlement` is untouched.

**Why this priority**: it is the clause-13 obligation and the larger of the two token wins, and it
carries no behavioral risk - a member move changes where a method's TEXT lives, never when it runs.

**Independent Test**: ship the split with `roll_village` moved verbatim as one body. The pool
regenerates byte-identically, the gate is green, and no consumer file changes. That alone is a
complete, valuable feature.

**Acceptance Scenarios**:

1. **Given** the split package, **When** every `pool/` generator is regenerated in a scratch copy
   (frozen legacy maps included), **Then** every produced artifact is byte-identical to a pre-split
   baseline.
2. **Given** the split package, **When** `make done` runs, **Then** it is green with the
   `settlement/` coverage ratchet at or above its floor.
3. **Given** the split package, **When** `git diff --stat` is read, **Then** no file outside
   `settlement/rolling*`, `settlement/CLAUDE.md`, `settlement/civic_grounds/CLAUDE.md`,
   `future-work.md` and `specs/118-*` has changed - `settlement/core.py` included.
4. **Given** any submodule, **When** its raw line count is taken, **Then** it is under 1,000 and in
   family with the six sibling packages (36-407 lines).

---

### User Story 2 - roll_village decomposed into named stages (Priority: P2)

A session tuning one phase of the seed-rolled village - where the cluster band is seated, how the
windbreak belt is derived, which civic features a village gets - reads and edits a named stage
method instead of finding its banner comment inside a 256-line body. Every stage is separately
invocable, which is the architectural cost clause 12 exists to prevent (`gate()` reaching 12,944
lines is the constitution's motivating case, and "nothing inside it could be invoked separately"
is what made it a problem).

**Why this priority**: it is the smaller token win and the one carrying real (if measured-away)
risk, so it ships second and behind the same oracle. It is also the half `future-work.md` has been
holding open.

**Independent Test**: with the split already landed, decompose and re-run the same byte-identity
oracle plus the gate. Identical artifacts prove the stages preserved call order.

**Acceptance Scenarios**:

1. **Given** the decomposed `roll_village`, **When** the pool byte-identity sweep runs, **Then**
   every artifact is byte-identical - in particular `honda`, `shimizu` and `kikuta`, the three
   generators that call `roll_village`.
2. **Given** the decomposed `roll_village`, **When** each resulting function's raw line count is
   taken, **Then** no function in `settlement/rolling/` exceeds the ~150-line bar features 112/115
   converged on.
3. **Given** the frame values that `to_screen` closed over, **When** a stage needs them, **Then**
   they arrive as an explicit value object rather than as a closure or as instance attributes
   smuggled onto `self`.

---

### User Story 3 - The indexes and the standing docs tell the truth afterwards (Priority: P3)

A session that has never seen this feature finds the new layout from the indexes it already reads,
and does not re-derive work this feature closed.

**Why this priority**: cheap, and the failure mode is silent - a stale index sends the next session
to a file that no longer exists.

**Independent Test**: read `settlement/CLAUDE.md` and follow its rows to real files.

**Acceptance Scenarios**:

1. **Given** `settlement/CLAUDE.md`, **When** its `rolling.py` row is read, **Then** it points at
   the package and its own index, in the form the six sibling packages use.
2. **Given** `future-work.md`, **When** its "next clause-12 candidate" section is read, **Then** it
   records the item as closed rather than pending, with the measured RNG finding preserved (the
   finding is reusable; the open task is not).
3. **Given** `settlement/civic_grounds/CLAUDE.md`, which cites `rolling.py (1,197)` as a
   then-larger unsplit file, **When** it is read, **Then** it does not assert as current a fact this
   feature made false.

---

### Edge Cases

- **A decorated member.** The decorator-safe slicing rule is inherited intact from 116 rather than
  re-derived: `@staticmethod` is live on `_bbox_of` and `_closest_on_seg`, and slicing by
  `node.lineno` instead of by the span above it would drop it silently - leaving a name that still
  exists, a package that still imports, a `mypy --strict` that still passes, and a method that is
  wrong at every call site.
- **A class-level constant separated from its consumers.** `_NUC_SIDES` is read by
  `_fits_any_side` and `_place_bundle_nucleated`, which land in different submodules. It stays with
  the nucleated placer and is reached through `self.` from the other, per the package convention.
- **An empty house list at the windbreak stage.** `roll_village` guards the well grid with
  `if hs:` and does NOT guard the windbreak derivation, which would divide by zero on an empty
  cluster. That asymmetry is pre-existing and is preserved exactly, not "fixed" under a refactor.
- **The name `rolling` colliding with the package.** `settlement/rolling.py` and
  `settlement/rolling/` cannot coexist; the old file is deleted in the same change that creates
  the package, and a stale `__pycache__` entry must not be able to shadow it.
- **A monkeypatching test.** No test in the suite patches a `settlement` module-level name (census
  in `specs/025-human-scale-splits/consumer-census.json`); the split re-confirms this rather than
  assuming it.
- **A concurrent split of a module this one imports from.** Feature 117 is turning `_geom.py` into
  `_geom/` at the same time. `from ._geom import ...` resolves either way, so the two features do
  not collide in code - but both edit the `settlement/CLAUDE.md` index table, which is a textual
  merge to resolve rather than a behavioral one.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `settlement/rolling.py` MUST be replaced by a `settlement/rolling/` package whose
  submodules are each under 1,000 raw lines.
- **FR-002**: The package MUST expose a `RollingMixin` with exactly the member surface the current
  class has - no name added, no name removed, no name defined twice.
- **FR-003**: `settlement/core.py` MUST be byte-unchanged.
- **FR-004**: Every member MUST move VERBATIM - its decorators, its preceding comment block and its
  internal comments included. Comment-line count across the package MUST equal the original's.
- **FR-005**: `roll_village` MUST be decomposed into named stage methods, with no resulting
  function over the ~150-line bar.
- **FR-006**: The decomposition MUST preserve the exact ORDER of every call that draws from the
  main RNG stream, and MUST NOT add or remove a draw.
- **FR-007**: The frame values `to_screen` closes over MUST be carried by an explicit value object,
  not by a closure spanning stages and not by new mutable state on `Settlement`.
- **FR-008**: The package MUST carry a `CLAUDE.md` index with a "look here when" row per submodule,
  matching the six sibling packages' form.
- **FR-009**: A guard test MUST assert the composed surface, and MUST be proven RED against a
  synthetic breakage before it is trusted (a lost member, and a name defined in two sub-mixins).
- **FR-010**: `settlement/CLAUDE.md`, `future-work.md` and `settlement/civic_grounds/CLAUDE.md`
  MUST be updated so no index asserts a fact this feature made false.
- **FR-011**: No consumer file - pool generator, test, tool, check - may need changing.
- **FR-012**: The unit tests in `tests/settlement/test_rolling.py` MUST pass unchanged. The file is
  343 lines, well under clause 13, so it stays one file (as `test_structures.py` did at 692 lines
  against a six-module `structures/`).

### Key Entities

- **Submodule**: one link of the rolling chain - a file, a sub-mixin class, a docstring saying what
  it is for, and a row in the package index.
- **Sub-mixin**: a class holding a slice of the current class body; composed into `RollingMixin`
  with no members of its own, exactly as `StructuresMixin` and `CivicGroundsMixin` are.
- **Stage**: a named method carved out of `roll_village`'s body, taking what it needs as parameters
  and returning what the next stage needs.
- **Margin frame**: the value object carrying the cluster band's origin and axes
  (`ccx`, `ccy`, `alx`, `aly`, `tdx`, `tdy`, `lat`, `dep`) plus the margin-frame-to-screen mapping.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The largest file a session must load to work on any one link of the rolling chain
  drops from 1,197 lines to under 350 - at least a 70% reduction in read cost per task.
- **SC-002**: No function in the resulting package exceeds 150 raw lines (from 256).
- **SC-003**: Every `pool/` artifact regenerated after the change is byte-identical to a
  pre-change baseline - 100%, generators and frozen legacy maps alike.
- **SC-004**: `make done` is green, with zero new failures against the baseline taken on unmodified
  code in a detached worktree (constitution Principle XIII).
- **SC-005**: Zero consumer files change.
- **SC-006**: Comment lines lost: 0.

  **Measured, and the two halves differ - recorded honestly rather than rounded to a pass.** The
  SPLIT met it exactly: 211 `#` lines before, 211 after. The DECOMPOSITION then took the package to
  198, because 22 comment lines became docstring text: the five `# --- banner ---` lines are now the
  stage names themselves, and the cluster-seat and windbreak explanations moved into
  `_roll_margin_frame`'s and `_roll_windbreak`'s docstrings, which is where a function's own
  reasoning belongs. Nine comment lines were ADDED (the `placed` annotation's rationale and the
  literal-arithmetic note). No PROSE was lost, and that is asserted rather than assumed - every
  migrated phrase was checked to still be present in the package text. The census remains the right
  guard for a pure move; it just cannot see a comment that legitimately became a docstring, so the
  phrase check is what covers the decomposition.

## Assumptions

- **The oracle is byte-identity, not judgment.** This is a pure refactor, so any artifact drift is
  a bug rather than a trade-off - which is also why it needs no `settlement-review` pass (same
  reasoning the `SeatMemo` change recorded: a change that is output-preserving by construction has
  a mechanical oracle).
- **The frozen legacy pool is included in the sweep** (`--frozen-ok`). The three `roll_village`
  callers - `honda`, `shimizu`, `kikuta` - are ALL frozen hand-authored maps, so a sweep that
  honored the freeze would exercise the feature's primary subject not at all.
- **The baseline is taken in a detached worktree**, never by stashing (CLAUDE.md, after a stash
  reverted a pool file underneath a live review agent).
- **`land.py` (1,187 lines) remains debt** and is explicitly out of scope; `_geom.py` (1,303) is
  being cut concurrently as feature 117. `land.py` is named here so the remaining clause-13 backlog
  stays visible rather than being quietly forgotten once the file the GM named is done.
- **Tests are not re-partitioned.** `tests/settlement/test_rolling.py` at 343 lines is under the
  bar; the tests/ mapping rule already survives a source file becoming a package.
- **The transformer is adapted, not rewritten.** 116's `split_shrines_wells.py` (itself descended
  from 114/113/112/025) carries the slicing rule that a fresh implementation gets wrong; it is the
  starting point.

# Research: Human-Scale Splits (025)

All NEEDS CLARIFICATION items resolved; each decision records rationale and alternatives per the
record-the-why rule. 024's research is the base layer; only deltas and new ground are here.

## R1 - The Settlement class splits as MIXINS, not module functions

**Decision**: `settlement.py` is one giant class (`Settlement`, 338 methods, lines 2032-16016)
plus ~2,000 lines of module-level helpers. The class splits into subsystem **mixin classes**, one
per new module, composed in `core.py`: `class Settlement(FieldsMixin, WaysMixin, ..., object)`.
Method bodies move verbatim. Class attributes (35 non-method statements in the class body) and
`__init__` stay in `core.py` with the composed class.

**Rationale**: the only pure-move shape for a monolithic class. Converting methods to module
functions would rewrite every `self.x` call site (thousands of edits, un-reviewable); keeping one
class in one file is the status quo the feature exists to end. Mixins preserve every runtime
lookup (`settlement.Settlement.method` identity, monkeypatch targets on the class, subclassing)
because the composed class's MRO resolves to the same single definition of each method.

**Alternatives considered**: (a) functions-with-explicit-state - rejected, not a pure move;
(b) `exec`/textual includes - rejected, unimportable garbage; (c) splitting the class into
multiple cooperating objects - a real redesign, explicitly not this feature's job.

## R2 - mypy --strict across mixins: `self: "Settlement"` annotations

**Decision**: every mixin method gets an explicit self annotation `self: "Settlement"` (string
form), with `from .core import Settlement` under `if TYPE_CHECKING:` in each mixin module. mypy
resolves all attribute access against the composed class; runtime sees no import cycle.

**Rationale**: settlement.py is fully strict today (the ratchet is retired) - the split must not
reopen it. Mixin methods reference attributes set in `__init__` and methods from sibling mixins;
without a self-type, mypy --strict fails on every such access. The self-annotation pattern is
mypy's documented answer, is mechanical (scriptable over 338 defs), and adds zero runtime cost.

**Alternatives considered**: (a) a base class declaring every attribute - duplicates `__init__`'s
truth, drifts; (b) Protocol per mixin - N protocols to maintain for zero gain; (c) `mypy` override
relaxing the package - reopens the retired ratchet, constitutionally backwards.

## R3 - Module grouping: contiguous method ranges cut at subsystem boundaries

**Decision**: mixin modules take **contiguous runs of the existing method order**, cut at theme
boundaries (024 R2's doctrine, applied to methods instead of registry rows), target <=~2,500
lines/file. The boundary map with explicit line ranges lives in data-model.md; the module-level
helpers (lines 1-2031) split into `_geom.py` (spatial/geometry/label helpers) and `_knobs.py`
(knob engine, roll helpers, population/capacity constants).

**Rationale**: contiguous cuts keep the mover script trivial and diffs verifiable (a reviewer can
prove "verbatim move" by comparing ranges); the file's existing order already clusters by
subsystem (fields -> water -> ways -> shrines/wells -> structures -> trades -> homesteads -> land
-> funerary -> city -> rolling -> finish), so contiguity and theme agree almost everywhere.
Methods keep their order within each module - diff-friendliness and the DRAW ORDER doctrine both
favor never reordering.

**Alternatives considered**: thematic cherry-picking across ranges - better names in 2-3 edge
cases, but breaks the verbatim-range proof and buys nothing a CLAUDE.md index line doesn't.

## R4 - Identity proof: byte-identical artifacts + gate verdicts + collection lists

**Decision**: three proof layers, all capture-then-compare (024 R5 lineage):

1. **Generation identity (US3)**: before the split, run every **regen-runnable** pool gen (the
   scripted hamlets/villages - the set `regen.py`/`poolmaps.py` will actually execute; the frozen
   hand-authored tiers never run by definition) plus a fixed-seed `hamletgen.py` cohort; record
   sha256 of each emitted `.svg` and `.json`. After: identical hashes. The `.png` is covered by
   the svg stamp logic (render_cache docstring) - svg identity implies png identity.
2. **Gate identity (US3)**: `check_village.gate()` verdict streams over every `pool/**/*.json`
   manifest and every regression fixture, pre vs post - reusing the 022 oracle-sweep method.
3. **Collection identity (US2/US4)**: `pytest --collect-only -q` node lists, sorted, pre vs post
   - zero nodes lost/added/renamed beyond the mechanical `test_checks.py::x` ->
   `test_checks/test_y.py::x` path prefix (compare on `::`-suffix).

**Rationale**: matches the proof shapes already trusted in this repo (022/023/024 oracle sweeps;
the mypy-strict migration's byte-identical map rule). "Tests still pass" alone cannot catch a
dropped test or a changed draw.

## R5 - Split-sensitive coverage/type machinery (found in recon, must move with the file)

**Decision**: US3 updates, in the same commit as the package lands:

- **Makefile**: `--omit='*/settlement.py'` -> `--omit='*/settlement/*'`;
  `--include='*/settlement.py'` -> `--include='*/settlement/*'`; `SETTLEMENT_COV_FLOOR = 94`
  keeps its value and its comment (the 2026-08-16 legacy-freeze ratchet now floors the package's
  COMBINED report - same discipline, same raise-never-lower rule; the uncovered town/city/capital
  wings will concentrate in specific package files, which the comment notes for the future
  tier-conversion raises).
- **pyproject.toml**: mypy `files` entry `"settlement.py"` -> `"settlement"`; coverage
  `source = ["settlement", ...]` already names the import path and keeps working for a package;
  ruff per-file-ignores gains `"settlement/__init__.py" = ["F401"]` (check_village precedent).

**Rationale**: without these the gate would either crash (mypy file not found) or silently stop
measuring settlement (coverage include pattern matching nothing = vacuous pass on some coverage
versions, hard fail on others) - both discovered by recon, neither acceptable to discover by gate
failure one at a time (CLAUDE.md ordering-read rule).

## R6 - render_cache.engine_fingerprint must learn about package engines

**Decision**: `engine_fingerprint()` currently hashes **root `*.py` files only**
(`os.listdir`, skip `test_*`), so a `settlement/` package would silently FALL OUT of the render
fingerprint - engine edits would stop invalidating pool renders, exactly the stale-render failure
the mechanism exists to prevent. Fix in US3: walk `settlement/` (and any future package whose
code determines renders) into the fingerprint - implementation: include `<dir>/*.py` for
non-test package directories, still excluding `check_village/` is NOT needed (safe-superset
doctrine in the docstring: over-including the validator costs at most a needless regen, and a
simple "all non-test .py under the skill root, any depth, minus pool/ and wip/ and this module"
rule is harder to get wrong than a curated list). Update `test_render_cache.py` expectations in
the same change; note the one-time full pool refresh this causes is a **non-event** because US3
proves byte-identical svg (stamps re-verify against unchanged bytes).

**Rationale**: recon caught a silent-staleness landmine; the safe-superset rule from the module's
own docstring decides the shape. 024 did not hit this because `check_village` never determined a
pixel; `settlement/` is the first render-determining package.

**Alternatives considered**: curated explicit list of engine dirs - one more thing to forget when
026 splits something else; rejected per the docstring's own under-inclusion warning.

## R7 - `settlement/__init__.py`: explicit re-export of the full legacy surface

**Decision**: generated explicit imports (024 R6 method) re-exporting every public name AND every
underscore name that any current caller references (`import settlement` consumers include
check_village segments, hamletgen, site_justice, why_placed, ~20 pool gens, wip gens, tests).
The mover script derives the needed-name set by scanning all importers for `settlement.<name>` /
`from settlement import ...` references and cross-checking against the monolith's namespace; the
import-surface contract (contracts/import-surface.md) records the generated list.

**Rationale**: star-imports hide breakage and fight ruff; a scanned+generated list is provable.
Underscore names are included when referenced (tests reach into `settlement._farm_wells`-style
internals today; a pure move may not break them).

## R8 - Test split shape: directory per old file, conftest.py for shared builders

**Decision**: `test_checks.py` -> `test_checks/` directory; `test_settlement.py` ->
`test_settlement/`. Each test directory is a **package** (`__init__.py`), with the shared fixture
builders (test_checks.py's `f`, `bldg`, `manifest`, `house`, `yard`, `garden`, `well`, `grove`,
`vgrove`, `_channel`, `_drain`, `_dryplot`, ...) moved verbatim into a `_builders.py` module
inside it; test modules use `from test_checks._builders import ...`. The builders stay plain
functions - NO conversion to pytest fixtures (not a pure move), and no importing helpers from
`conftest.py` (an import-from-conftest antipattern; a `conftest.py` appears only if a genuine
pytest fixture ever emerges - none exists today). Test function bodies move verbatim; only the
import line at the top of each new module is new. Module boundaries mirror the source package:
one `test_segments_*.py` per `check_village`
segment file (grouping = which segment file the tested check lives in, derived from the
registry), `test_common_*.py` for helper tests, `test_driver_and_fixtures.py` for gate-driver
and cross-cutting tests. US4 mirrors the final `settlement/` module map the same way.

**Rationale**: package-with-`__init__` makes helper imports unambiguous under pytest's rootdir
rules and keeps `python3 -m pytest` from the skill dir collecting identically; `_builders.py`
avoids conftest-import smell while keeping every test body verbatim. Mapping tests to the source
file they exercise is exactly the "load one subfile alongside" economics clause 13 wants.

**Alternatives considered**: flat sibling files (`test_checks_water.py`, ...) - keeps collection
trivially identical but violates the directory-module + CLAUDE.md-index target shape and leaves
11 more root entries; rejected. Converting builders to pytest fixtures - not a pure move,
rejected.

## R9 - Monkeypatch reach after the split (check_village's lesson, applied preemptively)

**Decision**: census every `monkeypatch.setattr(settlement, ...)` / `patch("settlement....")`
target in the test suite during US3; for each, either (a) the target is a `Settlement` method or
class attribute - unaffected (mixin composition preserves class-level patching), or (b) the
target is a module-level name now living in a submodule - the TEST updates to patch the defining
submodule, and the `settlement/` CLAUDE.md gets the same "Monkeypatching a policy table" section
check_village's index carries. No shim indirection in production code.

**Rationale**: check_village hit this exact hazard (its CLAUDE.md documents the multi-holder
patch loop); doing the census up front converts a class of silent test-lies into a mechanical
checklist item.

## R10 - Constitution mechanics: PATCH 1.6.0 -> 1.6.1

**Decision**: amending clause 13's wording to state test files are covered is a
**clarification of an existing rule's reach**, not new guidance: PATCH per the constitution's
semver policy (wording/scope clarifications = patch; new principles/clauses = minor). Sync-impact
header updated; the same amendment commit updates both mirrors (root CLAUDE.md "Files stay at
human scale" bullet; plan-template Principle X gate text, which already says "source file" - it
gains "(tests included)"). Spec's defer-to-policy fallback checked: the policy text supports
patch for clarifications.

**Rationale**: 024's MINOR bump added the clause; saying what the clause already-implicitly
covered is the canonical patch case. The GM's own scope statement called it a patch bump.

## R11 - Explicitly out of scope, recorded

- **check_village/registry.py** (8,420 lines): ordered-data exemption holds; its serious
  refactor is a SEPARATE future effort (GM 2026-08-16, also in session memory). Not touched.
- **British spellings in pre-existing test names** (e.g. `..._two_neighbours_...`): pure move
  keeps them verbatim; renames would break the collection-identity proof. New identifiers
  introduced by this feature (module names, builder-module names) follow the American-spelling
  rule.
- **waterfields.py / hamletgen.py** (2,619 / 2,736 lines): above the clause-13 line but NOT in
  the GM-approved scope for this feature; they remain ask-the-question candidates for a future
  feature. Recorded so it is a decision, not an oversight.
- **test_villages.py / other mid-size test files**: under threshold after this feature's three
  splits; untouched.

## R12 - Story landing order and gate cadence

**Decision**: US1 -> US2 -> US3 -> US4, one commit-and-green-gate landing per story (FR-008).
US2 before US3 (independent, cheapest first, proves the test-split mechanics US4 reuses);
US4 strictly after US3. The `make done` gate runs from the clone per its guard; docs-only US1
skips the gate per the docs-only rule but greps its three mirror sites as verification.

**Rationale**: spec's Assumptions, GM-approved; matches 024's stage discipline (stage commits
with a green gate each).

## R13 - What implementation taught the plan (added during implement, 2026-08-16)

**Census, before -> after** (T501): 34,614 lines in 3 files -> 35,471 lines in 54 files (+857
lines of import/annotation/docstring glue), largest single file 1,582 (`settlement/city.py`).
`settlement/`: 17 files, largest 1,582. `test_checks/`: 19 files, largest 1,537 (`_builders.py`).
`test_settlement/`: 18 files, largest 770. Every file is under the FR-009 bar; the E1 boundary
map held with zero range deviations.

**Mover lessons** (settlement.py):
- Top-level `Expr` calls must route POSITIONALLY: the knob catalog's `register_knob(...)` calls
  and the import-time guard are executable statements that belong right after their definitions,
  not in `__init__.py`.
- Interleaved class-body attribute assignments ride inside the contiguous METHOD slices; emitting
  them separately in core.py duplicated 35 definitions (caught via `_CROP_MARGIN_FT` appearing
  twice). An attribute now lives (once) on whichever mixin owns the method that follows it -
  reachable via the MRO exactly as before.
- Five attrs whose FIRST textual definition moved ahead of `__init__` (monolith had class attrs
  AFTER `__init__`, so mypy used the `__init__` annotation; mixin bases now declare first) needed
  the `__init__` annotation mirrored at the mixin site; two tuple-assignments were split into
  sequential statements to make room for the annotation.
- **mypy --strict x mixins**: the `self: "Settlement"` pattern itself trips "erased type of self
  is not a supertype of its class" ([misc]) while still fully checking every body against
  Settlement - silenced per def line with `# type: ignore[misc]`, nothing broader. Strict
  `no_implicit_reexport` requires the `X as X` re-export form in `__init__.py`. PEP 649 lazy
  annotations mean annotation-only names are invisible to symtable - the import synthesizer must
  walk annotations explicitly - and `type X = ...` aliases need their own AST case.
- **Runtime `Settlement.<CLASS_ATTR>` reads** (5 sites: crop_boxes in _knobs, ward in
  water_ways, city wall internals in city.py) get a function-local `from .core import Settlement`
  - the TYPE_CHECKING import satisfies mypy but NOT runtime, and the generation oracle only
  catches the sites the scripted tiers exercise; the frozen city wings surfaced theirs via unit
  tests only. Grep for `Settlement\.` is part of any future re-run of the mover.

**A second cache landmine beyond R6**: `gencache.engine_files()` had the same root-only
`os.listdir` shape as `render_cache.engine_fingerprint()` - after the split it recorded ZERO
settlement deps, caught by `test_gencache`'s "a real gen must record engine deps". Same fix
(walk, prune pool/wip/caches/test dirs), and its key change invalidates every gencache entry
once - a non-event, same reasoning as R6.

**Consumers that reached THROUGH the monolith**: tests used `settlement.math.radians` (stdlib
via engine module - an accident; tests now import math), `test_why_placed` and `test_gencache`
asserted the literal frame/dep filename `settlement.py` (now a package-path assertion), and
`why_placed`'s docstrings named the file (re-worded).

**US2/US4 splitter lessons** (split_tests.py):
- The flat test_checks.py defined `_CITY_WALL` TWICE with different values; tests were written
  against whichever definition was in scope at their line. The split renamed the second to
  `_CITY_WALL_SMALL` and repointed exactly the tests after the second definition (by original
  lineno). A dup-with-different-value scan is now a standard step; US4 had none.
- Import synthesis must be SCOPE-AWARE (symtable free reads, not raw Name occurrences): tests
  that locally assign `well`/`house`/`WALLSQ` inside their bodies otherwise pull spurious
  builder imports (F401/F811). Bare-name engine calls (`Settlement(...)`) additionally need
  from-import resolution against the engine namespaces.
- Both flat files carried a pre-pytest `if __name__ == "__main__"` runner iterating globals();
  dropped (runner convenience, superseded by pytest - collection identity is proven on the
  ::-suffix node lists, 2,899 nodes for each split, zero drift).
- `Path(__file__).parent` sites are rewritten `.parent.parent` (asserted count: 2 in US2, 0 in
  US4).

**Oracle mechanics**: hamletgen's cohort must respect the 10-20 household band and passes
`--no-render` (svg identity implies png per render_cache doctrine); svg hashes are compared with
the `render-cache:` stamp line stripped, since the stamp hashes the engine fingerprint and
changes BY DESIGN across the split while drawn bytes must not. Final sweeps: 9 generation
artifacts and 818 gate manifests, 0 drifted, twice (before and after the post-gate fixes).

**Process reminders re-learned the hard way**: a `pytest --collect-only` run in the skill dir
DURING a background gate clobbers `.coverage` mid-read (the baseline gate's "ratchet failure"
was exactly this, not a real shortfall), and piping `make done` through `tail` masks the exit
code - the memory note "background gate exit codes lie if wrapped" applies to pipes too, and one
US3 commit briefly landed on a red gate because of it (amended after fixing forward).

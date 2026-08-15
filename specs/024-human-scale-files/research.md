# Research: Human-Scale Files (024)

All decisions resolved; no NEEDS CLARIFICATION remain. The census numbers below were produced by
AST scripts against the monolith - the file itself was never loaded into a context window.

## R1 - Order of operations: split segments first, move files second

**Decision**: Stage 1 splits the oversized segments while `check_village.py` is still one file;
stage 2 moves the (now finer-grained) contents into the package.

**Rationale**: the 022/023 tooling (`transform_gate.py`, `split_megaseg.py`) targets the
single-file format - segment function + registry row in one module. Reusing it against the format
it was proven on is lower-risk than porting it to a package layout. Each stage also gets its own
oracle diff, so a verdict drift isolates to either "split logic wrong" or "move/imports wrong",
never both.

**Alternatives considered**: package-first (would force the split tooling to resolve
cross-module references); one combined pass (conflates the two failure classes in one diff).

## R2 - Package file grouping: contiguous registry ranges, theme-named

**Decision**: segment files are CONTIGUOUS ranges of the existing definition order, cut at theme
boundaries (~10-14 files, each ≤ ~3,000 lines), named `segments_NN_<theme>.py` where NN preserves
order and `<theme>` comes from the dominant check-name vocabulary of the range (frame/overlap,
water, fields, dwellings, shrine+temple, town, city, capital, justice+outcast, polder...).
The pre-segment common region (lines 1-2630) splits the same way into ~3 contiguous
`common_*.py` files (spatial/geometry helpers; overlap+label policy tables; capacity + segment
plumbing). `registry.py` and `driver.py` close the package.

**Rationale**: contiguity makes the move provably order-preserving (concatenating the files in
name order reproduces the monolith's definition order), keeps the split script simple, and keeps
top-level constant-initialization order intact (later constants are computed from earlier
helpers). Thematic names are what the CLAUDE.md index needs - registry order already roughly
clusters by theme because checks were appended battery by battery.

**Alternatives considered**: semantic regrouping ignoring source order (better theming, but
import-order hazards for derived constants and a much harder identity argument); one file per
registry battery number (opaque names, useless index).

## R3 - Which segments get split: ≥300 raw lines AND ≥2 emitted checks

**Decision**: the nine segments over 300 raw lines are all multi-check bundles; every one is
split per-check (method R5). Census (raw lines / stmt units / emitted check names):

| segment | lines | units | checks |
|---|---|---|---|
| `_seg_0285__wells_clear_of_shrine_and_torii` | 1,351 | 427 | 42 |
| `_seg_0286__cemetery_clear_of_shrine` | 511 | 139 | 20 |
| `_seg_0562__settlement_has_tanning_yard` | 495 | 117 | 10 |
| `_seg_0543__town_farmers_plurality` | 483 | 161 | 31 |
| `_seg_0106__capital_declares_a_budget` | 465 | 137 | 19 |
| `_seg_0523__drain_flows_downhill` | 417 | 111 | 6 |
| `_seg_0555__punishment_spot_in_the_core` | 349 | 70 | 19 |
| `_seg_0040__city_commoner_dwellings_inside_walls` | 337 | 90 | 7 |
| `_seg_0438__near_ring_cultivated_fraction` | 320 | 86 | 2 |

**Rationale**: the GM named 0285/0286/0562/0543/0106 explicitly and asked for "the other
functions as well"; 300 raw lines is where the remaining candidates end and single-concern
segments begin (next is `_seg_0133` at 289 lines - captured too if its statement boundaries
allow a clean per-check cut, otherwise it stands: it is 100 units, comfortably clause-12-legal).
By clause-12 LOGIC UNITS only `_seg_0285` (427) is past "a few hundred"; the others are split
for concern-separation and `only=` targetability, not because they are illegal sizes.

**Disposition of everything else**: all remaining segments are ≤ ~65 units - no annotations
needed anywhere; after this feature no function in the package exceeds clause 12.

## R4 - Split method: per-check statement grouping, 023 mechanics

**Decision**: adapt `specs/023-split-city-mega-segment/split_megaseg.py` into
`split_oversized.py`: for each target segment, walk its top-level statements, assign each
statement to the check name(s) it feeds (a statement group ends at each `check(...)` call
boundary, exactly 023's rule), emit `_seg_NNNN_MMM__<checkname>` functions with bodies moved
VERBATIM, params = the names each new body reads (bound from gate scope), `writes` = names later
segments/groups read, and replace the one registry row with the ordered row run. Guards stay in
the body (023's `# noqa: SIM102` convention where a comment bank sits under a guard); ruff's
SIM102 autofix may combine them afterwards with identity re-proven.

**Rationale**: proven twice (022 whole-gate, 023 the 1,040-statement urban battery); the oracle
sweeps caught all three known dataflow holes (helper-closure mutation, upward-exposed reads vs
raw loads, comprehension-target scoping - 022 research.md R9) and those rules are already encoded
in the tooling being adapted.

## R5 - Identity proof: reuse the 022 oracle sweep unchanged

**Decision**: `specs/022-gate-check-registry/oracle_sweep.py` runs as-is for capture / compare /
targeted at every stage. Baselines live in `specs/024-human-scale-files/` (`oracle_pre.json`
against the untouched monolith; compare after stage 1 and again after stage 2).

**Rationale**: it hashes verbose stdout per fixture - byte identity, not approximate - over all
regression fixtures + pool manifests, and its `targeted` mode re-proves the `only=` closure
contract. It imports `check_village` by module name, which resolves identically once the package
exists. Nothing to port.

## R6 - `__init__.py`: generated explicit re-exports, no star imports

**Decision**: the mover script generates `__init__.py` with explicit
`from .common_x import (name, ...)` blocks covering EVERY module-level name (public and
underscore) in original definition order, plus `registry` and `driver` names (`gate`,
`GATE_SEGMENTS`, `META_CHECKS`, `twin_report`, ...). Per-module imports inside segment files are
likewise generated explicitly from each function's free-name analysis (free names minus params
minus builtins, mapped to the defining module).

**Rationale**: tests and tools reach into internals (`import check_village` then attribute
access - `cohort_audit`, `site_justice`, `make_regressions`, four test modules), so the package
must re-export the full legacy surface. Star imports would trip ruff F403/F405 and hide
resolution errors; explicit generated lists fail loudly and read greppably.

## R7 - CLI: `python3 -m check_village`, docs updated

**Decision**: the monolith's `if __name__ == "__main__"` block becomes `__main__.py`; every doc
command line `python3 check_village.py X` becomes `python3 -m check_village X` (grep sweep across
`.claude/skills/diagram/**/*.md` and reference docs).

**Rationale**: a package cannot be invoked by filename; `-m` preserves the standalone-gate
workflow with the diagram dir as cwd (sys.path root), which is also how the sibling imports
(`from settlement import ...`) already resolve.

## R8 - `registry.py` exceeds the file threshold: justified as ordered data

**Decision**: `GATE_SEGMENTS` stays ONE tuple in ONE file (~7,300 lines of dense rows, `# fmt:
off`), with an inline justification comment at the top of the file citing constitution clause 13:
the rows are ordered DATA whose order IS the execution contract; splitting them across files
would make order un-auditable for zero token benefit (nobody reads the registry linearly; the
`only=` mechanism is how you find a row). The stale "586 dense data rows" comment is refreshed
to the true count while we are in there.

**Rationale**: clause 13 (like clause 12) is an ask-the-question threshold, not a mandate; this
is the canonical legitimate exception and gets recorded as the exemplar.

## R9 - waterfields.py engine builders exempt (clause 12, recorded)

**Decision**: `build_comb` (459 lines), `build_polder` (456), `_carve` (435) are NOT split.
They are deep-but-cohesive engine functions - single-concern geometry builders - exactly the
shape clause 12 legitimizes. No annotation is required (they are under ~1,000 units); this note
is the recorded disposition FR-011 asks for.

## R10 - settlement.py (15,993 lines) deferred, deliberately

**Decision**: out of scope. The rule makes it an ask-the-question candidate; this feature
establishes the pattern on the largest offender. A future feature can apply the same mover
script. Recorded so it is a decision, not an oversight. Same for `test_checks.py` and other
large test files - test modules are read selectively by test name and are a lower token cost in
practice; the clause covers them but this feature does not.

## R11 - The file threshold is RAW LINES (unlike clause 12's logic units)

**Decision**: clause 13 measures files in raw lines (~1,000 ask-the-question line).

**Rationale**: the motivating cost is context-window tokens, which scale with raw text - a
1,000-line file of dense one-line data rows costs the same tokens as 1,000 lines of sprawling
logic. Clause 12 uses logic units because ITS motivating cost (unreviewable, uninvokable
structure) scales with logic, not text. The asymmetry is deliberate and the clause says so.

## R12 - Constitution mechanics

**Decision**: version 1.5.0 → 1.6.0 (MINOR - material expansion of Principle X, mirroring
clause 12's own 1.4.2 → 1.5.0 bump); new SYNC IMPACT REPORT header entry; the plan template's
Principle X gate text gains one sentence ("Files stay at human scale too..."); CLAUDE.md's
Development Workflow gets a one-line operational mirror. The amendment procedure (edit +
sync-report + dependent-template review) is followed literally; the GM directed the change in
conversation on 2026-08-15, which is the approval the procedure requires.

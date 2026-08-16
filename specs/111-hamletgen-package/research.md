# Phase 0 Research: hamletgen.py -> hamletgen/ Package Split

**Feature**: 111-hamletgen-package | **Date**: 2026-08-16

Every question this feature had to settle before code moved, with the decision, why, and what else
was weighed. Measurements were taken against `hamletgen.py` at clone HEAD `665db35` (2,913 raw
lines, 69 top-level defs/classes, 34 module-level assignments).

---

## R1. The partition - where do the seams go?

**Decision**: ten code submodules plus a constants module, a derived `__init__.py`, and a
`__main__.py` shim, cutting on the file's own STAGE banner comments:

| module | holds | span in the monolith | lines |
|---|---|---|---|
| `consts.py` | `Pt`/`Poly` aliases + the 32 researched constants | L81-323 | ~243 |
| `plan.py` | `HamletSpec`, `SitePlan`, `_roll`, `offtakes_for`, `canvas_for`, `windward_for`, `plan_site` | L324-505 | 182 |
| `geom.py` | `poly_area`, `net_acres`, `centroid`, `unit`, `crop_polys`, `pull_clear`, `crosses_disc`, `crosses_poly` | L511-586 | 76 |
| `water.py` | STAGE 1-2: `stage_water_frame`, `fit_field`, `_fit_at_aspect`, `head_sluice`, `tail_dangles`, `net_bends_acutely`, `feed_brook`, `stage_polder`, `fit_polder`, `stage_field` | L592-1040 | 449 |
| `sink.py` | STAGE 3: `drain_outfall`, `drain_heading`, `edge_run`, `pond_clear_of_crop`, `pond_setback`, `stage_sink` | L1046-1282 | 237 |
| `cluster.py` | STAGE 4a: `below_drain`, `back_fouled`, `seat_cluster`, `_arm_hit`, `_arm_crossing_accidental`, `_fork_spur` | L1288-1511 | 224 |
| `ways.py` | STAGE 4b: `stage_ways`, `push_out_of`, `route_around`, `clip_to_clear`, `polyline_len`, `connector_track`, `path_violations`, `crossing_lands_on_crop`, `shallow_crossing` | L1514-1955 | 442 |
| `homesteads.py` | STAGE 5-6: `front_row`, `lane_frontage`, `stage_homesteads`, `stage_appurtenances`, `well_target`, `place_wells` | L1961-2323 | 363 |
| `hinterland.py` | STAGE 7: `stage_hinterland`, `open_ground_patches`, `content_box`, `title_pocket`, `_clear_gap`, `_near_line`, `stage_woodland`, `stage_windbreak`, `belt_polygon` | L2329-2695 | 367 |
| `frame.py` | STAGE 8: `stage_crossings`, `stage_notice`, `stage_frame` | L2701-2787 | 87 |
| `driver.py` | `STAGES`, `Report`, `build`, `generate`, `cohort`, `main` | L2791-2909 | ~119 |

**Rationale**: the module docstring says "THE ORDER IS THE DESIGN," and the author already drew the
seams as banner comments (`# ---- STAGE 4: seating the settlement, and its ways ----`). Cutting
anywhere else would fight the file. Every resulting module is well under the clause-13 bar, the
largest being `water.py` at 449 and `ways.py` at 442 - roughly the shape feature 110 landed
(`comb.py` 784, `polder.py` 782).

**One deliberate departure from the banners**: STAGE 4 covers both seating the cluster and laying
its ways, 670 lines together. It splits at the natural internal boundary (L1511/L1514) into
`cluster.py` (where the settlement sits) and `ways.py` (the lanes and the connector track), because
those are separately loadable concerns and 670 lines in one file re-creates the problem this
feature exists to solve. `ways.py` imports `cluster.py`, so the DAG stays a DAG.

**Import DAG verified acyclic** by AST analysis of every cross-group name reference:

```text
consts  (leaf)
plan    -> consts
geom    -> consts
water, sink, cluster, homesteads, hinterland, frame  -> plan, geom, consts
ways    -> cluster, plan, geom, consts
driver  -> every stage module (via the STAGES tuple)
```

Zero 2-cycles. One apparent `water -> driver` edge was investigated and is a **false positive**:
`stage_polder` binds a LOCAL variable named `main` (L849), which the name-based analysis matched
against `driver.main`. No real dependency exists.

**Alternatives considered**:

- *One module per STAGE banner, eight modules.* Rejected: leaves the 670-line STAGE 4 module and
  gives no home to the constants block or the shared geometry helpers, which are used by six
  modules each.
- *Split by object type (dataclasses / predicates / stages / driver).* Rejected: a session works on
  a STAGE, not on "all the predicates"; a type-based split scatters every concern across every
  file, which is the opposite of the token goal.
- *Sub-packages (`hamletgen/stages/`, `hamletgen/geom/`).* Rejected as premature: eleven flat
  modules are navigable from one index table, and `check_village/` (23 flat modules) shows the flat
  shape scales further than this.

---

## R2. The consumed surface - what must the package reproduce?

**Decision**: preserve 47 attribute names reached via `import hamletgen as hg`, plus the two names
imported directly by pool gens (`HamletSpec`, `generate`). A star-import `__init__.py` carries the
public names; an explicit aliased block carries the four underscore names.

**Measured census** (grep across the skill tree at HEAD):

- `pool/hamlets/{inashiro,mizuguchi,kashikawa,sawada}.gen.py`: `from hamletgen import HamletSpec, generate`
- `test_hamletgen.py`, `cohort_audit.py`: `import hamletgen as hg`, reaching 47 distinct attributes.
- Underscore names in that set (dropped by a bare star import, so they need the aliased block):
  `_arm_crossing_accidental`, `_clear_gap`, `_fork_spur`, `_near_line`.
- **Pass-through name**: `hg.point_in_poly` is NOT defined in `hamletgen` - the monolith imports it
  from `settlement` and consumers reach it through the module. The package must keep it reachable
  from the package root. It is re-exported from whichever submodule imports it (`geom.py`), which a
  star import carries because it is a public name.

**Rationale**: this is exactly the mechanism features 027 (check_village) and 110 (waterfields)
established, and it satisfies constitution clause 14 - the surface is DERIVED (stars) rather than a
hand-maintained roster that drifts.

**Alternatives considered**: an explicit `__all__` roster listing all 47 names. Rejected by clause
14 directly - a roster that restates what the submodules already declare is derived data, and 027
collapsed a 3,148-line roster to 63 lines for exactly this reason.

---

## R3. The oracle - what proves nothing changed?

**Decision**: byte-identical manifests, with the baseline captured from a **scratch copy of the
pre-split tree**, covering the four live hamlets at their committed seeds plus a fixed-seed cohort
sweep (`--batch`, seeds 1-24).

**Rationale**: `hamletgen` is fully deterministic per seed (a local `random.Random(seed)`, per the
module docstring), so identical inputs must give identical bytes. Feature 110's research R3 found
that the committed pool manifests are NOT a valid baseline on their own - the pool is frozen
against re-rolls, so a committed artifact can predate engine changes. Copying the tree at HEAD to
the scratchpad and running the gens there produces a baseline that is provably what today's code
does.

The cohort sweep matters more here than it did for waterfields: the four live hamlets exercise four
seeds, while `hamletgen`'s stages contain retry loops and archetype rolls whose branches only
appear on other seeds. 24 seeds covers the branch space at a cost of seconds.

**Alternatives considered**:

- *Tests alone as the oracle.* Rejected: `test_hamletgen.py` is 714 lines of unit tests over stage
  functions; it would not catch a reordered RNG draw that shifts every coordinate while every unit
  assertion still holds.
- *SVG diffing.* Redundant - the SVG is drawn from the manifest, so manifest identity implies it.
  SVGs are captured anyway since the gens emit them for free.

---

## R4. Tooling configuration

**Decision**: three config edits, all in `.claude/skills/diagram/pyproject.toml`:

1. `[tool.mypy] files`: `"hamletgen.py"` -> `"hamletgen"`.
2. `[tool.coverage.run] source`: `"hamletgen"` already names the module and resolves to the package
   unchanged - **no edit needed**, verified by the fact that `settlement`, `check_village` and
   `waterfields` are packages listed the same way.
3. `[tool.ruff.lint.per-file-ignores]`: add `"hamletgen/__init__.py" = ["F401", "F403"]` with the
   same why-comment style as the three existing entries.

**Coverage stays at 100%** for `hamletgen` - the Makefile enforces 100% on every module except
`settlement.py` (which carries a ratchet floor). The split must not drop a line into an untested
module; the test package mirrors the source package so every module keeps its tests.

---

## R5. Decomposition method for the oversized functions

**Decision**: mechanical extraction only. Preserve code order, RNG draw order and float-operation
order exactly; pass state in as parameters and return values out; introduce no shared mutable
module state; verify byte-identity after EACH function, one commit per function.

**Targets** (9 functions at or above ~85 lines):

| function | module | lines |
|---|---|---|
| `stage_ways` | ways | 177 |
| `stage_sink` | sink | 168 |
| `place_wells` | homesteads | 164 |
| `open_ground_patches` | hinterland | 137 |
| `seat_cluster` | cluster | 127 |
| `stage_polder` | water | 126 |
| `stage_homesteads` | homesteads | 111 |
| `connector_track` | ways | 89 |
| `belt_polygon` | hinterland | 85 |

**Rationale**: floating-point arithmetic is not associative, and the generator seeds a local RNG
whose draw sequence sets every coordinate. Any "while I'm here" tidy - reordering two independent
statements, hoisting a computation out of a loop, replacing `a*b + c` with `math.fma`-equivalent
regrouping - can shift a coordinate by an ULP and cascade. So the extraction is a cut-and-lift, not
a rewrite. This is the method 110 used across `_carve`, `build_comb` and `build_polder` with an
empty diff every time.

**Constitution clause 12 note**: the bar is ~150 lines with an inline justification permitted for a
genuinely atomic stage. Feature 024's research R9 had recorded a disposition of "do not split the
engine builders"; feature 110 superseded that on explicit GM request (2026-08-16) and this feature
continues under the superseding rule.

---

## R6. `STAGES` - the pipeline contract

**Decision**: `STAGES` lives in `driver.py`, in its current order, with a comment at that point
stating the order is the design and is shared with the skill's DRAW ORDER map
(`.claude/skills/diagram/CLAUDE.md`).

**Rationale**: the project's standing rule is that where ordering-critical code is added, a comment
goes at the point of change, because a rule in a document nobody re-reads does not hold. `driver.py`
is the one module that imports every stage, so it is the only place the whole sequence is visible;
splitting the tuple, or deriving it from module order, would hide the contract.

**Alternatives considered**: deriving `STAGES` by introspecting the submodules for `stage_*`
functions. Rejected - the order is a DECISION (water before the field the water shapes, ways before
the homesteads that front them), not a fact recoverable from the code, so clause 14's "derive"
guidance does not apply. This is precisely the ordered-data case the clause carves out.

---

## R7. The `sys.path` bootstrap and the CLI

**Decision**: the `HERE`/`sys.path` bootstrap moves to `__init__.py`, ahead of the star imports.
`main` STAYS in `driver.py` (consumers reach `hg.main`); `__main__.py` is a three-line shim that
imports and calls it.

**Rationale**: package `__init__.py` always runs before any submodule import, so the bootstrap is
in force for `import hamletgen`, `from hamletgen.ways import ...`, and `python3 -m hamletgen`
alike. Putting `main` in `__main__.py` would break `hg.main` (four uses in `cohort_audit.py`) and
would make it unreachable from `import hamletgen` - `__main__.py` is not imported by the package.

**CLI invocation changes** from `python3 hamletgen.py --batch 12` to `python3 -m hamletgen
--batch 12`, matching `check_village`'s post-split form. Docs naming the old form get updated
(R8).

---

## R8. Documentation touch list

**Decision**: update FILE-path references to `hamletgen.py`; leave importable-path prose
(`hamletgen.seat_cluster`) and historical `specs/NNN` artifacts verbatim.

Files that mention `hamletgen.py` today: `CLAUDE.md` (skill), `SKILL.md`, `hamletgen.md`,
`migration-plan.md`, and the four `pool/hamlets/*.notes.md`. The notes files are per-map records of
what was built and when; they get the path fix only where they name the file as a path to run, not
where they narrate history.

---

## R9. The test split

**Decision**: `test_hamletgen.py` (714 lines) becomes `test_hamletgen/` with one module per source
submodule that has tests, plus `__init__.py`. No test is deleted, renamed in substance, or skipped;
only module paths change.

**Rationale**: constitution v1.6.1 states tests are covered by clause 13 exactly as source, and the
motivating case named there was a test file split alongside its source. 714 lines is under the bar
today, so this is preventive - but the source/test correspondence is cheapest to establish now, by
the same pass that chose the partition, and `test_settlement/` and `test_checks/` are the
established shape.

**Alternatives considered**: leave `test_hamletgen.py` whole. Rejected on the same reasoning the
GM applied in v1.6.1 - a session modifying `ways.py` should load `test_hamletgen/test_ways.py`, not
all 714 lines; and after decomposition the file will grow, not shrink.

---

## R10. What is explicitly NOT in scope

No behavior change of any kind. `future-work.md` carries three open items touching this module -
the well minimax objective counting stream-watered houses, the envelope-trim near-duplicate vertex
dedup, and unrecorded woodland stand crowns. All three stay open. Fixing any of them would change
output and destroy the byte-identity oracle that makes this refactor verifiable.

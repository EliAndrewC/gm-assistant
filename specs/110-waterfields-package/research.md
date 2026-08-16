# Research: waterfields.py -> waterfields/ Package Split

**Feature**: 110-waterfields-package | **Date**: 2026-08-16

All items resolved empirically in-session (AST analysis, grep census, and config reads in the
`diagram-architecture` clone at HEAD `30fa670`).

## R1: Module partition - from the measured call graph

An AST walk of `waterfields.py` (31 top-level defs, 2,689 lines) produced the full internal
call graph. It layers cleanly with zero cycles:

- **Layer 0, frame math**: `_Frame`, `_Thread`, `_at_f`, `_f_at_u`, `_seg_x`, `_seg_d`, `_pip`,
  `_poly_perim`, `_signed_area`, `_poly_area`, `_dug_polyline`, `_point_along`, `_drain_bank`,
  `_miter_normals`, plus `Pt`/`Poly` aliases and the march constants (`DF`, `GAP`,
  `DRAIN_W_HEAD/TAIL`). Nothing here calls upward.
- **Layer 0, palette/parcel**: `PADDY_CELL_ACRES`, `paddy_grain`, the color constants
  (`_RICE_GREEN`, `RICE_GREENS`, `FLOODED`, `RIPE_GOLD`, `BUND`, `AZE`, `AZE_FT`, `BEAN_GREEN`),
  `aze_w`, `organic_parcel`, `DRY_CROPS`. Self-contained.
- **Layer 1, bank clearance**: `BANK_MARGIN`, `polyline_cum`, `drain_bank_clearance`,
  `supply_bank_clearance`, `hem_to_bank`, `hem_on_paddy`, `_TOE_MIN_THICKNESS`,
  `round_channel_joints`. Uses only layer-0 geometry (`_seg_x`, `_pip`).
- **Layer 2, builders**: `build_comb` -> {`_carve`, `_fill_wedges`, `_dry_fields`, `_bund_beans`,
  layers 0-1}; `_carve` -> layers 0-1; `_dry_fields` -> `_miter_normals`; `build_polder` /
  `build_terraces` / `build_ribbon` -> {`organic_parcel`, `hem_to_bank`, `round_channel_joints`,
  `_poly_area`}.

**Decision** - six submodules plus the derived `__init__.py`:

| module | contents | est. lines |
|---|---|---|
| `frame.py` | layer-0 frame math + march constants + `Pt`/`Poly` | ~300 |
| `palette.py` | layer-0 palette/parcel | ~230 |
| `banks.py` | layer-1 bank clearance | ~215 |
| `comb.py` | `build_comb` (+ extracted stages) + `_fill_wedges` | ~740 |
| `carve.py` | `_carve` (+ extracted stages) + `_dry_fields` + `_bund_beans` | ~660 |
| `polder.py` | `build_polder` (+ stages) + `build_terraces` + `build_ribbon` | ~740 |

Import direction: `comb -> carve -> banks -> frame`; `comb/polder -> palette`; no cycles by
construction (the split follows the measured graph). Every file lands well under the clause-13
~1,000-line bar even after stage extraction adds signatures. `comb`+`carve` are split (rather
than one "comb engine" file) because together they would be ~1,290 lines - over the bar.

**Alternatives considered**: (a) one `builders.py` for all four builders - rejected, ~1,700
lines; (b) keeping `_carve` inside `comb.py` for locality - rejected on the line count; the
`comb.py` module docstring will point at `carve.py` as its other half.

## R2: Re-export surface - reuse of the 027 findings

Feature 027's mypy probes (research.md R1-R3 there) established, on this exact toolchain
(mypy 2.3.0, Python 3.14, `strict = true`): star imports in a package `__init__` ARE explicit
exports under `no_implicit_reexport`; plain single-name imports are NOT; the `from X import name
as name` aliased idiom is. ruff needs `F401`+`F403` per-file-ignores on the `__init__` (the
stars are the mechanism), exactly as `check_village/__init__.py` already has.

**Consumer-name census** (grep over the skill tree at HEAD, all `from waterfields import` +
`wf.<attr>` accesses):

- Public, via `from waterfields import`: `AZE`, `BEAN_GREEN`, `BANK_MARGIN`,
  `PADDY_CELL_ACRES`, `aze_w`, `build_comb`, `build_polder`, `build_ribbon`, `build_terraces`,
  `drain_bank_clearance`, `hem_on_paddy`, `paddy_grain`, `polyline_cum`,
  `supply_bank_clearance` (consumers: 16 pool gens, `hamletgen.py`, `settlement/fields.py`,
  `settlement/houses.py`, `check_village/segments_03` + `segments_08`, `test_villages.py`).
- Underscore, needing the aliased explicit block: `_RICE_GREEN` (`settlement/fields.py:525`),
  `_Frame` + `_miter_normals` (`test_hamletgen.py`, via `import waterfields as wf` attribute
  access).

**Decision**: `__init__.py` = module docstring + `from .<module> import *` for the six
submodules + an aliased block for the three consumed underscore names. No `__all__` (027 R1:
it is a second roster). A guard test (`test_waterfields_surface.py`, modeled on
`test_check_village_surface.py`) pins every censused name AND re-runs the census mechanically
(grep the tree, assert each found name resolves) - so a consumer added by a concurrent session
fails loudly rather than silently. The census is re-run at implement time before the block is
written (027 R4's concurrency lesson: two pushes landed during this feature's own specify
phase).

Constant identity is automatic - re-export binds the same objects; the guard test asserts
`waterfields.AZE is waterfields.palette.AZE` style identity for the consumed constants.

## R3: Verification oracle - throwaway-tree byte-identity, not committed artifacts

The hand-authored pool FROZE on 2026-08-16 (migration-plan.md "The accepted trade"): legacy
gens never re-run, and **the engine has been free to drift since** - so the committed `.json`
manifests of the 13 legacy waterfields consumers are NOT a valid baseline (a pre-split re-run
today could already differ from what is committed, through no fault of this feature).

**Decision** - capture the baseline ourselves, out of tree:

1. **Pre-split**: copy the diagram skill dir at HEAD to the scratchpad, run EVERY
   waterfields-consuming gen there directly (`python3 <gen>` - bypassing regen.py's frozen
   skip, which guards the real pool, not a scratch copy), and save the produced `.json`
   manifests + `.svg` as `baseline/`.
2. **Post-split** (and after EACH mega-function extraction pass): same run in the working
   clone copied to a second scratch dir; `diff -r` the manifests byte-for-byte.
3. The real pool in the clone is never regenerated for legacy maps; scripted maps are
   additionally covered by the normal gate (`test_villages.py` regenerates them via gencache
   and runs the full check battery - checks are never cached).

`gencache` compat: `compute_key` hashes recorded dep FILES per path; recorded entries name
`waterfields.py`, which will no longer exist. A missing/unparsable dep degrades to a
conservative whole-state mismatch -> cache MISS -> regeneration. Safe by construction (a miss
can never serve stale output); the first post-split gate run repopulates the cache with the
package's files. `poolmaps.classify` greps for the settlement/hamletgen engine imports only -
no `waterfields` reference - so map classification is untouched.

## R4: Toolchain config deltas

- **mypy** (`pyproject.toml` `files`): `"waterfields.py"` -> `"waterfields"` (the package dir).
  The module is already fully `--strict` (the 005-feature ratchet retired); the split keeps
  every annotation, so strictness carries over file-by-file.
- **ruff**: add `"waterfields/__init__.py" = ["F401", "F403"]` to per-file-ignores with the
  same why-comment as check_village's entry.
- **coverage**: `waterfields` is NOT in `[tool.coverage.run] source` today and STAYS out.
  Recorded decision, not an oversight: pre-split the module was unmeasured (its exercise
  comes via `hamletgen`/`settlement` paths and the gate's map regeneration); adding it to the
  measured set is a coverage-expansion feature with its own ratchet questions (the frozen
  legacy maps are what exercised `build_terraces`/`build_ribbon`), out of scope here. FR-010's
  "no coverage regression" is satisfied vacuously and the measured modules keep their 100%.
- **lint's duplicate-defs check** is per-module (same name defined twice in ONE file), so the
  split cannot trip it; extracted stage names must still be unique within their module.

## R5: Mega-function decomposition method (and the clause-12 supersession)

**Prior disposition being superseded**: 024 research R9 recorded `build_comb`/`build_polder`/
`_carve` as clause-12-legitimate deep-but-cohesive builders, NOT to be split; 025 R11 deferred
`waterfields.py` itself as "a future feature." This feature IS that future feature, requested
explicitly by the GM (2026-08-16, naming the three mega-functions as the engineering
motivation). The supersession is deliberate and GM-authorized, recorded here.

**Method** (the same discipline as the mypy-strict migration, which held byte-identical map
output across ~2,470-error annotation passes):

1. Move-only first: split the monolith into the six modules with ZERO logic edits (functions
   move verbatim, comments and docstrings travel intact per FR-009). Verify byte-identity +
   full gate. Commit.
2. Then decompose ONE mega-function at a time into named sequential stage functions, passing
   state explicitly (parameters in, tuple/small-dict out - no shared mutable module state).
   Extraction is mechanical: code order, RNG draw order (`R: random.Random` is threaded as a
   parameter), and float-op order are preserved exactly, so output stays byte-identical.
   Verify byte-identity after EACH function's decomposition. Commit per function.
3. Target ~150 lines/function; a genuinely atomic stage may overshoot modestly with an inline
   note (the spec's stated tolerance).

**Rationale**: interleaving the move with the decomposition makes a byte-diff failure
un-bisectable; the per-pass oracle localizes any drift to one extraction.

## R6: Documentation surface

- New `waterfields/CLAUDE.md` in the check_village style ("look here when" table), indexed
  from the diagram skill's `CLAUDE.md` (which already references `waterfields.py` by name in
  its LIVE-engine line - update the path there).
- Historical references to `waterfields.py` in old `specs/NNN` artifacts are point-in-time
  records - NOT updated (same policy as every prior split; 024/025 left old specs verbatim).
- Prose references of the form `waterfields._bund_beans` in check messages remain valid (the
  importable path is unchanged) and are left alone.

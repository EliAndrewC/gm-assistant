# Implementation Plan: Near-Ring Farmland Density (towns and provincial cities)

**Branch**: `main` (session-clone workflow; spec dir `013-near-ring-farmland`) | **Date**: 2026-07-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/013-near-ring-farmland/spec.md`

## Summary

Town and city `/diagram` maps read sparse: the settlement, a few hand-authored `build_comb` paddy fans ringed by farmsteads, and bare/scrub ground filling the rest of the frame. The feature makes the flat, waterable **near ring** read as packed cultivation and relocates scrub/fallow to the frame margins and non-arable ground - which the research shows is *more* faithful to the labor-limited setting model, not less (the fallow is moved to where the model puts it, not erased).

Technical approach (Mechanism C, per [research.md](./research.md) Part B): add one parametric, **channel-free** `Settlement` method that tiles dry-field + garden cropland over an auto-derived flat near-ring band (frame minus the inflated hill, wet toe/marsh, watercourses, and the urban halo), recorded into `M["dry_plots"]`/`s.dry_polys`; keep paddy strictly per-gen; gate intensity on a new `meta(near_ring_density=<tier>)` kwarg (dense default, dialable down); add a `near_ring_cultivated_fraction` coverage check (a restricted clone of `town_margins_clothed`) with a saved sparse negative regression fixture; redesign the motivating maps (Hirameki, Tango) and sweep the whole pool. Dry/garden cropland is the water-source escape hatch - it needs no channel, sluice, or drain - so no new hydrology is invented.

## Technical Context

**Language/Version**: Python 3.14 (diagram skill; `pyproject.toml` in `.claude/skills/diagram/`).

**Primary Dependencies**: the in-repo `/diagram` engine - `settlement.py` (the `Settlement` class + drawing methods), `waterfields.py` (`build_comb`, `_dry_fields`), `check_village.py` (the manifest-reading validator gate), rendered to SVG then rasterized via the generators' own resvg call.

**Storage**: per-map `.gen.py` sources + derived `.json` manifests (tracked) and `.svg`/`.png` renders (gitignored) under `pool/{towns,provincial-cities,...}/`; negative fixtures under `pool/regressions/`.

**Testing**: `pytest` + `pytest-cov` (100% line coverage on pure logic), plus the `check_village` validator gate run over every regenerated pool map (`make done`), plus the Principle XII closing gate (human review of the rendered PNGs).

**Target Platform**: the `/diagram` skill toolchain (CLI generators), not the webapp.

**Project Type**: content-generator engine change (shared engine code + per-map gens + validator checks). No UI, no webapp, no pool markdown content.

**Performance Goals**: single-map regen stays in the ~1-7s band; full-pool `make done` sweep stays near its current ~1 min. The near-ring tiler must not blow up node count (reuse the tiling density of `_dry_fields`/`veg_tract`).

**Constraints**: to-scale honesty (Mode B is 1 px = 1 ft town / 3 ft city; no size inflation); every existing validator check must stay green on every pool map; the change touches shared engine code, so the full-pool regeneration + gate sweep is MANDATORY at the end.

**Scale/Scope**: two scales in scope (`scale="town"`, `scale="city"`); four existing downstream gens (Hirameki, Hoshizora towns; Tango, Nagahara cities) plus every other pool map as a regression surface; village/hamlet explicitly out of scope and must stay behavior-unchanged.

## Constitution Check

*GATE: passed before Phase 0; re-checked after design (below).*

- **I. Accessibility-First Viewports**: N/A - no webapp/HTML UI surface. The artifact is a diagram PNG, reviewed under Principle XII's closing gate, not the browser-viewport workflow.
- **II. Bold, Intentional Design**: N/A - no new UI surface or typography.
- **III. Pool Data Conventions**: N/A - no new recurring markdown/YAML pool content. (Regression *fixtures* are `.json` manifests under `pool/regressions/`, which follow the established diagram-regression convention, not the markdown-pool convention.)
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks added or moved. The historical "why" is AI-authored doctrine (settlements.md / code comments), not GM SOURCE text.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: PASS - no task touches any `<!-- SOURCE: GM NOTES -->` block or `l7r.md`.
- **VI. Verify Before Reporting Done**: PASS - the plan commits to: `ruff check` + `ruff format --check` + `mypy --strict` + `pytest` + `--cov-fail-under=100` on the diagram package; the `check_village` gate green on the motivating map then on the FULL pool; and a spot-check of the recon's claims already done against the real files. Delegated work (if any) is artifact-verified before relay.
- **VII. De-Localized Generation by Default**: N/A - no pool content generated. (Maps are inherently specific artifacts; no clan/city lock-in question arises.)
- **VIII. Direct Voice Over Framing Distance**: N/A - no in-world prose.
- **IX. Setting Integration**: PASS - grounded in `budgets.md` ("Rice and arable-land math"), consistent with the labor-limited framing and the ~4%/~15% land-use numbers; contradicts no setting fact (research.md Element 2 keeps the fallow). No new named figures.
- **X. Python Discipline (NON-NEGOTIABLE)**: PASS (committed) - the new tiler method, the `meta` knob read, and the new check are production Python: `ruff`/`format`/`mypy --strict` clean; **red-green TDD** (the new `near_ring_cultivated_fraction` check ships test-first, with its sparse negative fixture as the failing case before the motivating map is densified); `pytest --cov-fail-under=100` on the pure-logic diagram package; no swallowed exceptions; no `print`; behavior-named, parametrized tests; the intensity is a `meta()` kwarg (configuration, not a hardcoded magic constant), and the density threshold constant carries a record-the-why comment.
- **XI. Japanese Authenticity (NON-NEGOTIABLE)**: N/A - no kanji/romaji surfaced (crop labels are English; no new place/relic names).
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: PASS - this feature changes what the generator asserts about the world, so BOTH bookends are committed:
  - **Opening gate (done)**: [research.md](./research.md) Part A states, for each of the five changed elements, the historical reality (China-first: site selection, von Thünen intensity gradient, the labor-limited fallow's distribution, the polycultural quilt, topography), whether the design matches (it does), and what determines each element in reality. It records the three REJECTED designs (delete-the-scrub, more-wet-paddy, one-global-density) so a future pass does not reinvent them, and discloses the **calibrated-liberty** choice on the *degree* of density (dense default within a plausible middling-to-saturated range, with the range itself exposed as the knob).
  - **Closing gate (committed, in tasks)**: the final phase re-examines the RENDERED PNGs of Hirameki and Tango (and spot-checks Hoshizora/Nagahara and a dialed-down map) and confirms each Element 1-5 still holds in the picture - near ring reads cultivated, scrub only at margins/hill/wet-toe, quilt not monoculture, no paddy on slopes, dialed-down map visibly thinner. This is explicitly separate from the `check_village` gate (which proves internal consistency, never historical truth). The record-the-why note goes into `settlements.md` beside the rule and beside the threshold constant in code.

**Result: PASS.** No violations; no Complexity Tracking entries required. One doctrinal revision (`settlements.md:195` narrowed for the near ring) is flagged in research.md Part B and to the GM - it is a conscious doctrine edit, not a constitution violation.

## Project Structure

### Documentation (this feature)

```text
specs/013-near-ring-farmland/
├── spec.md              # done (/speckit-specify)
├── plan.md              # this file
├── research.md          # done - Principle XII opening gate + mechanism decision
├── data-model.md        # this phase - entities: the knob, the near-ring band, cover sets, contracts
├── quickstart.md        # this phase - how to iterate + the closing-gate ritual
└── tasks.md             # next (/speckit-tasks)
```

(No `contracts/` directory: this is an internal engine change with no external API, CLI schema, or wire contract. The "contracts" here are the `meta` knob signature, the new method signature, and the check's pass condition - captured in `data-model.md`.)

### Source Code (the touch-points)

```text
.claude/skills/diagram/
├── settlement.py        # NEW: s.near_ring_cropland(...) method (near comb_base_fill ~:1336);
│                        #   meta(near_ring_density=...) read (~:736); the not-hill/keep-out derivation
├── waterfields.py       # MAYBE: lift _dry_fields (~:990) tiling into a channel-free, bbox-driven variant
│                        #   the new method can call (or the method inlines an equivalent tiler)
├── check_village.py     # NEW: near_ring_cultivated_fraction check (clone of town_margins_clothed ~:5412);
│                        #   dry-plot hill keep-out gap noted by recon may need closing
├── settlements.md       # doctrine: the near-ring-density rule + Historical grounding (Part A why);
│                        #   revise the :195 "representative sample" line for the near ring
├── test_settlement.py   # tests for the new method (pure-logic geometry)
├── test_checks.py       # test for the new check (red-green: fires on sparse, passes on dense)
├── pool/regressions/    # NEW: near_ring_cultivated_fraction_fires_on_sparse_<map>.json negative fixture
├── pool/towns/hirameki.gen.py          # redesign: drop near-ring commons polys, call the fill
├── pool/provincial-cities/tango.gen.py # redesign: same outside the wall
├── pool/towns/hoshizora.gen.py         # verify/adjust (second town)
└── pool/provincial-cities/nagahara.gen.py # verify/adjust (second city)
```

**Structure Decision**: single self-contained change inside the `/diagram` skill directory; no cross-package or webapp impact. Work happens in the session clone; the full-pool render + gate sweep runs via `make done` before the stop-work ritual.

## Design details (feeds /speckit-tasks)

### The near-ring band (derived, no new topo primitive)

The flat, waterable near-ring region is derived as the framed view MINUS: the inflated hill `in_ellipse(x, y, M["hill"], 1.45)`, the wet toe/marsh and watercourse `block_polys`, the moat/streams/channels, the wall interior (for a walled map, the fill is OUTSIDE the wall), and the 30-ft urban-clearance halo (`_urban_keepouts`) around every structure. "Near ring" is bounded by the frame itself at the scales we draw (town ~0.5 mi, city ~1.5 mi across), optionally clamped to a radius from the settlement centroid - a plan-time detail resolved in data-model.md. This is the same complement the existing coverage checks already sample, so no new elevation model is introduced.

### The fill method (channel-free dry/garden tiler)

`s.near_ring_cropland(density=<resolved tier>, ...)` tiles ridge-cultivated dry-field rectangles (the `_dry_fields`/`veg_tract` idiom: furrowed hatake, `DRY_CROPS` variety honoring the "~1 in 6" mix) and garden-grain plots over the derived band, skipping every keep-out, recording each plot into `M["dry_plots"]` + `s.dry_polys` (so the existing `structures_clear_of_dry_plots` / `groves_clear_of_dry_plots` protect them and the coverage checks count them). Optional farmstead ringing of the new fill reuses `ring()`/`try_place`. It draws NO channels and taps NO water - dry cropland is exempt from `fields_show_water_source` and the moat/paddy-density checks.

### The knob (per-map `meta` kwarg)

`meta(near_ring_density=<tier>)`, read via `meta.get("near_ring_density", <dense default>)`. Tiers span the calibrated-liberty range (research.md): dense (well-sited default) to thin (dry/marginal). Exact tier names/values and whether it is an enum or a float are a data-model decision. The default must reproduce the intended packed look; declaring nothing yields dense.

### The check (restricted coverage clone)

`near_ring_cultivated_fraction`: clone the `town_margins_clothed` 25px grid-sampler but (a) restrict the sampled cells to the flat near-ring band above, and (b) count only *cultivated* cover (paddy `fields` + `dry_plots` + `gardens`), NOT scrub/pasture/structure. Require cultivated-fraction >= a threshold keyed to the resolved `near_ring_density` tier (high threshold at dense; the dialed-down tier lowers the requirement so a thin ring passes and, ideally, a dense ring on a thin-declared map does not masquerade). Ships with a saved sparse negative fixture proving it fires on today's sparse maps. Scoped to town + city; village/hamlet untouched.

### Population reconciliation (town scale only)

Added near-ring **dry fields and gardens** house no one - they do not touch population. Added **farmsteads** do, at town scale (they count toward the depicted farmer cohort). If the redesign adds farmhouses at town scale, re-reconcile the town's declared `meta(population=...)` and re-verify `town_caste_count`/`households_consistent`/`town_farmers_plurality` stay in band (the recon confirms plurality is only helped). City scale is free (farmhouses do not count toward the city figure).

## Phasing (for /speckit-tasks to expand)

1. **Doctrine + why** (settlements.md): write the near-ring-density rule and its Historical grounding (Part A), and revise the `:195` representative-sample line for the near ring. (Docs-only; no gate.)
2. **Check-first (red)**: add `near_ring_cultivated_fraction` and its test; save the sparse negative fixture from a current (undensified) manifest; watch it fire on the sparse map.
3. **Engine (green)**: implement `s.near_ring_cropland(...)` + the `meta` knob + the band derivation + any dry-plot hill keep-out gap; unit-test the geometry to 100% coverage.
4. **Motivating maps**: redesign Hirameki (town) then Tango (city) to call the fill and drop near-ring commons; iterate single-map regen + gate until each reads packed and green; re-reconcile town population.
5. **Tunability proof**: add/adjust one dialed-down map (or a knob-down variant) proving the thin ring passes and reads visibly thinner.
6. **Full-pool sweep (MANDATORY)**: `make done` - regenerate every pool map and run the whole gate; fix any downstream map the shared-engine change disturbed (Hoshizora, Nagahara, villages/hamlets must stay behavior-unchanged).
7. **Principle XII closing gate**: review the rendered PNGs against Elements 1-5; record the outcome in the maps' review logs.
8. **Stop-work ritual**: commit; `sync-with-main.sh done` (push + render-sync).

## Complexity Tracking

No constitution violations; no entries required.

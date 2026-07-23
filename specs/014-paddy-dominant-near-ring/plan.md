# Implementation Plan: Paddy-Dominant Near-Ring Farmland

**Branch**: `main` (session-clone workflow; spec dir `014-paddy-dominant-near-ring`) | **Date**: 2026-07-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/014-paddy-dominant-near-ring/spec.md`

## Summary

Feature 013 packed the near ring but filled it with dryland grain (dry cropland needs no plumbed water) - historically backwards for a wet-rice county seat, whose flat waterable near ring is paddy-dominant. This feature corrects the *composition*: near-ring wet paddy becomes the dominant land use, dry grain is demoted to the drier/higher margins, and vegetable/market gardens take a tight band by the settlement. 013's packed-density win and the `near_ring_density` knob are preserved.

Technical approach (per [research.md](./research.md) Part B): add `Settlement.near_ring_paddy(bbox, ...)` - a channel-free flooded-basin filler (reusing `paddy_field`'s tile primitives) that places paddy only where it can be *legitimately watered* (abutting a stream within ~18px, in the pond's 1.0-1.10x ring, or running off-edge) and skips ground with no reachable water; enlarge/add the existing hand-authored combs per map where needed; demote `near_ring_cropland` to an outer-margin grain pass + a near-town garden band; and add a `near_ring_paddy_dominant` check (paddy cells > dry-grain cells in the near ring, tiered) with a frozen dry-dominant negative fixture. Where a map genuinely lacks near-ring water, the honest result is a lower tier, never fake paddy.

## Technical Context

**Language/Version**: Python 3.14 (diagram skill).

**Primary Dependencies**: the `/diagram` engine - `settlement.py` (`Settlement`, `paddy_field`/`_paddy_plots`/`_paddy_surface`, `near_ring_cropland`), `waterfields.py` (`build_comb`), `check_village.py` (validator gate), rendered SVG->PNG via the generators' resvg call.

**Storage**: per-map `.gen.py` + tracked `.json` manifests + gitignored `.svg`/`.png`; negative fixtures under `pool/regressions/`.

**Testing**: `pytest` + `pytest-cov` (100% on pure logic), the `check_village` gate over every regenerated map (`make done`), and the Principle XII closing gate (human review of the rendered PNGs, confirming paddy now dominates).

**Target Platform**: the `/diagram` CLI toolchain (not the webapp).

**Project Type**: content-generator engine change (shared engine + per-map gens + validator). No UI, no pool markdown content.

**Performance Goals**: single-map regen ~1-7s; full-pool `make done` ~1 min. The paddy filler must not blow up node count (reuse `_paddy_surface`'s density).

**Constraints**: to-scale honesty (1 px = 1 ft town / 3 ft city); every existing check stays green on every pool map; **no paddy without a legitimate water source** (FR-004); shared-engine change so the full-pool sweep is mandatory; villages/hamlets unchanged.

**Scale/Scope**: town + city scales; four downstream gens (Hirameki, Hoshizora, Tango, Nagahara) redone for composition; every other pool map a regression surface; village/hamlet out of scope.

## Constitution Check

*GATE: passed before Phase 0; re-checked after design (below).*

- **I. Accessibility-First Viewports**: N/A - no webapp/HTML UI; the artifact is a diagram PNG (reviewed under Principle XII).
- **II. Bold, Intentional Design**: N/A - no new UI surface.
- **III. Pool Data Conventions**: N/A - no new markdown/YAML pool content (regression fixtures are `.json`, the diagram-regression convention).
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks touched. The corrected "why" is AI-authored doctrine.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: PASS - no task touches any SOURCE block or `l7r.md`.
- **VI. Verify Before Reporting Done**: PASS - commits to `ruff` + `format --check` + `mypy --strict` + `pytest` + `--cov-fail-under=100`; the `check_village` gate green on the motivating map then the FULL pool; recon claims spot-checked against the real files; the Principle XII PNG review.
- **VII. De-Localized Generation by Default**: N/A - no pool content generated.
- **VIII. Direct Voice Over Framing Distance**: N/A - no in-world prose.
- **IX. Setting Integration**: PASS - grounded in `budgets.md` and consistent with the wet-rice / labor-limited framing; corrects (does not contradict) the setting. No new named figures.
- **X. Python Discipline (NON-NEGOTIABLE)**: PASS (committed) - the new filler method, the demoted-fill wiring, and the new check are production Python: `ruff`/`format`/`mypy --strict` clean; **red-green TDD** (the `near_ring_paddy_dominant` check ships test-first with its frozen dry-dominant negative fixture before the maps are recomposed); `pytest --cov-fail-under=100`; no swallowed exceptions; no `print`; behavior-named parametrized tests; tier/threshold as data with a record-the-why comment.
- **XI. Japanese Authenticity (NON-NEGOTIABLE)**: N/A - no kanji surfaced (crop labels English; no new names).
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: PASS - this changes what the generator asserts (the near ring is now paddy-dominant), so BOTH bookends are committed:
  - **Opening (done)**: [research.md](./research.md) Part A grounds the corrected finding (a wet-rice county seat's flat near ring is paddy-dominant; dry grain is secondary/marginal; gardens by the town), states the design matches it, names what determines it (water + micro-topography), corrects the mis-applied ~1/3 domain average, and **records the dry-grain-dominant reading as REJECTED and why** (Principle XII's "record the grounding that led to rejecting a design").
  - **Closing (committed, in tasks)**: the final phase re-examines the RENDERED PNGs of all four maps and confirms paddy now dominates the flat near ring, grain is on the margins, gardens are by the town, no paddy sits without water, and the thin map is paddy-led. Separate from the automated gate (`check_village` proves internal consistency, never historical truth - the 013 maps passed every check while depicting the wrong crop mix, the exact failure mode this bookend guards).

**Result: PASS.** No violations; no Complexity Tracking entries. This feature also *retires* a Principle XII slip in 013 (a plausible-but-wrong composition claim in a governing doc), which is itself the bookend working as intended.

## Project Structure

### Documentation (this feature)

```text
specs/014-paddy-dominant-near-ring/
├── spec.md          # done
├── plan.md          # this file
├── research.md      # done - Principle XII opening gate + mechanism decision
├── data-model.md    # this phase - the filler, the demoted fill, the dominance check, entities
├── quickstart.md    # this phase - iteration loop + the XII closing-gate review
└── tasks.md         # next (/speckit-tasks)
```

(No `contracts/` dir: internal engine change; the "contracts" are the new method signature, the reused `near_ring_cropland` call shape, and the check's pass condition - in `data-model.md`.)

### Source Code (touch-points)

```text
.claude/skills/diagram/
├── settlement.py        # NEW: Settlement.near_ring_paddy(bbox, ...) (near near_ring_cropland ~:4379),
│                        #   reusing paddy_field's _paddy_plots/_paddy_surface basin primitives
├── check_village.py     # NEW: near_ring_paddy_dominant (clone the near_ring_cultivated_fraction sampler ~:5660)
├── settlements.md        # correct the 013 composition claim; add the paddy-dominant "why" + the recorded rejection
├── test_settlement.py   # tests for near_ring_paddy (water-abutment gating, off-edge, keep-outs, 100% cov)
├── test_checks.py       # near_ring_paddy_dominant: fires on dry-dominant, passes on paddy-dominant (red-green)
├── pool/regressions/    # NEW: near_ring_paddy_dominant_fires_on_dry_dominant_<map>.json (frozen 013-style)
├── pool/towns/hirameki.gen.py          # recompose: near_ring_paddy + demoted near_ring_cropland (margin grain + garden band); maybe enlarge combs
├── pool/towns/hoshizora.gen.py         # thin, but paddy-led
├── pool/provincial-cities/tango.gen.py # extramural paddy-dominant (moat/wall/farmhouse constraints)
└── pool/provincial-cities/nagahara.gen.py
```

**Structure Decision**: single self-contained change inside the `/diagram` skill; no webapp impact. Work in the session clone; full-pool render + gate via `make done` before the stop-work ritual.

## Design details (feeds /speckit-tasks)

### `near_ring_paddy(bbox, density=None, *, seed, avoid=())`
Tiles flooded paddy basins over the flat near-ring ground in `bbox`, reusing `paddy_field`'s `_paddy_plots`/`_paddy_surface` look. Places a basin only where it is **legitimately watered**: an outline vertex within ~18px of an `M["streams"]` segment (without the stream crossing the basin - `streams_avoid_fields`), OR in the pond's 1.0-1.10x ring (outside the 1.0x core - `pond_clear_of_paddies`), OR the basin runs off the map edge (exempt). **Skips** any cell with no reachable water and every keep-out `near_ring_cropland` already handles (fields, structures+halo, roads, hill, wall-interior on a city, groves, block/dry polys). Records each basin as a `kind="paddy"` field (name/outline/bbox) with **no channels/ditches**. Town basins stay < 80000px bbox (or alternate orientation) for `common_fields_vary_orientation`; city basins run off-edge or get >=2 farmhouses (`city_outside_fields_have_farmhouses`). Deterministic own RNG (no ripple).

### Demoting `near_ring_cropland`
Call it in two reduced passes per map: (1) an **outer-margin grain pass** - bbox(es) on the drier/higher ground (near `M["hill"]` / frame margin), with the new paddy region added to `avoid`; (2) a **near-town garden band** - a tight bbox buffered off `M["wall"]` / the structure halo, `garden_frac` ~0.85 so it reads as gardens. Net effect: grain on the margins, gardens by the town, paddy on the flat floor.

### Comb enlargement (per-map supplement)
Where the flat floor's water is combs/moat (not filler-abuttable), grow the existing `build_comb` fans (`field_fall` / `canal_a_len` / `offtakes_a`) or add a fan, in the single-map gate loop, watching for re-exposed tessellation holes. Auto water-legal via `draw_comb_field`.

### `near_ring_paddy_dominant` (check)
Clone the `near_ring_cultivated_fraction` 25px band + `committed` mask. Tally **paddy cells** (inside any `kind=="paddy"` field outline) vs **dry-grain cells** (inside a `dry_plots` poly with `crop != "garden"`). Require **paddy > dry-grain** over the near-ring band, scaled per tier (dense: a clear margin; thin: paddy at least ties). Town + city only. Failure detail reports the paddy/dry cell counts and the fix. Frozen dry-dominant negative fixture proves teeth.

## Phasing (for /speckit-tasks)

1. **Doctrine correction** (settlements.md): fix the 013 composition claim; add the paddy-dominant rule + Historical grounding + the recorded rejection. Docs-only.
2. **Check-first (red)**: add `near_ring_paddy_dominant` + tests; freeze a current (dry-dominant) manifest as the negative fixture; watch it fire.
3. **Engine (green)**: implement `near_ring_paddy` (basin filler, water-abutment gating); factor `_paddy_plots`/`_paddy_surface` out of `paddy_field` if cleaner; unit-test to 100%.
4. **Motivating map** (Hirameki): recompose - `near_ring_paddy` on the flat floor, demoted `near_ring_cropland` (margin grain + garden band), enlarge combs if needed; iterate single-map regen + gate to paddy-dominant AND green.
5. **Remaining maps**: Tango, Nagahara (cities - moat/wall/farmhouse constraints), Hoshizora (thin but paddy-led).
6. **Full-pool sweep (MANDATORY)**: `make done`; villages/hamlets unchanged; fix any downstream disturbance.
7. **Principle XII closing gate**: review all four PNGs - paddy dominates, grain on margins, gardens by town, no waterless paddy, thin map paddy-led.
8. **Stop-work ritual**: commit; `sync-with-main.sh done`.

## Complexity Tracking

No constitution violations; no entries required.

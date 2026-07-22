# Data Model / Contracts: Paddy-Dominant Near-Ring Farmland

**Feature**: 014-paddy-dominant-near-ring | **Date**: 2026-07-22

Internal engine change, no external API. The contracts are the new filler method, the reused/demoted `near_ring_cropland` calls, and the dominance check. Names/values are the plan's recommendation; implementation may refine within the stated intent.

## Entity 1 - `near_ring_paddy(bbox, density=None, *, seed=0, avoid=())` (filler method on `Settlement`)

- **Behavior**: tiles flooded **paddy basins** over the flat near-ring ground in `bbox`, reusing `paddy_field`'s `_paddy_plots` (contour/fall split into bunded basins) + `_paddy_surface` (wet mottled sheet + faint sheen) look. Density read from `density` or `meta(near_ring_density=...)` (dense/medium/thin), same tiering as `near_ring_cropland`.
- **Water legality (the core gate - a basin is placed ONLY if watered)**: a candidate basin is kept iff at least one of:
  - an outline vertex is within **~18px of an `M["streams"]` segment** AND the stream does **not** cross the basin interior (`streams_avoid_fields`); or
  - a vertex sits in the **pond's 1.0-1.10x ring** (outside the 1.0x core, `pond_clear_of_paddies`); or
  - the basin **runs off the map edge** (`runs_off_edge` exemption).
  Any candidate with no reachable water is **skipped** (that ground is left for the demoted dry/garden fill or scrub). No channels are drawn (keeps basins out of `field_ditches_reach_source_and_sink` / channel-anchor / `channels_flow_downhill` / `paddy_fan_has_floor`).
- **Keep-outs** (reuse `near_ring_cropland`'s `_blocked`): existing fields, structures + urban halo, roads/streets, hill, wall-interior (city), groves, block/dry polys, `avoid`.
- **Records**: each basin as `M["fields"].append({"name","kind":"paddy","outline","bbox"})` (the `paddy_field` shape - no vis_bbox/plots/channels), plus its footprint into `self.field_polys` so the demoted dry fill and later passes avoid it.
- **Scale constraints**: town basins keep bbox area < 80000px OR alternate wide/tall (`common_fields_vary_orientation`); city basins run off-edge OR get >=2 farmhouses within 165px (`city_outside_fields_have_farmhouses`).
- **Determinism**: own seeded RNG; perturbs no other pack.

## Entity 2 - Demoted `near_ring_cropland` (two reduced passes, per map)

- **Margin grain pass**: `near_ring_cropland(<outer/higher bbox>, density, garden_frac≈0.12, avoid=(<paddy region>, ...))` - dry hatake on the drier/higher ground near `M["hill"]` / the frame margin, kept off the flat valley floor (paddy region in `avoid`).
- **Near-town garden band**: `near_ring_cropland(<tight bbox by the wall/edge>, density, garden_frac≈0.85)` - reads as gardens (greens) hugging the settlement.
- Unchanged method; only the call sites (bbox + garden_frac + avoid) change. Both passes still record `dry_plots` with `crop` (grain crops vs `"garden"`), which the dominance check reads.

## Entity 3 - The near-ring band + cover tallies (derived, shared by the check)

- **Band + `committed` mask**: identical to `near_ring_cultivated_fraction` (`check_village.py`): 25px grid over the framed view minus hill (1.45x) / pond / wall-interior / structure halo / corridors / skip polys.
- **Paddy cells**: eligible cells inside any `M["fields"]` outline with `kind=="paddy"`.
- **Dry-grain cells**: eligible cells inside any `M["dry_plots"]` poly with `crop != "garden"` (gardens are excluded - they are the legitimate near-town dry use, not the thing being demoted).

## Entity 4 - `near_ring_paddy_dominant` (validator check)

- **Kind**: `check("near_ring_paddy_dominant", ok, detail)` in `check_village.py`, town + city only.
- **Pass condition**: **paddy cells > dry-grain cells** over the near-ring band, scaled per `near_ring_density` tier - dense demands a clear paddy margin (e.g. paddy >= 1.2x dry-grain), thin only requires paddy to at least tie (paddy >= dry-grain), so a dialed-down map is paddy-led but not forced to a dense paddy quantity. Exact ratios calibrated against the recomposed maps to have teeth vs the frozen 013 dry-dominant baseline.
- **Interaction with 013's check**: `near_ring_cultivated_fraction` (013) stays and still enforces the packed floor (FR-005); this new check adds the composition constraint on top. A map must pass BOTH.
- **Failure detail**: reports paddy vs dry-grain cell counts, the tier, and the fix (add near-ring paddy where water reaches / thin the margin grain / lower the tier if the near ring genuinely lacks water).
- **Negative fixture (FR-009)**: `pool/regressions/near_ring_paddy_dominant_fires_on_dry_dominant_hirameki.json` - a frozen pre-fix (013-style, dry-grain-dominant) manifest, proving the check fires.

## Entity 5 - Doctrine record (settlements.md)

- **Correct** the 013 "Near-ring farmland density" text that asserts dry-field-carried densification -> paddy-dominant, dry grain marginal, gardens by the town.
- **Add** the Historical grounding for the correction (research.md Part A) AND the explicit recorded rejection of the dry-grain-dominant reading (so it is never reinvented), beside the `near_ring_paddy_dominant` check and the tier ratios.

## Flow

Gen declares `meta(near_ring_density=...)` -> calls `near_ring_paddy(flat-floor bbox)` (basins where water reaches) -> enlarges combs if the floor needs more watered paddy -> calls `near_ring_cropland` twice (margin grain + garden band, paddy in `avoid`) -> manifest carries paddy fields + margin `dry_plots` + garden `dry_plots` -> `near_ring_paddy_dominant` + `near_ring_cultivated_fraction` + every existing check validate it -> render -> Principle XII closing-gate PNG review (paddy dominates).

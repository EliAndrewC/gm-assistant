# Phase 1 Data Model: Village Visual Variation Knobs

The "data" here is the knob catalogue and the village-spec shape - the structures the generator reads and the validator checks. No persisted database; these are in-memory structures in `settlement.py` and fields in the per-map `meta` + manifest.

## Entity: Knob

A named degree of variation in a village's layout.

| Field | Meaning |
|-------|---------|
| `name` | stable identifier (e.g. `cluster_position`, `lane_skeleton`) |
| `value_space` | the discrete set (or bounded range) of allowed values |
| `typing_rule` | predicate over the village's stated geography + already-resolved knobs; excludes values that are historically invalid in that context |
| `default` | the value used when neither pinned nor rolled (for maps that opt out of rolling a given knob) |
| `roll(seed, context)` | deterministic independent draw from `value_space` filtered by `typing_rule`, keyed off the seed + the knob name (so different knobs draw independently, and the same spec+seed is reproducible) |

**Resolution order per knob** (FR-001, FR-007, FR-014): pinned value (if the spec sets it) → else `roll(seed, context)` (if the map opts into rolling) → else `default`. A pinned value that fails its `typing_rule` is rejected/warned (FR-004), never silently drawn.

### Phase-1 knob catalogue (Family A)

| Knob | Value space | Typing rule (excludes when...) |
|------|-------------|-------------------------------|
| `cluster_position` | `high_margin` \| `flank` \| `mid_margin` \| `valley_mouth` \| `valley_head` \| `on_rise` | must stay field-adjacent, off the flood toe, and above the drain line |
| `cluster_shape` | `round` \| `elongated` \| `crescent` \| `split` (2 sub-hamlets) | `split` needs room for two readable hamlets; `elongated`/`crescent` orient along the field margin |
| `lane_skeleton` | `spine` \| `T` \| `Y` \| `cross` \| `waterside` | `waterside` needs a stream/canal adjacent to the cluster |
| `water_source_position` | pond: `corner{NW,NE,SW,SE}` \| `mid_margin` \| `chain`; stream: `edge{N,E,S,W}` | source must sit uphill of the field intake (gravity feed); `chain` implies a smaller/drier catchment |
| `plot_texture` | size `small_irregular` \| `medium` \| `large_block` \| `strip`; regularity `organic` \| `grid` | `grid` regularity implies a planned/surveyed field, not an organically-grown old one |
| `grain_drift` | bounded angular drift off the fall-line (degrees) | none (always allowed; a gentle real-valley drift) |
| `focal_feature_set` | subset of the Focal-feature catalogue (below) | per-feature typing (see Focal feature); the mandatory floor (primary shrine, graveyard, wells, windbreak) is always present and not part of this roll |

Headman-house and primary-shrine positions are **derived** (not knobs): a function of `cluster_position` + `lane_skeleton` (headman at the lane's focal point; shrine at an edge/gateway per the existing shrine-placement rules).

## Entity: Village spec

The per-map declaration - today the `pool/<name>.gen.py` plus its `s.meta(...)`. Extended, not replaced.

| Field | Meaning |
|-------|---------|
| `seed` | the RNG seed; drives every unpinned knob's roll deterministically |
| geographic facts | `scale`, `down_deg` (water direction), water-source `kind` (pond/stream), optional `region`/`terrain` type |
| pinned knobs | any subset of the knob catalogue, set explicitly |
| rolled knobs | the rest - resolved by `roll(seed, context)` |

A minimal spec (FR-006) supplies only `seed` + `scale` + `down_deg` + water-source `kind` (+ optional region); the generator rolls the rest and emits a complete, gate-passing map. Existing hand-authored maps remain expressible by pinning knobs (FR: knob machinery is a superset of hand-authoring).

## Entity: Focal feature

An optional, historically-attested village element drawn from a catalogue (research.md D4), placed by the existing overlap/placement invariants.

| Feature | Placement typing |
|---------|-----------------|
| `crescent_pond` (半月塘) | in front of / field-facing the cluster; distinct from the irrigation pond |
| `ancestral_hall` (祠堂) | single-lineage villages only; at the head-of-lane focal point |
| `water_mouth_complex` (水口) | at the low drain exit; grove + bridge + small hall |
| `mill` | on a watercourse with fall (drain/stream), not still pond water |
| `market` | at a lane/track junction or the water-mouth |
| `secondary_shrine` | away from the primary shrine, on dry ground |

Each recorded in the manifest with its footprint so the validator's overlap/set-back checks apply unchanged, and so the twin-detector can read the focal-feature set as a distinctiveness axis.

## Entity: Archetype (later phases)

A whole terrain/settlement type that swaps the field-geometry generator and settlement-placement logic and adds archetype-specific validator rules.

| Field | Meaning |
|-------|---------|
| `field_archetype` | `comb_fan` (default) \| `terraces` \| `polder` \| `ribbon` \| `mulberry_fishpond` |
| `settlement_form` | `nucleated` (default) \| `linear` \| `water_town` \| `dispersed` |
| `land_use_overlay` | `rice_mono` (default) \| `mulberry_fishpond` \| `rape` \| `lotus` \| `tea_fringe` |
| validator rules | archetype-specific checks registered so the per-map gate includes them |
| grounding | recorded in `settlements.md` (China-first) |

Each archetype value is region-typed so a roll respects the stated geography (e.g. `mulberry_fishpond` and `water_town` = delta; `terraces`/`tea_fringe` = hill). Delivered incrementally, one validated end-to-end before the next.

## Entity: Twin-detector report (validation output)

Not persisted; produced by the pool-level check.

| Field | Meaning |
|-------|---------|
| pair | the two village names compared |
| shared `down_deg` | true when they share water direction (the scope condition) |
| axis diffs | which of the ~7 SC-001 axes differ |
| verdict | PASS (differ on >= threshold axes) / TWINNED (too similar) |

Threshold target: differ on at least 4 of ~7 axes. The exact axis discretization + threshold are tuned during implementation against the re-varied pool and recorded in `settlements.md`.

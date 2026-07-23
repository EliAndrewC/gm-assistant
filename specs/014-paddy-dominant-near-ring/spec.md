# Feature Specification: Paddy-Dominant Near-Ring Farmland

**Feature Branch**: `014-paddy-dominant-near-ring` (spec directory; work lands on `main` per the session-clone workflow)

**Created**: 2026-07-22

**Status**: Draft

**Input**: GM review of the feature-013 maps - "we had exactly the correct amount of rice paddies, but there would also be just tons and tons of dry crop fields everywhere? That is not what a wet-rice county seat looks like." This feature corrects the land-use *composition* of the near ring.

## Context and Research Findings

This supersedes exactly one decision in feature 013 ([`specs/013-near-ring-farmland/`](../013-near-ring-farmland/)). It does NOT re-derive 013's still-valid grounding - **site selection**, the **von Thünen intensity gradient**, the **tunable near_ring_density knob**, and the **frame math** all stand and are referenced from [013's research.md](../013-near-ring-farmland/research.md), not repeated here. What changes is the *mix* of what fills the packed near ring.

### What 013 got right, and the one thing it got wrong

013 densified the flat near ring of town/city maps so a well-sited settlement reads as embedded in packed farmland. That goal is correct and is preserved. But 013 delivered the densification **almost entirely as dryland grain fields** (barley/millet/soybean hatake), holding the wet-rice paddy fixed - because dry cropland is exempt from the water-source rule and was the cheap way to fill the frame without plumbing new irrigation. On the rendered Hirameki and Hoshizora maps this reads as a town ringed by dry grain fields, which is **not** what a wet-rice county seat looks like.

The error was not only in the code: 013's `research.md` (Element 3) and `FR-003` wrote the wrong composition into the governing document - *"the densification is carried substantially by dry-field plots"* - to justify the engineering shortcut. That is precisely the "confident, plausible sentence in a governing doc" that Constitution Principle XII warns about, and this feature records why it was wrong.

### The corrected historical finding (China-first; to be fully grounded in research.md)

A town sits in the fertile alluvial basin **because of the wet rice**. The flat, waterable valley floor immediately around a Song/Ming or Japanese county seat was **overwhelmingly paddy**. Dryland grain (barley/millet/soybean) was the **secondary** use, pushed onto the higher, drier, un-irrigable margins and terraced slopes - not blanketing the flat basin. The one dry land-use that genuinely belongs *right at the town* is **intensive vegetable / market gardens** (the von Thünen inner ring: night-soil-fed truck gardens feeding the urban market).

The number 013 leaned on cuts the other way. `budgets.md` says only ~1/3 of rice-*suitable* land is active wet paddy in any year - but that is a domain-wide average over 560 sq mi **including the hills and dry margins**. The near ring of a valley-bottom town is the *most* waterable, flattest ground on the whole domain, so its paddy share should be **higher** than the domain average, not lower. 013 inverted this: it made the near ring dry-grain-heavy (worse than even the domain average) when the same site-selection logic that justifies densifying at all says the near ring should be paddy-heavy.

### Rejected design (recorded per Principle XII so it is not reinvented)

- **Rejected: dry-grain-dominant near ring** (the 013 outcome). Historically backwards for a wet-rice basin: the flat waterable valley floor is paddy, not dryland grain. Dry grain belongs on the drier margins; market gardens belong near the town. The only reason 013 chose it was the engineering convenience that dry fields need no plumbed water - a convenience that does not justify an ahistorical picture.

### The crux the plan must confront

Wet paddy requires a **plumbed water source the validator checks** (`fields_show_water_source`: a channel ending inside the field, or the field abutting a stream/pond/moat). 013's dry-field fill needed none. So generating *more real paddy* near settlements is genuinely harder, and the plan must pick a tractable, in-grain mechanism from: enlarging/extending the existing hand-authored `build_comb` paddy fans; adding more combs tapping the existing streams/moat/pond; and/or a channel-free paddy filler that tiles paddy only where it can legitimately abut an existing water body. This spec states the WHAT (paddy-dominant near ring); the plan decides the HOW.

## User Scenarios and Testing *(mandatory)*

The "user" is the GM generating and browsing `/diagram` town/city maps.

### User Story 1 - A well-sited town's near ring reads paddy-dominant (Priority: P1)

The GM regenerates a well-sited town map. The flat near ring reads as **wet-rice paddy as the dominant land use** - paddy occupies the flat waterable ground - with dryland grain reduced to a secondary presence on the drier/higher margins and a tight band of vegetable/market gardens near the settlement. The overall "packed" look from 013 is preserved; the mix is corrected.

**Why this priority**: This is the whole point and the GM's correction. It delivers value on its own.

**Independent Test**: Regenerate the motivating town map (Hirameki); by eye the near ring reads as paddy with grain/garden accents (not a sea of dry grain); the new paddy-dominance check passes; every existing check still passes.

**Acceptance Scenarios**:

1. **Given** a well-sited town map, **When** it is generated, **Then** wet-rice paddy is the **largest single cultivated land use** in the flat near ring (paddy area exceeds dryland-grain area).
2. **Given** the same map, **When** its near ring is inspected, **Then** dryland grain sits on the drier/higher margins (not blanketing the flat basin) and vegetable/market gardens sit in a tight band near the settlement.
3. **Given** the same map, **When** every field is checked, **Then** each on-map paddy still shows a legitimate water source (no paddy without a channel/abutting water body) and all currently-passing checks still pass.

---

### User Story 2 - A well-sited provincial city reads the same way (Priority: P2)

The extramural near ring of a walled/unwalled city reads paddy-dominant outside the wall, respecting the moat/wall/gates and the existing in-wall agricultural district.

**Why this priority**: Shares the engine with towns; more constrained (moat, tight view), so it follows the town case.

**Independent Test**: Regenerate Tango and Nagahara; the extramural ring reads paddy-dominant; walls/moat/bridges/estates unchanged; paddy-dominance + all checks pass.

**Acceptance Scenarios**:

1. **Given** a provincial-city map, **When** generated, **Then** paddy is the dominant cultivated use in the flat extramural near ring, and no field/farmstead crosses the wall or moat.
2. **Given** a walled city, **When** near-ring paddy is added, **Then** every added paddy shows a legitimate water source (e.g. tapping the moat or an existing stream/comb) and every gate approach still bridges the moat.

---

### User Story 3 - Tunability and the dial-down are preserved (Priority: P3)

The `near_ring_density` knob (dense/medium/thin) still works, and a dialed-down map (Hoshizora, thin) still reads visibly thinner - now as a *paddy-light* near ring (a grazing/relay locale with modest paddy) rather than a dry-grain one.

**Why this priority**: The knob and dial-down are inherited from 013 and must not regress; lower priority because the default (dense, paddy-dominant) carries the value.

**Independent Test**: Regenerate Hoshizora (thin); its near ring is visibly thinner than the dense maps and its modest cultivation is paddy-led, not dry-grain-led; it passes at the thin tier.

**Acceptance Scenarios**:

1. **Given** a thin-tier map, **When** generated, **Then** its near ring is visibly thinner than the dense default and what cultivation it has is paddy-led (paddy at least ties the dominant use), passing the thin tier.
2. **Given** any tier, **When** generated, **Then** the paddy-dominance requirement scales with the tier (a thin map is not forced to a dense paddy count, but is still not dry-grain-dominant).

---

### Edge Cases

- **A settlement with little water in-frame**: if there is no stream/pond/moat/comb the new paddy can legitimately draw from, near-ring paddy cannot be conjured (no paddy without water). The generator must not create paddy with no visible water source; in that case the honest result is a *thinner*/dryer near ring (a lower tier), not fake paddy.
- **Topography**: paddy stays off hill slopes (existing `no_field_on_hill` / `dry_plots_off_hill`); the drier/higher margins are exactly where the demoted dry grain and any slope crops go.
- **Water plausibility**: added paddy must not create implausible hydrology (channels violating the downhill / anchored-at-both-ends / no-build-corridor rules, or paddy sitting on open water).
- **Preserving 013's win**: the near ring must stay *packed* (013's cultivated-fraction floor still met); this feature changes the mix, it must not thin the ring back out.
- **Gardens vs grain near the town**: the tight near-settlement band should read as gardens (greens), not grain; grain should not dominate the immediate edge.
- **Regression fixtures**: the current 013-style dry-grain-heavy manifests must be frozen as negative fixtures proving the new paddy-dominance check fires on them.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: On town and provincial-city maps, wet-rice **paddy MUST be the dominant cultivated land use in the flat near ring** - paddy area MUST exceed dryland-grain area there (scaled to the map's `near_ring_density` tier).
- **FR-002**: Dryland grain MUST be **demoted to a secondary role on the drier/higher margins** of the near ring, not blanketing the flat waterable ground.
- **FR-003**: Intensive **vegetable / market gardens MUST occupy a tight band near the settlement** (walls/edge), reading as gardens (greens), so the immediate near-town ground is not dominated by grain.
- **FR-004**: Every on-map paddy - including all newly added near-ring paddy - MUST show a **legitimate water source** (a channel ending inside it, or it abutting a stream/pond/moat/existing comb), satisfying `fields_show_water_source`; the generator MUST NOT create paddy with no visible water source.
- **FR-005**: The **packed near-ring look from 013 MUST be preserved** - the near ring stays densely cultivated (013's cultivated-fraction floor is still met per tier); this feature changes the *composition*, not the overall density.
- **FR-006**: The `near_ring_density` **knob (dense/medium/thin) and its dial-down MUST be preserved**; the paddy-dominance requirement scales with the tier (a thin map is paddy-led but sparser, never dry-grain-dominant).
- **FR-007**: New paddy MUST respect topography and existing exclusions: no paddy on hill slopes; nothing crossing the wall/moat; no paddy on roads/streets/structures/existing fields; channels obey the downhill / anchored / no-build-corridor rules.
- **FR-008**: A validator check MUST enforce **near-ring paddy dominance** (paddy is the largest cultivated use, scaled by tier), so a dry-grain-dominant near ring FAILS. Every currently-passing check MUST still pass.
- **FR-009**: A **negative regression fixture** MUST be saved (a frozen 013-style dry-grain-heavy manifest) proving the new paddy-dominance check fires on it.
- **FR-010**: The corrected historical grounding, AND the explicit record that the dry-grain-dominant reading was **rejected and why**, MUST be written where the rule lives (`settlements.md` "Historical grounding" + comments by the check), per the CLAUDE.md record-the-why rule and Principle XII.
- **FR-011**: 013's now-wrong composition claim MUST be **corrected in place** in `settlements.md` (and 013's research left as the historical record, annotated as superseded), so the doctrine no longer asserts dry-field-carried densification.
- **FR-012**: Village and hamlet scales are **out of scope** and MUST be left behavior-unchanged.

### Key Entities

- **Near-ring paddy**: wet-rice fields occupying the flat, waterable near-ring ground, each with a legitimate water source; the new dominant use.
- **Demoted dry grain**: the 013 dry-field fill, reduced and relocated to the drier/higher margins of the near ring.
- **Near-town gardens**: intensive vegetable/market-garden plots in a tight band by the settlement edge/walls.
- **Paddy-dominance measure**: the per-tier requirement that near-ring paddy area is the largest cultivated use.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On Hirameki (town), the flat near ring reads as **paddy-dominant** - paddy is the largest cultivated use by area - with dry grain on the margins and gardens near the town; the GM reads it as "a rice-basin town," not "a town in dry grain fields."
- **SC-002**: On Tango and Nagahara (cities), the extramural near ring reads paddy-dominant outside the wall, with walls/moat/bridges/estates unchanged.
- **SC-003**: Every added paddy shows a legitimate water source (zero `fields_show_water_source` violations), and the full validator gate passes for every pool map after the engine change.
- **SC-004**: Hoshizora (thin) still reads visibly thinner than the dense maps, but its modest cultivation is paddy-led, not dry-grain-led, and it passes at the thin tier.
- **SC-005**: The 013 "packed" density is preserved (the cultivated-fraction floor still met); the near ring is not thinned back out by the recomposition.
- **SC-006**: Village and hamlet maps are unchanged.
- **SC-007**: The corrected "why" (and the recorded rejection of the dry-grain-dominant reading) is discoverable in `settlements.md` and by the check, without re-reading this spec.

## Assumptions

- The motivating artifacts are the four 013 maps (Hirameki, Tango, Nagahara dense; Hoshizora thin); the fix redoes their near-ring composition.
- "Paddy-dominant" is defined by **area within the flat near ring** (paddy > dry grain), scaled per tier; the exact ratio/threshold and whether the check measures area or plot-count is a plan/data-model decision, calibrated against the redesigned maps to have teeth against the 013 dry-heavy baseline.
- The mechanism for generating more paddy (enlarge existing combs vs add combs vs a water-abutting paddy filler) is a **plan-phase decision**; this spec only requires that the paddy be real (plumbed) and dominant.
- 013's `near_ring_cropland` (the dry/garden tiler) is reused in a reduced, margin-and-gardens role rather than removed; the exact split is a plan decision.
- This is a shared-engine change (`settlement.py`, `check_village.py`), so the mandatory full-pool regeneration + gate sweep applies, and villages/hamlets must be verified unchanged.
- Work is done in the session clone on `main`; the spec-kit git feature-branch hook is intentionally not used (same as 013).

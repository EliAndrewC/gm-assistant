# Tasks: Ubame County Town (border charcoal district)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

Ordered by dependency. `[P]` = may run in parallel with the task above it.
Every task names the verification that must pass before it is checked off (Principle VI).

## Phase A - engine vocabulary

- [x] **T001** `border_line()` in `settlement.py`: a dashed jurisdictional polyline plus label,
  recorded as `M["borders"]` with `poly` + `label` and **no footprint**. Classify `borders` in
  `_OVERLAP_EXEMPT` and `_LABEL_EXEMPT` with the reason ("a line of law is not a physical object;
  the magistracy's east wall stands on it by design").
  *Verify*: `every_feature_classified_for_overlap` and `every_solid_feature_classified_for_labels`
  pass on a synthetic manifest carrying a border under a manor wall.

- [x] **T002** `charcoal_yard()` in `settlement.py`: two roofed stacking sheds (34x18 ft each) with
  baled stock, an open **cooling apron** (30x20 ft) set apart from them, a weighing floor (16x14 ft),
  and cart standing; whole ground ~88x58 ft, `rot` laying the **road side to local -y**. Records
  `M["charcoal_yards"]` via `_trade_record` plus `sheds` and `apron`.
  *Verify*: sizes are TRUE feet (no legibility inflation); the drawn ground renders legibly at
  1 ft/px.

- [x] **T003** [P] `refining_forge()` in `settlement.py`: an open-sided **two-hearth** shed
  (44x26 ft, three walls and an open working front), a charcoal store (24x16 ft), quench trough,
  slag heap, and stacked bar iron; whole ground ~74x48 ft, open front to local +y. Records
  `M["refining_forges"]` with `hearths`.
  *Verify*: as T002.

- [x] **T004** Register `charcoal_yards` and `refining_forges` in `_OVERLAP_STRUCTS` and give each a
  caption group in `_LABEL_GROUP`.
  *Verify*: `test_every_solid_struct_is_gated_off_every_hazard` names both new keys and passes -
  i.e. each is refused every hazard by membership alone.

## Phase B - the checks (red before green)

- [x] **T005** `settlement_has_charcoal_yard` (gated on `meta.charcoal_district`) and
  `charcoal_yard_keeps_fire_gap` (**30 real ft** of every solid structure, converted through
  `meta.ftpx`). Record the reasoning at the check.
  *Verify*: fires on a fixture with a yard 20 ft off a house; spares every good placement.

- [x] **T006** [P] `settlement_has_refining_forge` (gated on `meta.iron_district`),
  `refining_forge_stands_off_dwellings` (**60 real ft**), and `refining_forge_downwind` (the forge
  must lie downwind of the dwelling centroid, keyed off `meta.windward`).
  *Verify*: each fires on its own broken fixture.

- [x] **T007** Freeze one negative fixture per new check into `pool/regressions/` with a
  `_regression` block naming the checks it must trip, and add a firing test per check to
  `test_checks.py` using the existing fixture builders.
  *Verify*: `pytest test_regressions.py test_checks.py -n auto --no-cov` green; each check observed
  RED on its fixture **before** any artifact is corrected.

## Phase C - the map

- [x] **T008** Write `pool/towns/ubame.gen.py`, copied from `hoshizora.gen.py`. Declarations per
  [data-model.md](./data-model.md). Layout: magistracy NE with `gate_dir="south"` and its east wall
  on the border; unlabeled trunk road east-to-west; ubame-oak stand on the NE high ground; water-first
  combs on the lower SW with one running off the frame; urban core along the road; burakumin quarter,
  tanning yard, execution ground + boundary marker SW (downstream); charcoal yard on the east trade
  approach; refining forge SE (downwind); two monasteries (Benten, Jurojin) with the theater stage
  adjacent to and opening toward one; windbreak on the NW margin.
  Follow the draw order settled in [plan.md](./plan.md); use `s.open_seat(...)` rather than guessing
  coordinates when a pocket needs one more feature.
  *Verify*: `DIAGRAM_SKIP_RENDER=1 python3 pool/towns/ubame.gen.py && python3 check_village.py
  pool/towns/ubame.json` reports ALL CHECKS PASSED, with **no opt-out knob added to make a check
  pass** (FR-009).

- [x] **T009** Run the check-ran diagnostic across the pool for every new check, and for the
  wall-scoped checks Ubame legitimately skips.
  *Verify*: each new check reports a non-zero count on the maps that carry the feature; the
  wall-scoped skips are confirmed deliberate, not accidental.

## Phase D - the record

- [x] **T010** Record the "why" where the rule lives: the trade-works rules and both separation
  figures in `settlements/urban-features.md`, the full research record in
  `research/urban-features.md`, Ubame in the worked-examples list in `settlements/towns.md`, and the
  reference entry in `SKILL.md`.
  *Verify*: each new magic number (30 ft, 60 ft, two hearths, the cooling apron) is discoverable
  with its reasoning without reading code (SC-007).

- [x] **T011** [P] `pool/towns/ubame.notes.md` - the design record: knob settings, the layout
  decisions and why, the disclosed divergence, and the review log.

## Phase E - verification

- [x] **T012** Cheap linters, then the whole affected test files, then `make done` **once**,
  backgrounded and not polled.
  *Verify*: `ruff` + `mypy` clean; `make done` green including the whole-pool regeneration sweep and
  the 100% coverage floor; no existing map's verdict changed (SC-002, SC-003).

- [x] **T013** Read the rendered PNG back, batching every crop into one call, then get an
  independent `building-review` (or `size-audit`) pass, because the author is not a reliable
  reviewer of their own visual output.
  *Verify*: findings applied or explicitly overruled with a reason in the notes.
  **Done by the author's own render pass** (three defects found and fixed: the forge reading as a face,
  the windbreak drawn as a blob, the manor contradicting its Mode A envelope). The INDEPENDENT
  subagent pass was NOT run - this session is configured not to spawn agents unasked - so it remains
  open and is flagged to the GM rather than silently skipped.

- [x] **T014** **Principle XII closing bookend (NON-NEGOTIABLE)**: re-examine the RENDERED PNG - not
  the code, not the intent - against every Phase 0 finding in [research.md](./research.md), element
  by element, and confirm each still matches. `check_village` proves internal consistency, never
  historical truth.
  *Verify*: a written element-by-element confirmation appended to `research.md`.

- [ ] **T015** Stop-work ritual: commit in the clone, then `scripts/sync-with-main.sh done` from
  inside it (locked pull + push, then render-sync). Never force-push.

## Dependency notes

- T004 depends on T002 + T003 (the keys must exist to be registered).
- T005-T007 depend on T004 (the checks read `solid_structs`, which reads the registry).
- T008 depends on all of Phase A and B - the map is the integration test, not the first test.
- T012 must come after every code change; T013 and T014 read the artifact T012 proves.

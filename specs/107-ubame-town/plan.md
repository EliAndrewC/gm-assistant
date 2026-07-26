# Implementation Plan: Ubame County Town (border charcoal district)

**Branch**: `main` (session-clone workflow) | **Date**: 2026-07-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/107-ubame-town/spec.md`

## Summary

Add a third pool town - **Ubame**, the county seat of Ubame county, Moriguchi province, Daika domain
(Scorpion) - as an **unwalled town with no Imperial road**, the combination neither existing town
covers, so the town gate runs over fresh geometry. Ubame stands on the Fox/Scorpion border with the
magistracy at the northeast, its east wall on the line, the land falling northeast to southwest.

Three new engine capabilities carry the county's declared economy onto the sheet: a **charcoal yard**
(roofed stacking sheds, an open cooling apron, a weighing floor), a **refining forge** (open-sided
two-hearth ōkajiba, charcoal store, slag heap, stacked bar iron), and a drawn **clan border line**.
Each goes through the KEEP-CLEAR CONTRACT - new manifest key, `_OVERLAP_STRUCTS` (or
`_OVERLAP_EXEMPT` with a reason), a caption group in `_LABEL_GROUP` - so registry membership alone
gates it off every hazard, plus four new siting checks with negative fixtures.

## Technical Context

**Language/Version**: Python 3.14 (container pin)

**Primary Dependencies**: none new - `settlement.py` + `waterfields.py` + `check_village.py` in
`.claude/skills/diagram/`; `resvg` for rasterization; PIL for text measurement

**Storage**: files - `pool/towns/ubame.gen.py` (source), `ubame.json` (manifest, tracked),
`ubame.svg` / `ubame.png` (derived, gitignored); negative fixtures in `pool/regressions/*.json`

**Testing**: pytest + pytest-cov + pytest-xdist, run via `make done` (`ruff check`, `ruff format
--check`, `mypy`, `pytest -n auto`, `--cov-fail-under=100`)

**Target Platform**: the container's Linux CLI; output consumed as PNG by the GM

**Project Type**: generator library + validator (single package, no UI)

**Performance Goals**: single-map regen + gate under ~7 s; the whole-pool sweep stays near its
current ~80 s (any new check that scans globally must be `GridIndex`-pruned, never coarsened)

**Constraints**: every drawn footprint at TRUE size (1 px = 1 ft at town scale); the stroke
convention is the only sanctioned divergence and covers linework floors and location markers only;
100% line coverage over `check_village.py` and `settlement.py`; all 17 existing pool maps must
regenerate byte-identically except where a deliberate change says otherwise

**Scale/Scope**: 1 new pool map (~700 depicted residents, ~150 dwellings), 3 new glyph methods,
4 new checks, 2 new opt-in `meta()` knobs, 3 new manifest keys

## Constitution Check

*GATE: passed before Phase 0 research; re-checked after Phase 1 design.*

- **I. Accessibility-First Viewports** - **N/A**. No web UI. This feature's visual output is a PNG
  map read directly, not a page with viewports; the analogous verification is the render read plus
  the `building-review` / `size-audit` subagent passes, committed to under VI.
- **II. Bold, Intentional Design** - **N/A**. No new UI surface. The map's aesthetic is the
  established `/diagram` house style (parchment palette, Georgia serif, English-default labels),
  which this feature follows rather than restates.
- **III. Pool Data Conventions** - **PASS**. The artifact goes in `pool/towns/` per the skill's
  foldered-by-subject convention, as `ubame.gen.py` + `ubame.json` tracked and `.svg`/`.png`
  gitignored-and-regenerated. Negative fixtures go in `pool/regressions/` with a `_regression`
  block naming the checks they must trip. (The markdown-with-YAML frontmatter form in this gate is
  the *prose* pool convention - relics, names, dreams; `/diagram`'s pool is generator + manifest,
  which is the settled form for this skill.)
- **IV. One Canonical Home for GM Source** - **PASS**. No SOURCE blocks are added or moved. The
  canonical home for Ubame's setting facts stays `/host-l7r-repo/setting/l7r.md`; this feature reads
  it and cites the section by name, and copies nothing.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)** - **PASS**. No task touches anything inside
  SOURCE markers, and no task writes to `l7r.md` at all.
- **VI. Verify Before Reporting Done** - **PASS**. Per-task verification is named in `tasks.md`.
  The standing bar: `ruff check` + `ruff format --check` + `mypy` before the gate; the whole affected
  test files before the gate; `make done` once, backgrounded, not polled; each new check verified to
  fire RED on its fixture before the artifact is corrected; the rendered PNG read back; and an
  independent `building-review` / `size-audit` pass, because the author is not a reliable reviewer of
  their own visual output.
- **VII. De-Localized Generation by Default** - **DEFERRED (GM-scoped)**. This map is deliberately
  and explicitly localized: the GM asked for *this* county town, tied to a named magistrate and a
  named border. That is exactly the "explicit GM scoping" the principle allows for. The *engine
  features* it ships obey the principle in full - `charcoal_yard`, `refining_forge` and the border
  line are generic vocabulary with no Ubame-specific constants, usable by any fuel district, iron
  district or frontier settlement. See Complexity Tracking.
- **VIII. Direct Voice Over Framing Distance** - **PASS**. All in-world prose (labels, notes,
  docstrings) states facts directly. No "tradition says," "the temple holds that," "skeptics
  report."
- **IX. Setting Integration** - **PASS**. Grounded in `l7r.md` ("The Kurogi and the dynasty province
  of Moriguchi"), the existing Mode A `ubame-magistracy.notes.md`, `setting/budgets.md` for the
  caste counts, and the campaign map for the terrain. No new named figures are invented, so there is
  no campaign-names collision to check - the only person named is the existing Bayushi no Daika
  Koharu.
- **X. Python Discipline (NON-NEGOTIABLE)** - **PASS**. `ruff check` + `ruff format --check` +
  `mypy` + `pytest --cov-fail-under=100`. Red-green is mandatory and specific here: each new check
  must be observed FIRING on a deliberately-broken manifest before the map is fixed, per the skill's
  standing "every found defect becomes an automated check" rule. No new dependencies, so no lockfile
  change. No `print` in library paths (the gens' summary line is a CLI path and matches existing
  convention).
- **XI. Japanese Authenticity** - **PASS**. Every kanji surfacing in notes or docstrings passes the
  kanji-romaji-meaning triangle; the table is in [research.md §5](./research.md). No kanji is drawn
  on the sheet - the skill's labeling rule keeps commonplace nouns in English, so the captions read
  "charcoal yard" and "refining forge."
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)** - **PASS on the opening bookend**;
  closing bookend scheduled as the final task. The opening bookend is [research.md](./research.md):
  China-first findings for the fining hearth, the charcoal trade and the border, each with an
  explicit does-it-match verdict, each naming what determines it in reality, one **disclosed
  divergence** (Ubame uses the Japanese two-site pattern, not the Chinese adjacent-hearth
  arrangement, because dispersed fuel forces two sites), one **design change forced by the research**
  (the open cooling apron, from charcoal's self-heating), and five recorded **rejections**. The
  closing bookend re-examines the rendered PNG against those findings before "done."

## Project Structure

### Documentation (this feature)

```text
specs/107-ubame-town/
├── plan.md              # this file
├── research.md          # Phase 0 - the Principle XII opening bookend
├── data-model.md        # Phase 1 - manifest keys, meta knobs, check contracts
├── quickstart.md        # Phase 1 - how to regenerate and gate the map
├── checklists/
│   └── requirements.md  # spec quality checklist (passed)
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code

```text
.claude/skills/diagram/
├── settlement.py                      # + charcoal_yard(), refining_forge(), border_line()
├── check_village.py                   # + 4 checks, 3 registry entries, 2 meta knobs
├── settlements/
│   ├── urban-features.md              # + the trade-works rules (the "why" lives here)
│   └── towns.md                       # + Ubame in the worked-examples list
├── research/
│   └── urban-features.md              # + the full research record (mirrors research.md)
├── pool/
│   ├── towns/ubame.gen.py             # NEW - the map spec
│   ├── towns/ubame.json               # NEW - the manifest (tracked)
│   └── regressions/*.json             # NEW - one negative fixture per new check
├── test_checks.py                     # + a firing test per new check
├── test_settlement.py                 # + branch coverage for the new glyphs
└── test_villages.py                   # picks up ubame.gen.py by glob
```

**Structure Decision**: no new package or module. All three features are additions to the existing
shared Mode B library and its validator, which is what the skill's architecture requires - "when you
need a NEW shared capability, add it to the library, not to one village." The map itself is a thin
spec in `pool/towns/`, copied from `hoshizora.gen.py` (the unwalled-town exemplar).

## Phase 1 design decisions

**Footprints, in TRUE feet** (no legibility inflation; sized against the pool's existing trade works
- lumber yard 90x60, dye yard 80x52, brewery vat hall 96x36, oil press barn 54x30):

| feature | element | true size |
|---|---|---|
| charcoal yard | two roofed stacking sheds | 34 x 18 ft each |
| | open cooling apron (set apart) | 30 x 20 ft |
| | weighing floor | 16 x 14 ft |
| | whole ground | ~88 x 58 ft |
| refining forge | open-sided two-hearth shed | 44 x 26 ft |
| | charcoal store | 24 x 16 ft |
| | whole ground incl. slag heap and bar stacks | ~74 x 48 ft |

**Separation ladder** (derived in [research.md §2](./research.md), placed against the project's
existing figures rather than invented):

| rule | figure | new? |
|---|---|---|
| `farrier_keeps_fire_gap` | ~6 ft | existing |
| `charcoal_yard_keeps_fire_gap` | **30 ft** | NEW |
| `refining_forge_stands_off_dwellings` | **60 ft** | NEW |
| crematory / tanning yard from dwellings | 120 ft | existing |

**Two opt-in `meta()` knobs**, following the `granary=True` precedent (opt-in, not default-on, so an
ordinary county seat is unaffected):

- `meta(charcoal_district=True)` -> `settlement_has_charcoal_yard`
- `meta(iron_district=True)` -> `settlement_has_refining_forge`

Opt-in knobs carry a known hazard - "a check that never RUNS looks exactly like a check that
passes." Mitigation: the presence checks are declaration-gated by design (only a fuel/iron county
should have one), but the **siting** checks (`charcoal_yard_keeps_fire_gap`,
`refining_forge_stands_off_dwellings`, `refining_forge_downwind`) are gated on the FEATURE's
presence, not on the knob - so a yard drawn without the knob is still fully validated, and the
`grep -c "<check_name>"` diagnostic is run across the pool as an explicit task.

**Nuisance axes deliberately separated.** Smoke goes **downwind** (SE, from the default NW winter
monsoon); filth goes **downstream** (SW, from `down_deg=135`). Ubame is the first pool map where
those two point to different corners, which is what makes it a real test that the rules are
independent rather than accidentally agreeing.

**Draw order** (per the skill's DRAW ORDER map - the sequence is settled here, on paper, rather than
discovered one gate failure at a time): border line and terrain -> water and comb fields -> the
road -> the manor -> urban packs -> the two trade works (AFTER the packs, so their standoffs are
measured against the final layout) -> `farmsteads()` -> wells -> justice works -> hinterland ->
`village_grove()` -> crop -> title.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **VII. De-Localized Generation** - the map is locked to a named county, province, domain and magistrate | The GM asked for this specific county town, to sit beside the existing Mode A magistracy sheet for the same place and to be tested against the campaign map. Pool settlement maps are inherently localized artifacts (Hoshizora, Hirameki, Tango, Nagahara all are); the principle's target is reusable *generated content*, and it explicitly permits explicit GM scoping. | A generic "border charcoal town" would not agree with the existing `ubame-magistracy.svg`, which already fixes the compound's orientation and the border's position - two artifacts of the same place that contradicted each other would be worse than localization. The reusable half is preserved instead: all three new engine features carry zero Ubame-specific constants. |

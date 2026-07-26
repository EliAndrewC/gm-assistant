# Implementation Plan: Minami - the Fox Clan provincial city

**Branch**: `016-minami-provincial-city` | **Date**: 2026-07-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/016-minami-provincial-city/spec.md`

## Summary

Add the pool's third provincial city - **Minami**, seat of the Fox Clan's southern province: walled, on the east bank of the Hayakawa, population ~2,600, `peaceful` defense tier, no Imperial road, with an **eight-precinct temple program** (the seven Fortunes of Good Luck plus a larger Inari) in place of the standard two great complexes.

The technical approach is deliberately narrow: **parameterize what is currently hard-coded, and change nothing else.** The temple program becomes declared knobs on `CityProgram` whose defaults reproduce today's budget exactly; the multi-temple exception (already written in the doctrine but enforced by nothing) becomes a declaration plus a check; and the map itself is a new `pool/provincial-cities/minami.gen.py` built on the existing river-city vocabulary. Phase 0 research (see [research.md](research.md)) established that the eight-precinct form is **inside the attested historical band rather than a liberty** - the surprise of this feature - which is why the doctrine wording matters as much as the code.

## Technical Context

**Language/Version**: Python 3.14 (container pin)

**Primary Dependencies**: none new - `settlement.py`, `citybudget.py`, `waterfields.py`, `check_village.py`; resvg for the raster

**Storage**: files - `pool/provincial-cities/minami.{gen.py,json,svg,png}`; only `.gen.py` and `.json` are tracked

**Testing**: pytest with `-n auto`; `test_villages.py` (pool regeneration + gate), `test_checks.py` (negative fixtures), `test_citybudget.py` (budget back-prediction), `test_settlement.py`

**Target Platform**: the diagram skill's dev container

**Project Type**: single project - a generator library plus its validator, no UI

**Performance Goals**: Minami's own regen + gate stays in the ~1-7s single-map band; the full `make done` sweep stays near its ~80s baseline (a third city adds one map to the sweep - watch that no new check is a global scan; index rather than coarsen if it is)

**Constraints**: Tango and Nagahara must reprice and regenerate **byte-identically**; 100% coverage on `check_village.py`, `settlement.py`, `citybudget.py`

**Scale/Scope**: one new map (~600 recorded features), 3 new budget knobs, 1 new gate check, 6 doc files touched

## Constitution Check

*GATE: passed before Phase 0 research; re-checked after Phase 1 design.*

- **I. Accessibility-First Viewports**: **N/A** - no UI surface. The artifact is a rendered PNG read with the Read tool, not a web page; the viewport matrix does not apply.
- **II. Bold, Intentional Design**: **N/A** - no new UI surface. The map's visual language is the existing `/diagram` style library, unchanged.
- **III. Pool Data Conventions**: **PASS** - the artifact goes to `pool/provincial-cities/` per the established Mode B layout (`.gen.py` + `.json` tracked, `.svg`/`.png` gitignored and regenerated). This is settlement-map pool data, not the markdown-with-YAML content pool, so the frontmatter schema clause does not apply. **The city-baking prohibition is scoped away by GM instruction**: the GM explicitly commissioned a specific named city in a specific named province, exactly as for Tango and Nagahara.
- **IV. One Canonical Home for GM Source**: **N/A** - no SOURCE blocks added or moved. All setting facts are read from `l7r.md` and cited by section name, never copied.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: **PASS** - no task in this plan writes to `/host-l7r-repo/setting/l7r.md` or touches any SOURCE block. `l7r.md` is read-only input throughout.
- **VI. Verify Before Reporting Done**: **PASS** - every task lists its verification; the feature-level gate is `make done` plus a read of the rendered PNG plus the Principle XII closing bookend.
- **VII. De-Localized Generation by Default**: **PASS with GM scoping** - as III. The GM named the city, the province, the clan and the river.
- **VIII. Direct Voice Over Framing Distance**: **PASS** - the only in-world prose is map labels and the notes file. Labels state what a thing IS (`Temple of Inari`, `timber yard`), never "tradition says."
- **IX. Setting Integration**: **PASS** - `l7r.md` ("The Fox Clan", "Fox Lineages and Provinces", "Fox Temples", "The Fox Clan's economy", the clan population table) and `budgets.md` (provincial-city caste table) are the sources; Phase 0 recorded exactly what each supports. **Name-collision check is a task** (T02): the Nanke lineage and any named officeholder must be grepped against the campaign-names cache and the existing pool, per the Kazuma/Harima precedent.
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS** - ruff check + ruff format --check + mypy --strict + pytest at `--cov-fail-under=100`. The new check is written RED first against a synthetic broken manifest (T05) before the declaration exists to satisfy it. No new dependencies, so no lockfile change.
- **XI. Japanese Authenticity**: **PASS** - any kanji that surfaces (the city name 南 "south", the Nanke lineage 南家, temple names) must pass the kanji/romaji/meaning triangle. `Minami` 南 and `Nanke` 南家 are already in `l7r.md` / `place-names`, so the triangle is inherited rather than coined.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: **PASS** - this feature plainly changes what a generator asserts about the world, so both bookends are committed:
  - **Opening**: [research.md](research.md), six findings, each stating the historical reality, whether the design matches, and what determines the element in reality. Finding 4 records a change **rejected** on the research (scaling the graveyard ceiling with temple count). Finding 1 records the significant reversal: eight precincts sits inside the attested band, and our two-complex default is the liberty.
  - **Closing**: T14, the final task - re-examine the RENDERED PNG against all six findings before "done", separately from the automated gate.

**No Complexity Tracking entries** - no gate is DEFERRED.

## Design decisions settled at plan time

Recorded here so `tasks.md` implements rather than re-decides.

### D1 - The temple knobs

`CityProgram` gains three fields, all defaulted to today's hard-coded values so the shipped cities reprice unchanged:

- `temple_precincts: int = 2`
- `temple_precinct_px2: float = 16_250.0`
- `monk_houses_per_precinct: float = 2.5`

The `("temple precincts", 2, 16_250.0)` row moves out of the static `CIVIC_PROGRAM` tuple and is emitted from the knobs. The adept-monk line becomes `round(temple_precincts * monk_houses_per_precinct)` - 2 x 2.5 = 5, today's constant, preserved exactly. Minami sets `temple_precincts=8`, a per-precinct area below the 16,250 default, and `monk_houses_per_precinct` in the 5-9 band from research Finding 3.

**The Inari uplift is its own `extras` line**, not an inflated average (FR-004): a precinct that is "slightly larger" should be a visible number, and averaging hides it.

### D2 - The multi-temple justification

A new map-level declaration `meta(temple_exception=<reason>)` with a fixed vocabulary of four values - `"large"`, `"pious"`, `"changed_hands"`, `"fox_structure"` - and a new walled-city check that fires when `>= 3` major temples are drawn with no recognized value declared. Tango declares `"changed_hands"` (a meta line, not a map change); Nagahara is under the threshold and declares nothing.

**Why a fixed vocabulary rather than free text**: the doctrine already enumerates the recognized justifications, so an enum keeps the check honest and makes an unrecognized reason a failure rather than a silent pass. This is the "the declaration must EXIST" ratchet from the skill's `CLAUDE.md`, applied to a rule that has been written down but unenforced since it was authored.

### D3 - Precincts distribute by TRADE, not into a teramachi belt

Settled by research Finding 2: the Fox precincts are economic houses, so each sits where its business is rather than in one temple quarter. The Japanese rim-belt *teramachi* was the considered alternative and is deliberately not taken (it is a castle-town defensive arrangement, and Minami's temples are commercial institutions first). Consequence: some precincts will be lone temples in their quarter, correctly exempting them from `city_temple_neighborhood_has_shrines`, exactly as Tango's converted-estate Bishamon already is.

### D4 - What is deliberately NOT changed

- `city_graveyard_count` stays 2-4 (research Finding 4 - a rejected change, recorded).
- `CLAN_FORTUNES` gains no `fox` entry (spec Assumptions) - Minami declares `temple_fortunes` explicitly.
- `city_temples_dedicated` logic is untouched; it already supports the override.
- The `monk_house` glyph stays identical to a laborer house.

## Project Structure

### Documentation (this feature)

```text
specs/016-minami-provincial-city/
├── spec.md              # feature specification
├── plan.md              # this file
├── research.md          # Phase 0 - Principle XII opening bookend
└── tasks.md             # Phase 2 output
```

### Source Code

```text
.claude/skills/diagram/
├── citybudget.py                          # D1: temple knobs; adept-monk line derived
├── check_village.py                       # D2: the multi-temple justification check
├── settlement.py                          # only if a raft-landing glyph proves needed (research F5, deferred)
├── test_citybudget.py                     # default-equivalence + Minami program tests
├── test_checks.py                         # RED fixture for the new check
├── test_villages.py                       # picks up the new map automatically
├── settlements/religion-and-death.md      # FR-017 the Fox program + why the graveyard ceiling holds
├── settlements/cities/sizing.md           # FR-018 the temple knobs and their derivation
├── research/religion-and-death.md         # research.md findings 1-4 land here
├── research/urban-features.md             # research.md finding 5 lands here
├── research/SOURCES.md                    # 13 new source keys
├── SKILL.md                               # FR-019 Mode B example G
└── pool/
    ├── provincial-cities/minami.gen.py    # the map (tracked)
    ├── provincial-cities/minami.json      # the manifest (tracked)
    └── regressions/                       # negative fixture for the new check
```

**Structure Decision**: no new packages or directories. This feature parameterizes two existing modules, adds one check, and adds one map to an existing pool folder - the same shape as every prior city feature.

## Phases

**Phase 0 - research** (DONE): [research.md](research.md).

**Phase 1 - engine**: the budget knobs (D1) with default-equivalence proven FIRST, then the justification check (D2) written RED. Both are pure logic with unit tests; neither needs the map to exist.

**Phase 2 - the map**: build `minami.gen.py` against the derived wall, iterating on the ONE map per the skill's dev-loop doctrine (`DIAGRAM_SKIP_RENDER=1` + single-map gate, ~1-7s a cycle) rather than the ~80s pool sweep. Render order follows the standing city doctrine: river -> walls + moat -> roads -> ring road -> towers -> gates -> water works -> civic compounds -> dense packs -> farmsteads/wells/fire towers last.

**Phase 3 - docs and closing**: the doctrine and research files, `SKILL.md`, the notes file, then the full sweep ONCE, then the Principle XII closing bookend against the rendered PNG.

## Risks and how each is handled

| Risk | Handling |
|---|---|
| The temple-knob refactor silently shifts Tango/Nagahara's wall by a rounding hair | Default-equivalence test written BEFORE the refactor (T03); byte-identical manifest check in the sweep (SC-002) |
| ~40-50 monk houses drag a caste out of band | `city_caste_counts_in_band` is already in the gate; SC-007 makes it an explicit acceptance line rather than something noticed late |
| Eight precincts + eight torii rolls produce a 7-arch avenue that will not fit a modest precinct | The engine already shortens an avenue rather than standing an arch in a wall; verified per precinct on the rendered map |
| A new glyph (raft landing) is added late and lands on packed dwellings | KEEP-CLEAR CONTRACT: classify in `_OVERLAP_STRUCTS` + `_LABEL_GROUP` at the moment it is written, and reserve its ground up front per the render-order doctrine |
| The new check is a global scan and slows the gate | Profile if the sweep moves off ~80s; INDEX, never coarsen (the standing rule) |

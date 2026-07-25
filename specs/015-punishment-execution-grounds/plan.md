# Implementation Plan: Punishment Spots and Execution Grounds

**Branch**: `main` (session-clone workflow) | **Date**: 2026-07-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/015-punishment-execution-grounds/spec.md`

## Summary

Add three related Mode B settlement features - an in-town **punishment spot**, an out-of-town **execution ground**, and the **boundary marker** that separates them - to the `/diagram` engine, gate each siting rule with an automated check plus a negative regression fixture, record the historical grounding beside the rules, and carry both features onto every town, walled-town, and provincial-city map in the pool.

The design follows [research.md](research.md): China supplies the *jurisdiction* (a county seat executes, because confirmed sentences come back down to where the crime happened), Japan supplies the *siting* (kegare pushes the ground past the built edge), and the volume math (~1 execution per county per 5-10 years) sets the county ground's character as a disused patch rather than an installation.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: none new. The feature is additive within the existing `/diagram` engine (`settlement.py`, `check_village.py`); rasterizing stays on the installed `resvg`.

**Storage**: SVG + JSON manifest per map under `.claude/skills/diagram/pool/`; negative fixtures under `pool/regressions/`.

**Testing**: `pytest -n auto` via `make done` in `.claude/skills/diagram/` - `test_settlement.py` (engine units), `test_checks.py` (check units, using the fixture builders), `test_villages.py` (regenerate + gate every pool map), `test_regressions.py` (replay the negative corpus).

**Target Platform**: CLI generators run in the session clone; output is SVG/PNG the GM reads locally.

**Project Type**: Content generator (single package, no service or UI surface).

**Performance Goals**: the full pool sweep (`make done`) stays near its current ~80s. New checks must not add a global O(n*m) scan - if a new check is slow, index it with the existing `GridIndex` rather than coarsening it (per the skill's dev-loop doc).

**Constraints**: to-scale drawing at the tier's grain (1 ft/px hamlet/town, 2 ft/px village, 3 ft/px city). No size inflation: sub-glyph features become explicit **location markers** with `vw`/`vh` recorded, never silently enlarged footprints.

**Scale/Scope**: 3 new engine methods, ~9 new checks, ~9 new regression fixtures, 4 pool maps updated (2 towns, 2 provincial cities), 2 documentation files plus one `l7r.md` section.

## Constitution Check

*GATE: evaluated before Phase 0, re-evaluated after Phase 1 design (below).*

- **I. Accessibility-First Viewports**: **N/A** - no UI surface. The artifacts are SVG/PNG map renders the GM opens locally, not webapp pages.
- **II. Bold, Intentional Design**: **N/A** - no new UI surface. The features use the existing map style library and palette conventions.
- **III. Pool Data Conventions**: **PASS** - no new markdown-with-frontmatter pool content. The map pool follows its own established convention (`pool/<tier>/<name>.gen.py` + `.json` + `.svg`/`.png`), and the negative fixtures follow the established `pool/regressions/<check_name>_fires_on_<case>.json` naming.
- **IV. One Canonical Home for GM Source**: **PASS** - no SOURCE block is created or moved. New setting text is written to `l7r.md` (the canonical home for setting material) and the skill docs reference it rather than duplicating it.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: **PASS** - the `l7r.md` addition is a **new** sub-section appended after the Ministry of Justice section. No existing GM prose is edited, reworded, or reflowed, and no `<!-- SOURCE: GM NOTES -->` block anywhere in the repo is touched. The TOC gets exactly one new line inserted; every other TOC line is left byte-identical, verified by `git diff`.
- **VI. Verify Before Reporting Done**: **PASS** - every task lists its verification. Engine work: cheap linters (`ruff format`, `ruff check`, `mypy`), then the whole touched test files, then `make done` once, backgrounded and not polled. Map work: regenerate the single motivating map and gate it, then the full pool sweep once at the end. Plus the Principle XII artifact review below.
- **VII. De-Localized Generation by Default**: **PASS** - the features are generic settlement vocabulary. The pool maps they land on are already-existing named places; no new campaign-tied figures or households are invented.
- **VIII. Direct Voice Over Framing Distance**: **PASS** - the `l7r.md` prose states what the institution does, not what anyone "holds" or "believes."
- **IX. Setting Integration**: **PASS** - the design is built from canon, not around it: burakumin as executioners for all non-samurai (`castes.md`), the county jail and the domain-only "ceremonial executions" budget lines (`budgets.md`), the tier ladder (`median-domain.md`), bandit counts (`professions.md`). No new named figures, so no collision with the campaign-names cache.
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS** - committed to `ruff check` + `ruff format --check` + `mypy --strict` + `pytest` + `--cov-fail-under=100`. Red-green TDD: each new check gets its `test_checks.py` test **and its negative regression fixture** before the check is wired into a pool map, so the fixture demonstrably fires. No new dependencies, so no lockfile change. No swallowed exceptions, no `print` in engine code, behavior-named tests, parametrized where the variants are near-identical.
- **XI. Japanese Authenticity (NON-NEGOTIABLE)**: **PASS** - every Japanese term that surfaces passes the kanji/romaji/meaning triangle and is a real historical term, not a construction: 枷 *jia* (cangue, Chinese), 晒し *sarashi* (exposure), 獄門 *gokumon* (prison gate - the beheading-plus-display sentence), 道祖神 *dosojin* (road ancestor deity), 刑場 *keijou* (execution ground), 仕置場 *shiokiba* (punishment place). Map labels stay in plain English per the SKILL.md labeling rule (`latrine`, `well`, ...); the Japanese terms appear only in documentation prose.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: **PASS, both bookends committed.**
  - **Opening gate**: [research.md](research.md) states, per element, what the historical reality was (China-first with Japan corroborating), whether the design matches, and the governing variable. It changed the design twice before implementation - the punishment spot lost its beating function to the yamen courtyard, and the second notice board was dropped - and both rejections are recorded there rather than left to be rediscovered.
  - **Closing gate**: the final task re-examines the **rendered PNGs** (via `crop_map.py`, batched in one call) and confirms per map that the ground reads as outside the settlement, as bare waste ground rather than a field, as *disused* at county tier, as on the road past the boundary stone, and as visibly a different place from the burial/cremation cluster. This is a separate step from `make done`, which proves internal consistency and never historical truth.

**Post-Phase-1 re-evaluation**: unchanged. The design added no new dependency, no new UI, no SOURCE-block movement, and no pool-content convention. The one deliberate departure from literal reality (the 150 ft separation floor, where the true separation was much larger) is disclosed in research.md and will be repeated in a comment beside the check, as Principle XII's calibrated-liberty clause and the record-the-why rule both require.

## Project Structure

### Documentation (this feature)

```text
specs/015-punishment-execution-grounds/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0 - the Principle XII opening gate
├── data-model.md        # Phase 1 - manifest records and their relationships
├── contracts/
│   └── engine-api.md    # Phase 1 - generator methods + check names
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source code

```text
.claude/skills/diagram/
├── settlement.py                  # + punishment_spot(), execution_ground(), boundary_marker()
│                                  # + 3 manifest registries
├── check_village.py               # + ~9 checks; + the 3 new kinds in the struct-overlap list
├── settlements.md                 # + vocabulary entries; + historical-grounding entries
├── test_settlement.py             # + engine unit tests
├── test_checks.py                 # + check unit tests (via the fixture builders)
└── pool/
    ├── towns/hoshizora.gen.py     # unwalled county seat  - both features
    ├── towns/hirameki.gen.py      # walled county seat    - both features
    ├── provincial-cities/tango.gen.py     # walled city   - both features
    ├── provincial-cities/nagahara.gen.py  # walled city   - both features
    └── regressions/               # + one negative fixture per new check
```

Plus, outside this repo: `/host-l7r-repo/setting/l7r.md` - one new sub-section and one new TOC line.

**Structure Decision**: additive within the existing single-package diagram skill. No new module: the three methods belong on `Settlement` beside their nearest analogs (`cremation_ground`, `ossuary`, `kosatsuba`), and the checks belong in `gate()` beside the existing funerary and notice-board checks, so the shared helpers (`_struct_rect`, `wall_runs`, `GridIndex`) apply without plumbing.

## Design decisions settled before implementation

The skill's dev-loop doc requires ordering and placement to be settled on paper first, because discovering it one gate failure at a time is the expensive failure mode. Settled:

**DRAW ORDER.** Both new solid features must *reserve* ground, so both run **before** the things that would otherwise cover them, and both register in the registries that the relevant placer honors (`placed` for distance-based clearance, `block_polys` for footprint blocking):

- `punishment_spot()` is called **before the urban packs**, like `manor()` and `granary()` - it sits in the core, where packing pressure is highest, and reserving after the pack would mean fighting for a seat that no longer exists.
- `execution_ground()` and `boundary_marker()` are called **beside the existing funerary cluster** (`cremation_ground` / `ossuary`), which is phase 4 - after the water and fields, before the hinterland scrub and `village_grove()`, so no crown or scrub is drawn onto the ground.
- All three draw at true size except the boundary marker, which is a **location marker** (true ~3 ft footprint recorded in `w`/`h`, drawn box in `vw`/`vh`), following the wells and the kosatsuba exactly.

**Placement, not guessed coordinates.** Where a pool map has no obvious free ground, use `s.open_seat(rect, w, h, clear_of=[...])` at the point in the gen where the feature belongs, rather than hand-picking coordinates and regenerating - the engine's own `_fits` sees no-build corridors that no manifest records.

**Presence is a floor with an opt-out**, matching `town_has_kosatsuba` / `town_has_cremation_ground`: towns and cities MUST carry both features, `meta(punishment_spot=False)` / `meta(execution_ground=False)` opts a suppressed or backwater seat out, and a companion check forbids either feature at hamlet/village tier.

**Every check that is gated on an optional declaration gets the "declaration exists" ratchet.** The dev-loop doc records three separate cases where the defect was a check that silently never ran. After wiring, verify per map with `python3 check_village.py pool/<tier>/<map>.json | grep -c "<check_name>"` - a `0` on a map that plainly has the feature is the bug.

## Complexity Tracking

No constitutional gate is DEFERRED or violated, so this section is empty.

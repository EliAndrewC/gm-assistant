# Implementation Plan: Village Visual Variation Knobs

**Branch**: `005-village-variation-knobs` | **Date**: 2026-07-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-village-variation-knobs/spec.md`

## Summary

Extend the Mode B settlement generator (`.claude/skills/diagram/`) so that villages are assembled from named, individually-tunable **knobs** rather than one frozen per-map template. Each knob can be pinned in a village spec or rolled independently and deterministically from the seed, gated by historical-typing rules so a roll respects the village's stated geography. Phase 1 delivers the "same water direction still distinct" knob set (cluster geometry, lane skeleton with derived headman/shrine, water-source placement, plot texture + grain drift, focal-feature catalogue); an automated **pool-level twin-detector** in `check_village.py` mechanically guards distinctiveness; Kikuta and Hoshigaoka are re-varied to stop twinning. Later phases add whole-terrain/settlement **archetypes** (contour terraces, polder grid, ribbon valley, mulberry-dike fish-pond; linear/dispersed/water-town forms; land-use overlays), each an incremental build with its own validator rules and to-scale grounding. Every knob value carries recorded historical grounding (China-first, Japan corroborating); all existing pool maps keep passing the gate.

**Foundation work first (GM-directed 2026-07-13):** before the knob work, the diagram skill is brought to full Principle X compliance - fix the ~10 `ruff` findings, wire `ruff` + `ruff format --check` + `mypy` + `pytest --cov-fail-under=100` into one gate command (a `make done` equivalent) so it is maintained going forward, and migrate the three engine modules (`settlement.py`, `check_village.py`, `waterfields.py`) to `mypy --strict` via a **per-module ratchet** (new code strict immediately; each legacy module annotated in a focused pass that flips it off the relax-list). This eliminates the Principle X deferral rather than carrying it.

## Technical Context

**Language/Version**: Python 3.13 (dev sandbox system Python).

**Primary Dependencies**: the diagram skill's own modules - `settlement.py` (the shared `Settlement` library), `check_village.py` (the validator), `waterfields.py` (`build_comb` irrigation/field engine); `rsvg-convert` (librsvg) for PNG rendering; `pytest` + `pytest-cov` for tests. No new third-party runtime dependency is anticipated (the roll uses the stdlib seeded RNG already in use).

**Storage**: files only - per-map `pool/<name>.gen.py` (spec + generator), `pool/<name>.json` (manifest consumed by the validator), `pool/<name>.svg` / `.png` (outputs), `pool/regressions/*.json` (saved negative fixtures). No database.

**Testing**: `pytest` - `test_villages.py` (integration: regenerate every pool map and run the full `check_village` gate), `test_checks.py` (negative fixtures asserting each check FIRES on a broken manifest), `test_settlement.py` (unit tests for `settlement.py` branches). Coverage gated at 100% (`fail_under = 100` in `pyproject.toml`) on `settlement.py` + `check_village.py`.

**Target Platform**: CLI / library. Generators run as `python3 pool/<name>.gen.py`; the validator runs as `python3 check_village.py pool/<name>.json` or via the pytest gate.

**Project Type**: Single project - a parametric generator + validator library inside one skill directory.

**Performance Goals**: Not a constraint. Generation is offline, seconds per map; the twin-detector runs over ~6 manifests.

**Constraints**: (a) to-scale realism preserved - every knob draws a real historical form at honest relative size (Mode B scale ladder: village = 1 px = 2 ft); (b) China-first grounding (Song/Ming rice south), Japan corroborating, GM canon overrides; (c) determinism - a spec + seed always produces an identical map (seeded rolls, no wall-clock entropy); (d) all six existing village/hamlet pool maps keep passing `check_village`; (e) every shipped knob value has recorded grounding in `settlements.md`.

**Scale/Scope**: The knob layer + independent seeded roll + historical-typing rules + the focal-feature catalogue + the pool-level twin-detector, applied first to re-vary Kikuta + Hoshigaoka (the MVP), then the terrain/settlement/land-use archetypes delivered one at a time (each: new geometry generator + archetype-specific validator rules + grounding). The other four village/hamlet maps (Hikari, Moritono, Ikegami, Ueda) stay as-is and keep passing.

**Unknowns resolved in Phase 0 research** (no open NEEDS CLARIFICATION): the historical catalogue of real variation axes and their to-scale grounding (China-first), the concrete value spaces + typing rules per knob, the twin-detector's axis set and threshold, and the current ruff/mypy status of the diagram skill (Principle X scope).

## Constitution Check

*GATE: evaluated pre-Phase-0 and re-checked post-Phase-1.*

- **I. Accessibility-First Viewports** - **N/A**. No webapp/HTML UI. Outputs are SVG/PNG diagram maps; the skill's own visual review is the rendered-PNG self-review + the `check_village` gate, not the browser screenshot/DOM-audit workflow.
- **II. Bold, Intentional Design** - **N/A**. No new webapp UI surface; the map's visual language (palette, glyphs) is the established diagram-skill convention and is unchanged.
- **III. Pool Data Conventions** - **N/A (different pool kind)**. The diagram Mode B pool is `gen.py` + `json` + `svg` + `png` gated by `check_village`, not the markdown-with-YAML relic-style pool Principle III governs. This feature adds no markdown-YAML pool entries. Village names stay generic placeholders (no `Kyuden/Shiro/Shinden` baked in).
- **IV. One Canonical Home for GM Source** - **N/A**. No `SOURCE` blocks added or moved.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)** - **PASS**. No task modifies any `SOURCE`-marked content; all edits are to generated/AI-authored generator code + grounding docs.
- **VI. Verify Before Reporting Done** - **PASS**. Every implementation task ends with: the `check_village` gate on all affected maps, the full `pytest` suite at 100% coverage on `settlement.py` + `check_village.py`, and a human render-review of any re-varied/new map (author reads the PNG; the twin-detector provides the objective distinctiveness signal). Delegated work (if any) is spot-checked.
- **VII. De-Localized Generation by Default** - **PASS**. Villages remain generic, reusable places; no knob locks a map to a specific city or campaign figure. Example NPC labels (headman, priestess) follow Principle IX (no campaign-name collisions).
- **VIII. Direct Voice Over Framing Distance** - **N/A**. No in-world prose; map labels are terse nouns.
- **IX. Setting Integration** - **PASS**. Knob grounding draws China-first on rice-south settlement geography (Song/Ming) with Japanese corroboration, recorded in `settlements.md`; sizing cross-references `/setting/` (demographics, median-domain). Any named figure is checked against the campaign-names cache before use.
- **X. Python Discipline (NON-NEGOTIABLE)** - **PASS (gate-enforced ratchet, GM-directed 2026-07-13)**. No deferral. The diagram skill is brought under full Principle X enforcement as the FOUNDATION work of this feature (before the knob work): (1) fix the ~10 `ruff` findings and wire `ruff check` + `ruff format --check` + `mypy` + `pytest --cov-fail-under=100` into a single diagram-skill gate command (a `make done` equivalent) so all checks run together and cannot be missed going forward; (2) because `mypy --strict` currently reports ~2,470 errors across `settlement.py`/`check_village.py`/`waterfields.py` (the engine passes an untyped manifest dict), adopt a **per-module strict ratchet**: `mypy --strict` is on in the gate from day one; **new** feature code (the knob layer, the twin-detector) is strict immediately; the three legacy modules are temporarily relaxed via per-module `mypy` config and then annotated to strict in **focused per-module passes within this feature**, each pass flipping its module off the relax-list so the gate blocks any backsliding. End state: the whole diagram skill passes `ruff` + `ruff format --check` + `mypy --strict` + `pytest` at 100% coverage, gate-enforced. Also committed: red-green TDD for every new check/knob and for each module's typing pass; behavior-named + parametrized tests; saved negative fixtures in `pool/regressions/`; no `print` in library paths (the CLI/gate `print` moves behind a script entrypoint or `logging` as each module is migrated). Configuration-over-hardcoding (X.11): per-map knob values are *spec parameters*, not runtime env config, so ConfigObj/pydantic-settings does not apply; knob defaults + value spaces live in typed data structures in `settlement.py`, not scattered magic literals.
- **XI. Japanese Authenticity (NON-NEGOTIABLE)** - **PASS (scoped)**. New focal features that surface Japanese terms (an ancestral hall, a water-mouth pavilion, a mill) must pass the kanji ↔ romaji ↔ meaning triangle if any kanji is drawn; map labels stay English-default per the skill's labeling rule, so most features carry no kanji.

**Gate result**: PASS on all principles. No DEFERRED gates; Complexity Tracking is empty. `/speckit-tasks` may proceed.

## Project Structure

### Documentation (this feature)

```text
specs/005-village-variation-knobs/
├── spec.md              # /speckit-specify + /speckit-clarify output
├── plan.md              # this file
├── research.md          # Phase 0 - historical variation axes + grounding, knob value spaces, twin-detector design, Principle X status
├── data-model.md        # Phase 1 - the Knob catalogue (value spaces, typing rules, defaults, roll), Village-spec shape, Focal-feature catalogue, Archetype registry
├── contracts/
│   └── knob-interface.md # Phase 1 - the knob declaration surface (meta), the roll contract, the twin-detector report contract, the archetype plug-in contract
├── quickstart.md        # Phase 1 - "generate a rolled village" + "pin a knob" worked walkthrough
├── checklists/
│   └── requirements.md  # spec quality checklist (done)
└── tasks.md             # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
.claude/skills/diagram/
├── settlement.py           # the shared Settlement library - ADD: the knob layer (declaration + independent seeded roll + historical-typing gate), derived headman/shrine placement, cluster-geometry + lane-skeleton + water-placement knobs, plot-texture hooks, the focal-feature catalogue placement
├── waterfields.py          # build_comb - EXTEND: plot-texture (plot size / bund regularity) + paddy-grain drift; later, new field-archetype generators (terraces, polder, ribbon, mulberry-fishpond)
├── check_village.py        # the validator - ADD: the pool-level twin-detector (cross-map distinctiveness) + per-knob/per-archetype validity rules; existing per-map gate unchanged
├── settlements.md          # grounding doc - RECORD the historical "why" for every knob value + archetype (China-first), per project policy
├── SKILL.md                # skill doc - DOCUMENT the knob surface + how to roll vs pin
├── pool/
│   ├── kikuta-village.gen.py    # RE-VARY through the knobs (distinct from Hoshigaoka)
│   ├── hoshigaoka.gen.py        # RE-VARY through the knobs (distinct from Kikuta)
│   ├── hikari-no-sato.gen.py    # unchanged (already distinct)
│   ├── moritono.gen.py          # unchanged
│   ├── ikegami.gen.py           # unchanged
│   ├── ueda.gen.py              # unchanged
│   └── regressions/*.json       # ADD negative fixtures for the new checks
├── test_villages.py        # integration gate (regenerate pool + full check_village) - stays green
├── test_checks.py          # ADD negative fixtures: twin-detector fires on a twinned pair; each new validity rule fires
└── test_settlement.py      # ADD unit tests: knob roll determinism, historical-typing gating, derived placement, plot-grain drift
```

**Structure Decision**: Single-project, in-place extension of the existing `diagram` skill. The knob layer is a new capability inside `settlement.py` (the shared library, per the skill's rule "only touch settlement.py for a genuinely new shared capability" - this qualifies); the twin-detector is a new function in `check_village.py`; `waterfields.py` gains the field-texture hooks and, later, the archetype field generators. No new packages or directories beyond the spec docs and the regression fixtures.

## Complexity Tracking

No constitutional gates are deferred; there are no violations to justify. (The one candidate - Principle X's ruff/mypy status on the legacy diagram code - was resolved by the GM-directed decision to bring the skill to full `ruff` + `mypy --strict` compliance via a gate-enforced per-module ratchet as this feature's foundation work, rather than defer it. See Constitution Check, Principle X, and the Foundation work package in Summary / research.md D7.)

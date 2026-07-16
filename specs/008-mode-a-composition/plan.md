# Implementation Plan: Mode A Composition Grammar + Perimeter-First Placer

**Branch:** `008-mode-a-composition` | **Spec:** [spec.md](spec.md)
**Status:** Draft (GM approved "Phase 1 + build Phase 2")

## Summary

Encode the historical Mode A composition (perimeter buildings + a named court-spine) as
doctrine + an inverted check (central open good, perimeter gaps bad), recompose the two
manors as intentional courtyards, and build a feet-first `CompoundProgram` + a
perimeter-first placer that auto-composes a draft the GM refines.

## Key design decisions (GM: flag D1)

- **D1 - scaffold vs regenerate-every-time.** The placer emits a **composed DRAFT SVG**
  that becomes the starting pool file, then hand-refined; the pool `.svg` stays the final
  hand-refinable source. It is NOT a Mode-B-style regenerate-every-time pipeline, because
  Mode A instances are bespoke and carry hand-tweaked particulars (relics, annotations,
  odd accretions) that do not belong in a placement program. The feet-first program is
  the source for the DRAFT (delivering "footage as source of truth" for the compositional
  skeleton); the particulars are added by hand. **Recommended; can evolve to fully
  regenerable later if we make many compounds.**
- **D2 - placement algorithm = perimeter-first ring** (NOT worst-fit, which scatters):
  (1) build the envelope + divider (two courts); (2) reserve the court-spine (forecourt
  at the gate, oshirasu before the office-hall band, inner garden behind the residence)
  as protected OPEN zones; (3) for each court and each wall in a fixed order, place that
  wall's buildings largest-first from a corner, hugging the wall, advancing with fire-gaps
  (kura ~6-10 ft, wooden ~6-8 ft); (4) overflow to an inner ring that still avoids the
  reserved court-spine; (5) emit SVG. Fixed ordering (like Mode B water-first) so it can't
  paint into a corner.
- **D3 - keep the placer a SEPARATE module** (`compound.py` / `placer` in the diagram
  skill), not entangled with `pack_audit.py` (which stays a read-only auditor). pack_audit
  gains only the perimeter metric.

## Technical Context

- Python 3.13; ruff + mypy --strict + pytest + pytest-cov; stdlib only (dataclasses, re).
- Feet-first: the program and placer work in FEET; a single emit step multiplies by
  `FTPX = 3` for SVG px. No pixel literals in the program.
- Pure logic (geometry/placement) separated from I/O (SVG string build / file write) for
  100% coverage without external-boundary mocks.

## Constitution Check

- **I. Accessibility-First Viewports** - N/A (no webapp UI; SVG plans + a CLI).
- **II. Bold, Intentional Design** - follows the established Mode A vocabulary/palette.
- **III. Pool Data Conventions** - the placer's DRAFT lands in `pool/` paired with its
  program; consistent with the pool convention (Mode B .gen.py analog).
- **IV / V. GM source** - PASS; no `l7r.md` / SOURCE-block edits.
- **VI. Verify Before Reporting Done** - PASS (committed): the five Python gates + a
  pack_audit perimeter/central pass + the size-audit subagent on the recomposed manors +
  read the rendered PNGs.
- **VII / VIII** - N/A (no generated setting prose).
- **IX. Setting Integration** - PASS; composition grammar cites the jin'ya grounding.
- **X. Python Discipline (NON-NEGOTIABLE)** - the spine of this feature: ruff, ruff format,
  mypy --strict, red-green TDD, 100% coverage on `pack_audit.py` additions + the new
  placer module. New code -> no grace period. `print` only in the CLI/emit shell.
- **XI. Japanese Authenticity** - labels reuse the vetted vocabulary; no new kanji.

No DEFERRED gates. One flagged decision (D1), recommended not deferred.

## Design detail

### Phase 1

- **pack_audit additions (FR-1/2):** `perimeter_hugging_pct(plan, depth_ft=25)` via the
  existing grid (a cell is "perimeter" if within depth of the interior edge / a wall);
  `VacantRect` gains `zone: "central" | "perimeter"` (perimeter if its bbox touches the
  perimeter band). Report lines + tags added. All TDD, keep 100%.
- **Composition grammar (FR-4):** buildings.md section: perimeter ring; the forecourt ->
  oshirasu -> garden court-spine; office-front/residence-rear; "every open region is a
  NAMED court." Historical grounding entry (why the center is composed courts, not slack).
- **Reframed sweep (FR-3):** size-audit PACKING sweep: report perimeter-hugging %; a
  perimeter-gap vacancy -> tighten; a large central vacancy -> keep only if named, else
  "name it or fill it." Central open is not a defect.
- **Recompose manors (FR-5):** name/extend the central open (forecourt label + a defined
  outer working-yard; extend/ްname inner-court open as garden/court), tighten any
  remaining perimeter gaps. No wall move, no coverage change beyond labelling.

### Phase 2

- **CompoundProgram (FR-6):** dataclasses - `Envelope(w_ft,h_ft, gate...)`,
  `CourtSpine(reservations: list[CourtZone])`, `BuildingSpec(name, kind, w_ft, h_ft,
  court: inner|outer, wall: N|S|E|W|any, order)`, `CompoundProgram(envelope, spine,
  buildings)`.
- **place() (FR-7):** returns `list[Placed]` (each a feet-rect + name/kind) via the D2
  algorithm; a pure function. `emit_svg(placed, program) -> str` multiplies by FTPX and
  builds labelled rects reusing the palette. A thin CLI writes the draft + renders.
- **Validate (FR-8):** encode the county-magistracy program, place it, emit, run
  pack_audit -> assert high perimeter-hugging %, court-spine intact, coverage in band.

## Phases (feed tasks.md)

- P1a pack_audit perimeter metric + central/perimeter tag (TDD, 100%).
- P1b composition grammar (buildings.md) + reframe size-audit sweep.
- P1c recompose Ochiba + Hayakawa; render; green-confirm (pack_audit + subagent + PNG).
- P2a CompoundProgram data model (typed, TDD).
- P2b perimeter-first place() + emit_svg (TDD, 100%, mypy, ruff).
- P2c encode a county-magistracy program; place/emit/render; pack_audit perimeter check;
  record grounding/notes/memory; final five gates.

## Risks

- Placer complexity could balloon - keep it to the fixed perimeter-first ordering, no
  backtracking; overflow-to-inner-ring is the only fallback; report (do not clip)
  anything that will not fit. Validate against ONE program, not a general solver.
- Recomposition could disturb existing labels - re-render + PNG read (Principle VI).
- Coverage on the placer's geometric branches - write the tests first, drive the branches.

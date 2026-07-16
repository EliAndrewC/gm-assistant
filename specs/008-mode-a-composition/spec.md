# Feature Specification: Mode A Composition Grammar + Perimeter-First Placer

**Feature branch:** `008-mode-a-composition`
**Status:** Draft (GM approved direction: "Phase 1 + build Phase 2")
**Input:** The area-budget calc showed Ochiba is 37% built / 63% open, historically
consistent for a courtyard compound - but the open is UNDER-COMPOSED (undifferentiated
bare middle) rather than organized into named courts. The right rule is "compose it
historically" (perimeter buildings + a defined court-spine), not "avoid empty space."
A perimeter-first placement algorithm (the Mode A analog of the Mode B water-first
generator) should make the composition reliable.

## Background / correcting the target

- Historical jin'ya composition is **office-front / residence-rear**, with buildings
  ringing the PERIMETER and the open ground forming a **structured spine of named
  courts**: forecourt at the gate -> the sanded **oshirasu** before the office-hall
  dais -> the divider wall -> the **garden/court** behind the residence. The center is
  a SEQUENCE OF NAMED COURTS, not one blank blob.
- So the check inverts from the old "flag empty space": **central open is GOOD**
  (courtyard), **perimeter gaps are BAD** (slack between edge buildings). Every open
  region must map to a named court; an unnamed central void is the defect.
- "Worst-fit" bin-packing would SCATTER buildings (maximize leftover everywhere),
  spreading them into the center - the opposite of the goal. The correct algorithm is
  **perimeter-first / ring placement**: biggest edge-buildings against the walls first,
  work inward, reserve the central court-spine.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The check rewards good composition, not emptiness (Priority: P1)

`pack_audit.py` measures **perimeter-hugging %** (building footprint within ~one
building-depth of a wall) and tags each vacant rectangle **central** (courtyard, keep)
vs **perimeter gap** (slack, tighten). The size-audit sweep then judges: perimeter gaps
-> consolidate; a large central open region -> keep, but it must be a named court.

**Acceptance:** on the current manors the tool reports a high perimeter-hugging % and
classifies the big central vacancies as central (not slack); the size-audit sweep asks
that each central court be named.

### User Story 2 - The two manors read as composed courtyards (Priority: P1)

The bare centers are defined as **named courts** (forecourt, the outer working yard,
the inner garden/court) - by extending gardens, labelling the forecourt and the
working yard - and perimeter gaps are tightened. Little or no building is added; the
envelope and coverage are unchanged.

**Acceptance:** after recomposition, every large open region on each manor is a labelled
court/garden; the size-audit packing sweep is clean; pack_audit's perimeter-hugging % is
high and no vacant rectangle is an unnamed perimeter void.

### User Story 3 - A compound is a feet-first program (Priority: P2)

A compound can be declared as a **feet-based program**: the envelope in feet, the
reserved court-spine, and a list of buildings each sized in feet with a zone/wall tag.
Footage is the source unit; pixels are derived (3 px/ft) only at emit time.

**Acceptance:** a `CompoundProgram` dataclass (typed) captures a county magistracy's
envelope + court-spine + building list entirely in feet; no pixel literals in the program.

### User Story 4 - The perimeter-first placer composes automatically (Priority: P2)

A placement routine takes a `CompoundProgram` and arranges the buildings **perimeter-
first**: reserve the court-spine, place buildings largest-first hugging their assigned
walls with fire-gaps, overflow to an inner ring that still avoids the court-spine, and
emit a composed **draft SVG** (feet -> px at emit) the GM refines.

**Acceptance:** running the placer on a county-magistracy program produces a draft whose
buildings hug the perimeter, whose center is the reserved court-spine, and which passes
pack_audit's perimeter/central check (high perimeter-hugging %, no unnamed perimeter void,
coverage ~37-42%).

### User Story 5 - Everything meets Python Discipline (Priority: P1)

All new/changed Python (`pack_audit.py` additions; the Phase 2 placer module) passes
ruff, ruff format, mypy --strict, pytest, and 100% coverage, TDD.

### Edge Cases

- A wall too short for all its assigned buildings -> overflow to the inner ring (not a
  crash, not an overlap).
- The court-spine reservation must never be overlapped by a placed building.
- A building larger than any wall run -> reported, not silently clipped.
- The placer's draft is a STARTING point; the final pool SVG stays hand-refinable
  (scaffold model - see plan decision D1).

## Requirements *(mandatory)*

- **FR-1** `pack_audit.py` computes `perimeter_hugging_pct(plan, depth_ft)` - fraction of
  building footprint within `depth_ft` of any interior wall.
- **FR-2** `pack_audit.py` classifies each vacant rectangle as `central` or `perimeter`
  (touching/adjacent to a wall band) and the report + `VacantRect` expose it.
- **FR-3** The size-audit PACKING sweep is reframed: perimeter-hugging % high is good;
  perimeter-gap vacancies -> tighten; a large central vacancy is kept ONLY if it is a
  named court (forecourt/oshirasu/garden), else "name it or fill it."
- **FR-4** buildings.md gains a **Mode A composition grammar** section (perimeter ring +
  court-spine; office-front/residence-rear; named-courts rule) with historical grounding.
- **FR-5** Both manors recomposed so every large open region is a labelled court/garden
  and perimeter gaps are tight; envelope + coverage unchanged; green on both checks.
- **FR-6** A `CompoundProgram` feet-first data model (typed dataclasses): envelope,
  court-spine reservations, buildings (name, fill/kind, w_ft, h_ft, zone, wall pref).
- **FR-7** A perimeter-first `place(program)` routine returning placed rects (in feet)
  + an SVG emitter (feet -> px at 3 px/ft), producing a composed draft.
- **FR-8** The placer output passes pack_audit's perimeter/central check on a real
  county-magistracy program.
- **FR-9** All Python at full Principle X (ruff/format/mypy --strict/pytest/100% cov),
  TDD; the placer + program live in the diagram skill with tests alongside.
- **FR-10** Grounding/notes/memory updated (the composition grammar "why"; the placer
  design; the recomposition logged).

## Success Criteria *(mandatory)*

- **SC-1** pack_audit reports perimeter-hugging % and central/perimeter tags; unit-tested.
- **SC-2** Both manors: every large vacant region is a named court; size-audit packing
  sweep clean; no unnamed perimeter void; coverage unchanged (~37-38%).
- **SC-3** The placer composes a county magistracy that passes the perimeter/central
  check with high perimeter-hugging % and a coherent reserved court-spine.
- **SC-4** ruff / ruff format --check / mypy --strict / pytest / 100% coverage pass on all
  new/changed modules.

## Assumptions

- Historical band already set (jin'ya ~37-42% built; forecourt/oshirasu ~12-18%). No new
  research beyond confirming the office-front/residence-rear + court-spine grammar (which
  the prior research already supports).
- The placer emits a DRAFT the GM refines; the pool SVG stays the hand-refinable final
  source (scaffold model - not a regenerate-every-time pipeline). See plan D1.

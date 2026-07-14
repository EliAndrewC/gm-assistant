# Tasks: Packing-Audit Hardening + Ochiba SE Consolidation

Scope (GM-approved): bring only the NEW `pack_audit.py` to full Principle X
compliance; `check_village.py`/`settlement.py` stay on their grace period.

Paths are under `.claude/skills/diagram/` unless noted.

## Phase 0: Research
- [ ] T001 Confirm the loading-apron depth figure (cart + draft animal ~15-20 ft);
  record in buildings.md grounding. (Quick check; band otherwise already set.)

## Phase 1: Setup (tooling, no behavior change)
- [ ] T002 Add `[tool.ruff]` (lint + format) and `[tool.mypy]` (strict) to
  `pyproject.toml`; add `pack_audit` to `[tool.coverage.run] source`. Keep the
  existing Mode B modules on their grace period (do not add them to mypy/ruff
  targets that would force a retrofit).

## Phase 2: Tests first (RED) - US5 (P1)
- [ ] T003 [P] Write `test_pack_audit.py`: behavior-named, parametrized tests over
  small SYNTHETIC svg strings / rect lists, covering (a) current behavior -
  `parse_svg`, `coverage`, `aligned_gaps`, maximal vacant rectangle; (b) NEW
  `top_vacant_rects` (returns >=N non-overlapping vacant rects, largest first) and
  `region_density` (per-tile coverage; a sparse tile reads low). Tests must FAIL
  against the current module (new functions absent). Include the "no interior
  rect -> raises" case and the `main()` shell via tmp_path.

## Phase 3: Implement (GREEN) - US1, US2, US5 (P1)
- [ ] T004 Refactor `pack_audit.py`: split typed pure-logic (dataclasses `Rect`,
  `ParsedPlan`, `VacantRect`, `Gap`, `RegionTile`; functions `parse_svg`,
  `coverage`, `top_vacant_rects`, `region_density`, `aligned_gaps`) from a thin
  `main(argv)` CLI shell that reads files + prints. Full annotations.
- [ ] T005 Implement `top_vacant_rects(plan, n, ...)` (greedy maximal-rectangle
  with masking; largest first; floor on area) and `region_density(plan, rows,
  cols)` (per-tile building-coverage over the interior mask). Preserve the
  existing report sections and ADD "top vacant rectangles" + "per-region density".
- [ ] T006 Make all five gates pass on the module: `ruff check`,
  `ruff format --check`, `mypy --strict pack_audit.py`, `pytest`,
  `pytest --cov-fail-under=100` (pack_audit at 100%).

## Phase 4: Red-confirm the miss - US1/US2 (P1)
- [ ] T007 Run hardened `pack_audit.py` on the PRE-fix Ochiba; confirm the SE void
  (~73x24 ft) appears in the top-N vacant list AND the SE tile's local coverage is
  far below the 37% average. (Reproduces the GM's finding objectively.)

## Phase 5: Rule + map fix - US3, US4 (P1/P2)
- [ ] T008 Update `agents/size-audit.md` PACKING sweep: read top-N vacant rects +
  the density grid; require a quantified `warrants ~N ft because <function>` line
  for any empty region cleared as a feature (apron ~15-20 ft; forecourt sized for
  assembly); an unquantified/over-size void is a finding. Record the Ochiba void
  as the validated example.
- [ ] T009 Consolidate Ochiba's SE: move cell + barracks (and the garrison latrine
  + the two SE fire-water tubs) north into a coherent range with a ~15 ft granary
  apron; no compound wall moves. Re-render (resvg) and READ the PNG (Principle VI).
- [ ] T010 Green-confirm: hardened `pack_audit.py` shows no unjustified >~20 ft
  vacant rectangle and a plausible SE tile; run the size-audit subagent -> clean
  PACKING sweep. Envelope + ~37% coverage unchanged; Hayakawa re-checked.

## Phase 6: Record + verify done
- [ ] T011 buildings.md grounding (top-N + local-density + quantify-the-apron,
  with the "why"); Ochiba + Hayakawa notes review-log entries; memory update.
- [ ] T012 Final Principle X gate: re-run ruff / format / mypy --strict / pytest /
  cov-100 and confirm the subagent green; only then report done.

## Dependencies
- T001, T002 before T003.
- T003 (red) before T004-T006 (green).
- T006 before T007 (need the hardened tool).
- T007, T008 before T009-T010.
- T009-T010 before T011-T012.

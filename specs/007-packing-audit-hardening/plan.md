# Implementation Plan: Packing-Audit Hardening + Ochiba SE Consolidation

**Branch:** `007-packing-audit-hardening` | **Spec:** [spec.md](spec.md)
**Status:** Draft (awaiting GM approval before /tasks + implement)

## Summary

Three coupled changes, driven by the GM catching a 1,760 sq ft void the packing
check waved through:

1. **Harden `pack_audit.py`** - report top-N vacant rectangles (not one) and a
   per-region (tiled) coverage breakdown, so a large secondary void and a
   locally-sparse quadrant can't hide behind a healthy global average / a
   legitimate forecourt.
2. **Bring `pack_audit.py` to Principle X compliance** - refactor into
   importable pure-logic geometry + a thin I/O/CLI shell; add full type
   annotations, a ruff config, and `test_pack_audit.py` at 100% coverage,
   written test-first.
3. **Tighten the size-audit PACKING sweep** - any empty region cleared as a
   "feature" must carry a quantified `warrants ~N ft because <function>` line;
   then fix Ochiba's SE (consolidate cell+barracks into a range with a real ~15 ft
   granary apron, no wall moved) and confirm the hardened check green.

## Technical Context

- **Language:** Python 3.13 (matches the project pin).
- **Tools:** ruff (lint+format), mypy --strict, pytest + pytest-cov. All config
  in the diagram skill's `pyproject.toml`.
- **Testing:** pure-logic unit tests with small SYNTHETIC svg strings / coordinate
  fixtures (not the pool maps, which change); behavior-named, parametrized.
- **No new dependencies** (stdlib `re`, `dataclasses`, `argparse`/`sys` only).
- **No UI, no network, no external boundary** - so 100% line coverage is
  achievable without fixtures-of-real-responses.

## Constitution Check

*GATE: must pass before implementation. Re-check after design.*

- **I. Accessibility-First Viewports (NON-NEGOTIABLE)** - N/A. No UI; this is a
  CLI analysis tool + an SVG data edit. No screenshot/DOM-audit obligation.
- **II. Bold, Intentional Design** - N/A (no visual design surface beyond the map
  edit, which follows the established Mode A vocabulary).
- **III. Pool Data Conventions** - N/A. `pack_audit.py` is a tool, not pool data;
  no `.gen.py`/manifest pattern applies.
- **IV. One Canonical Home for GM Source** - PASS. Touches only skill tooling and
  two pool SVGs; does not touch `l7r.md` or any GM source.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)** - PASS. No `SOURCE` blocks,
  no `l7r.md` edits.
- **VI. Verify Before Reporting Done** - PASS (committed): the five Python gates
  below MUST pass, AND the size-audit subagent must return a clean PACKING sweep
  on the fixed Ochiba (red-then-green), AND the rendered PNG is read back before
  "done."
- **VII. De-Localized Generation by Default** - N/A (no generated setting content).
- **VIII. Direct Voice Over Framing Distance** - N/A (no prose generated).
- **IX. Setting Integration** - PASS. The historical anchors (jin'ya coverage
  band, loading-apron depth) are already established and recorded in buildings.md
  grounding; the fix stays consistent with them.
- **X. Python Discipline (NON-NEGOTIABLE)** - THIS IS THE FEATURE. Committed:
  1. `ruff check` passes on `pack_audit.py`.
  2. `ruff format --check` passes.
  3. `mypy --strict` passes (full annotations; new code, no grace period).
  4. Red-green TDD: `test_pack_audit.py` written and failing before the
     top-N / per-region logic lands.
  5. `pytest --cov-fail-under=100` on the pack_audit pure logic.
  7. No swallowed exceptions (the "no interior rect" case raises, not passes).
  8. `print` is allowed - pack_audit is a script/dev-tool with a `__main__`
     guard; the importable pure-logic functions do not print.
  9/10. Behavior-named, parametrized tests.
- **XI. Japanese Authenticity (NON-NEGOTIABLE)** - N/A. No kanji/romaji generated
  (existing labels unchanged).

**No DEFERRED gates.** One scope decision requiring GM nod (below), not a
constitutional deferral.

### Scope decision (GM confirm)

`check_village.py` / `settlement.py` currently have pytest + 100% coverage but no
ruff/mypy and are largely untyped. Principle X grants pre-existing code a one-time
grace period. **Proposed scope: bring only the NEW `pack_audit.py` to full
compliance now**; add ruff/mypy config to `pyproject.toml` but target it at
`pack_audit.py` (and keep the existing modules on their grace period, retrofit as
a separate follow-up). Alternative (heavier): retrofit all three now. Recommend
the focused scope.

## Design

### D1 - Refactor for testability (FR-6, FR-7)

Split `pack_audit.py` into:
- **Pure logic** (no I/O): `parse_svg(text) -> ParsedPlan`, `coverage(plan)`,
  `top_vacant_rects(plan, n) -> list[Rect]`, `region_density(plan, rows, cols)`,
  `aligned_gaps(plan) -> list[Gap]`. Dataclasses for `Rect`, `Gap`, `ParsedPlan`.
  All fully typed; deterministic; unit-tested.
- **Thin shell**: `main(argv)` reads files, calls the pure functions, prints the
  report. Excluded from coverage via the existing `__main__`/entry pattern (or a
  tiny `# pragma: no cover` on the print glue), so 100% applies to the logic.

### D2 - Top-N vacant rectangles (FR-1)

Greedy: compute the maximal empty rectangle; record it; mark those cells occupied;
repeat until N found or no rectangle >= a floor area (e.g. ~150 sq ft). Yields the
forecourt AND the SE void as separate entries. Report each with dims/orientation/
location.

### D3 - Per-region density (FR-2)

Tile the interior bounding box into a small grid (default 3x3). For each tile,
compute building-footprint / tile-interior-area. Report the grid; the size-audit
sweep flags any tile that is both large-interior and far-below the global
coverage (a locally-sparse pocket) as a consolidation candidate.

### D4 - size-audit sweep update (FR-4)

Add to the PACKING sweep: read top-N vacant rects + the density grid; and require
that every empty region cleared as a feature states the historical size its
function warrants (loading apron ~15-20 ft; forecourt sized for assembly) and
that the drawn region fits. An unquantified label or an over-size void is a
finding. This closes the "it's a cart apron" laundering. Record the Ochiba void as
the validated example.

### D5 - Ochiba SE consolidation (FR-5)

Move the cell (x=820-874) and barracks (x=900-992) NORTH so the granary->range
gap is a real ~15 ft apron (~45 px) instead of ~24-27 ft, forming a coherent SE
storehouse-and-guard range under the granary; move the attached garrison latrine
and the two SE fire-water tubs with them; no compound wall moves; re-render and
read the PNG. Exact px in tasks, tuned against the hardened `pack_audit.py`.

## Project Structure

```text
.claude/skills/diagram/
  pack_audit.py            # refactored: pure logic + thin CLI shell
  test_pack_audit.py       # NEW - 100% coverage, test-first
  pyproject.toml           # + ruff config, + mypy config, + pack_audit in cov source
  buildings.md             # grounding: top-N + local-density + quantify-the-apron
  agents/size-audit.md     # PACKING sweep: top-N/density + quantified justification
  pool/ochiba-magistracy.svg / .png / .notes.md   # SE consolidation + review log
specs/007-packing-audit-hardening/
  spec.md  plan.md  tasks.md
```

## Phases (feed /tasks)

- **P0 Research:** confirm the loading-apron depth figure (~15-20 ft, cart+oxen);
  no other research (band already established). One quick web check.
- **P1 Setup:** add ruff + mypy config to `pyproject.toml`; decide coverage scope
  (D-scope). No behavior change.
- **P2 Test-first (red):** write `test_pack_audit.py` for the CURRENT behavior
  (coverage, aligned gaps, maximal rect) to lock it, THEN for the NEW top-N and
  per-region functions (failing).
- **P3 Refactor + implement (green):** split pure logic / shell, add types,
  implement top-N + per-region; make ruff/format/mypy/pytest/100%-cov all pass.
- **P4 Red-confirm the miss:** run hardened pack_audit on PRE-fix Ochiba; show the
  SE void in top-N and the sparse SE tile (reproduces the GM's finding).
- **P5 size-audit update + Ochiba fix:** update the PACKING sweep rule; consolidate
  Ochiba's SE; re-render; run size-audit green.
- **P6 Record:** grounding, notes review-log (both maps), memory; verify all five
  Python gates + the subagent green before "done."

## Risks

- Refactor could change report output subtly - P2 locks current behavior with
  tests first to catch drift.
- Moving the SE cluster could collide labels - mitigated by re-render + PNG read
  (Principle VI) and the pack_audit re-run.
- Coverage scope: if GM wants the full retrofit, P1/P3 grow to cover
  check_village/settlement typing (larger; flagged as the scope decision).

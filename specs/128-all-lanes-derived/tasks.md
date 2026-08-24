# Tasks: Farmhouses Before Lanes

**Spec**: [spec.md](spec.md) (FAITHFUL, round 2) | **Plan**: [plan.md](plan.md)

> [!IMPORTANT]
> **TICK THESE AS THEY PASS VERIFICATION, not when the code is written.**
>
> Feature 126's list was left at 42 tasks and zero ticks, including finished ones, and the next
> session could not tell what remained. A list nobody marks off is worse than no list, because it
> looks like a record.

## Phase 1: Setup

- [x] T001 Take the `128-start` perf bookend on unmodified code, before the first edit
- [x] T002 Record the regression baseline: the green gate at the pre-128 commit (3453 passed, both
      coverage floors met, 12 guard suites green)
- [x] T003 Record the pre-change measurement the whole feature is judged on: how many houses does the
      reference hamlet currently place, and how many candidate seats are refused by a lane corridor
      or tread. Without this, "it got better" has nothing to compare to

## Phase 2: The split (blocks everything)

- [x] T004 Split `stage_ways` in `l7r/diagram/hamletgen/ways.py` into `stage_seat` (drain lookup,
      `plan.watercourses`, `seat_cluster`, windward reconciliation - and NO call to `s.lane`) and
      `stage_track` (the connector and the field spur)
- [x] T005 Cover BOTH branches in `stage_track`: the polder connector at the early return, and the
      valley connector and spur. A fix to the valley path alone leaves polder hamlets reserving
      ground and the reference hamlet will not catch it
- [x] T006 Update `STAGES` in `l7r/diagram/hamletgen/driver.py` to `... sink, seat, homesteads,
      appurtenances, track, web, ...` AND its comment block in the same edit - that comment is
      declared to be the DRAW ORDER map's authority, so the two move together
- [x] T007 Assert `stage_seat` draws nothing: a test that no lane and no corridor exists when it
      returns

## Phase 3: Derive from the houses (US2)

- [x] T008 [US2] Re-origin the connector from the PLACED houses rather than
      `skeleton_layout(...seat["lat"], seat["dep"])` - feature 126's unfinished T009
- [x] T009 [US2] Re-origin the field spur from the placed cluster rather than the band's center point
      `to_screen((0, 0))`
- [x] T010 [US2] Assert `skeleton_layout` is not called before `stage_homesteads` - by test, not by
      reading, because this is the exact call 126 left behind

## Phase 4: Prove it (US1)

- [x] T011 [US1] **FIRES**: add a `check_village` segment asserting no house center lies in a lane
      corridor or on a tread, and prove it fires by feeding it a manifest that violates it
- [x] T012 [US1] **STAYS QUIET**: the same check passes on the reference hamlet
- [x] T013 [US1] Roll the reference hamlet and confirm the whole gate is green (SC-003)
- [x] T014 [US1] Re-measure T003's numbers and record the difference in this file

## Phase 5: The pool, and the page

- [x] T015 Roll the other three live pool hamlets and gate each (the second half of "every step is
      two steps"). **This is the task that earned its keep.** Kashikawa and Sawada came out clean;
      MIZUGUCHI REGRESSED - connector 0.2 ft from a garden and 14.6 ft from a farmhouse, on two checks
      its committed manifest passed. Three faults behind it, all fixed and written up in
      `pool/hamlets/mizuguchi.notes.md`. The reference hamlet alone would never have shown it
- [x] T016 Run `settlement-review` on the reference hamlet before it ships
- [x] T017 Regenerate the walk-through page and EDIT ITS CAPTIONS to match the new order. The
      captions are the deliverable: plate 05 said the opposite of what the code did for five days,
      and that is what made this feature necessary
- [x] T018 Read the regenerated page as the GM would, and confirm no plate before the farmhouses
      shows a lane. Plate 05 (`stage_homesteads`) shows the fifteen steadings standing on open ground
      with no way among them; plate 06 (`stage_track`) lays the connector down the cluster's WEST side
      and the spur into the field's near corner. Also found by reading it: the page on disk was still
      the pre-128 one (`04-stage_ways.png` before the houses - what the GM read), and a renumber had
      orphaned seven plates in a committed directory. The generator now prunes every plate it did not
      write, so a reorder cannot leave a picture of the old order lying next to the new one

## Phase 6: Close

- [x] T019 Mark feature 126's FR-003 superseded in `specs/126-derived-lanes-and-form/spec.md`
- [x] T020 Update the `dev/placement.md` DRAW ORDER map if it names the old stages
- [x] T021 Run `ruff` + `mypy --strict` + the full gate once, backgrounded. Green: 3,462 passed,
      12 guard suites, ruff and mypy --strict clean across 146 source files
- [x] T022 Take the `128-end` bookend and clear the perf gate. Run as `make perf-gate` on its own
      rather than inside `make done FULL=1`, because the GM has said plainly that the full sweep is
      not wanted for this scope; `perf-gate` takes the bookend and runs the comparison without it.
      Result: TOTAL -29.9%, three seeds individually over 5% and each diagnosed in writing in
      [`perf.md`](perf.md). The 5%-blocks-a-merge rule was replaced by the GM this session with two
      bands (diagnose at 5% per seed, block at 10% total) - constitution VI, v1.16.0
- [x] T023 Audit `dev/bypass-log/` for entries added during this feature and say in writing whether
      each was justified. **Feature 128 logged NO bypasses at all.** The eight entries in the
      directory break down as: one smoke test of the audit mechanism; four from feature 126 (three of
      them the same pre-push full sweep re-run, justified - the reference-scope gate cannot enforce
      the coverage floors, because deselected tests take their coverage with them); and three stamped
      17:15:29-30Z which are the guard's own test companion exercising cancelled / refused /
      permitted, not real runs. Nothing here needed a reason it did not have
- [x] T024 Tick every completed task above and confirm none is left unticked that was in fact done.
      All 24 ticked. The list was maintained AS the work went rather than at the end, which is the
      obligation feature 126 broke by leaving 42 tasks and zero ticks

## Dependencies

Phase 2 blocks everything. Phases 3 and 4 are independent of each other. Phase 5 needs 2-4 done.

## Baseline

| | value |
|---|---|
| `128-start` | total 394.3 s, median 73.3 s (2026-08-24, pre-edit) |
| gate at pre-128 commit | green, 3453 passed |
| lanes present when `stage_homesteads` runs | **2** (the connector and the field spur) |
| lane corridors present then | **2** of 25 - the other 23 are field and water keep-outs, which are legitimate and not this feature's business |
| houses placed | 15 of 15 |

**The target after the change**: 0 lanes and 0 lane corridors at `stage_homesteads`, still 15 houses.
Measured per stage by walking `STAGES` and counting `s.M["lanes"]` and `s.corridors` after each.

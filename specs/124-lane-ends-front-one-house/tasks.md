# Tasks: feature 124

**Baseline**: feature 123's shipped state (main at `1cefb97`) - `make done` green at 3,371 tests,
in-gate cohort 4/4, four pool hamlets green.

- [x] T001 Write the check FIRST. `_seg_0611__lane_ends_front_different_houses` in
      `check_village/segments_07c_*.py`, registered in `tests/fixtures/gate_check_names.json`.
- [x] T002 Prove it red before fixing anything: it fired on three of the four shipped maps,
      including Mizuguchi at (1120, 1713) - the exact coordinate the review named.
- [x] T003 Freeze the negative fixtures in `pool/regressions/`.
- [x] T004 Narrow the rule twice, each time because it was measurably wrong:
      a bearing clause (a house on a CORNER is not a fan), then the fray clause (an end 21.6 ft from
      a near-parallel way has not MET it - the engine's own `_FRAY_DEG`, and leaving it out un-fired
      the motivating fixture).
- [x] T005 Fix: `trim_lane_stubs`'s house test is now EXCLUSIVE - the end nearest a farmhouse keeps
      it, and any end alongside it pointing the same way must find its own reason or be trimmed.
- [x] T006 Unit tests: the fan fires; a corner does not; an end that crossed a way squarely is
      exempt; silent with no lanes or houses.
- [x] T007 Re-roll, gate, cohort.

## The fixture that was dropped, and why that is the honest move

Three maps fired at first and three fixtures were frozen. Under the finished rule **Sawada's no
longer fires** - its pair turned out to be a genuine junction, not a fan. A frozen fixture that does
not fire is worse than no fixture: it reads as coverage and provides none. It was deleted rather than
kept or "fixed" by loosening the rule back to where it would catch it.

The two that remain (Kashikawa, Mizuguchi) fire on the pre-fix manifest and pass on the shipped one,
which is the pair of facts that proves the fix rather than asserting it.

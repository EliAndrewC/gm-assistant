# 122 - tasks

## Phase 1: baseline (Principle XIII)

- [X] T001 Detached worktree at HEAD (`git worktree add --detach`), capture `GATE_SEGMENTS` as JSON
      (`registry_before.json`) and run `make done` there for the pre-existing-failure ledger.
      **DONE: worktree at 75c9ad3; `registry_before.json` = 1,377 rows; baseline `make done` GREEN (so there are no pre-existing failures to ledger - the final gate must be green too).**

## Phase 2: the splits, in the GM's stated order

Each task: run the splitter, which self-verifies body byte-identity and segment order, then confirm
the package still imports and the gate still derives its registry.

- [X] T002 `segments_05_fields_and_funerary` (2,624) -> 05a field cover + cremation, 05b graveyards
      + channel sources, 05c streams + field ditches, 05d supply roadways + commons
- [X] T003 `segments_08_town_and_fire` (2,661) -> 08a ponds/marshes/drainage, 08b flow bands + the
      burakumin seam, 08c town battery trades + theater, 08d kosatsuba + paddy basins
- [X] T004 `segments_01_city_frame_and_yards` (2,413) -> 01a/01b/01c
- [X] T005 `segments_03_structures_and_wards` (2,397) -> 03a/03b/03c
- [X] T006 `segments_04_homesteads` (2,387) -> 04a/04b/04c
- [X] T007 `segments_02_capital_and_walls` (2,358) -> 02a/02b/02c
- [X] T008 `segments_07_water` (2,351) -> 07a/07b/07c
- [X] T009 `segments_06_ways_and_bridges` (2,339) -> 06a/06b/06c
- [X] T010 `segments_10_city_battery_c` (2,324) -> 10f/10g/10h
- [X] T011 `segments_10_city_battery_a` (1,958) -> 10a/10b/10c
- [X] T012 `segments_10_city_battery_b` (1,707) -> 10d/10e
- [X] T013 `segments_09_justice_and_tanning` (1,478) -> 09a justice grounds + land fall, 09b tanning
- [X] T014 `segments_11_polders_and_edges` (1,406) -> 11a/11b
      **DONE (T002-T014): 13 files -> 38, 598-869 lines each. Cut points came from `propose()` (balanced at segment boundaries) rather than being hand-typed, so no segment name was transcribed by hand.**

## Phase 3: surface and docs

- [X] T015 `check_village/__init__.py`: replace the 13 segment star-imports with the 41 new ones
- [X] T016 `check_village/CLAUDE.md`: the "Look here when" table gets a row per new file with its
      key range; the "Why the segment files are numbered ranges" section gains the letter convention
- [X] T017 `tests/check_village/CLAUDE.md`: the mapping rule relaxes from segment FILE to segment
      GROUP (`segments_05*`), and the two split test modules get rows
      **DONE (T015-T017): `__init__.py` 13 -> 38 star-imports; both indexes rewritten.**

## Phase 4: tests over the bar

- [X] T018 Split `test_segments_08_town_and_fire.py` (1,140) along the 08 theme cuts
- [X] T019 Split `test_segments_05_fields_and_funerary.py` (1,044) along the 05 theme cuts
      **DONE (T018-T019): 05 -> 537+539, 08 -> 583+587; all 326 tests preserved in order.**

## Phase 5: prove it

- [X] T020 Capture `GATE_SEGMENTS` again; diff against `registry_before.json` - must be IDENTICAL
- [X] T021 Confirm `tests/fixtures/gate_check_names.json` is untouched (`git diff --exit-code`)
- [X] T022 Prove every moved line is byte-identical: reconstruct each original file's body from the
      sub-files and diff against `git show HEAD:<path>`
- [X] T023 `ruff format` + `ruff check` + `mypy --strict`, then `make done` (backgrounded, not
      polled); compare failures against the T001 ledger
      **DONE (T020-T023): GATE_SEGMENTS IDENTICAL on all 1,377 rows; `gate_check_names.json` untouched; all 24,354 content lines byte-identical to HEAD; ruff/mypy clean; `pytest tests/check_village/` 1,359 passed.**

## Phase 6: record

- [X] T024 `future-work.md`: the 15 over-150-line segment functions, with the measurement and the
      reason they were deliberately left out of this feature
- [X] T025 Retire `split_segments.py` into this spec dir as a one-shot (022/023 convention), commit,
      `scripts/sync-with-main.sh done`

      **The one-shot tools (`split_segments.py`, `apply_all.py`, `capture_registry.py`) stay in this spec dir, retired, per the 022/023 convention. They are the only remaining references to the old file names, and correctly so - they name their inputs.**
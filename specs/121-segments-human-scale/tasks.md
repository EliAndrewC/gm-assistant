# 121 - tasks

## Phase 1: baseline (Principle XIII)

- [ ] T001 Detached worktree at HEAD (`git worktree add --detach`), capture `GATE_SEGMENTS` as JSON
      (`registry_before.json`) and run `make done` there for the pre-existing-failure ledger.

## Phase 2: the splits, in the GM's stated order

Each task: run the splitter, which self-verifies body byte-identity and segment order, then confirm
the package still imports and the gate still derives its registry.

- [ ] T002 `segments_05_fields_and_funerary` (2,624) -> 05a field cover + cremation, 05b graveyards
      + channel sources, 05c streams + field ditches, 05d supply roadways + commons
- [ ] T003 `segments_08_town_and_fire` (2,661) -> 08a ponds/marshes/drainage, 08b flow bands + the
      burakumin seam, 08c town battery trades + theater, 08d kosatsuba + paddy basins
- [ ] T004 `segments_01_city_frame_and_yards` (2,413) -> 01a/01b/01c
- [ ] T005 `segments_03_structures_and_wards` (2,397) -> 03a/03b/03c
- [ ] T006 `segments_04_homesteads` (2,387) -> 04a/04b/04c
- [ ] T007 `segments_02_capital_and_walls` (2,358) -> 02a/02b/02c
- [ ] T008 `segments_07_water` (2,351) -> 07a/07b/07c
- [ ] T009 `segments_06_ways_and_bridges` (2,339) -> 06a/06b/06c
- [ ] T010 `segments_10_city_battery_c` (2,324) -> 10f/10g/10h
- [ ] T011 `segments_10_city_battery_a` (1,958) -> 10a/10b/10c
- [ ] T012 `segments_10_city_battery_b` (1,707) -> 10d/10e
- [ ] T013 `segments_09_justice_and_tanning` (1,478) -> 09a justice grounds + land fall, 09b tanning
- [ ] T014 `segments_11_polders_and_edges` (1,406) -> 11a/11b

## Phase 3: surface and docs

- [ ] T015 `check_village/__init__.py`: replace the 13 segment star-imports with the 41 new ones
- [ ] T016 `check_village/CLAUDE.md`: the "Look here when" table gets a row per new file with its
      key range; the "Why the segment files are numbered ranges" section gains the letter convention
- [ ] T017 `tests/check_village/CLAUDE.md`: the mapping rule relaxes from segment FILE to segment
      GROUP (`segments_05*`), and the two split test modules get rows

## Phase 4: tests over the bar

- [ ] T018 Split `test_segments_08_town_and_fire.py` (1,140) along the 08 theme cuts
- [ ] T019 Split `test_segments_05_fields_and_funerary.py` (1,044) along the 05 theme cuts

## Phase 5: prove it

- [ ] T020 Capture `GATE_SEGMENTS` again; diff against `registry_before.json` - must be IDENTICAL
- [ ] T021 Confirm `tests/fixtures/gate_check_names.json` is untouched (`git diff --exit-code`)
- [ ] T022 Prove every moved line is byte-identical: reconstruct each original file's body from the
      sub-files and diff against `git show HEAD:<path>`
- [ ] T023 `ruff format` + `ruff check` + `mypy --strict`, then `make done` (backgrounded, not
      polled); compare failures against the T001 ledger

## Phase 6: record

- [ ] T024 `future-work.md`: the 15 over-150-line segment functions, with the measurement and the
      reason they were deliberately left out of this feature
- [ ] T025 Retire `split_segments.py` into this spec dir as a one-shot (022/023 convention), commit,
      `scripts/sync-with-main.sh done`

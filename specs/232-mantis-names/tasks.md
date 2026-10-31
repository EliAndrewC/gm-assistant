# Tasks: Mantis Clan names

- [x] T001 Baseline: run `make done` on unmodified HEAD (green at 6e5c6034 per this session's gate).
- [x] T002 [US3] Write `.claude/skills/name/pool-mantis.jsonl`: 16 GM examples (gm: true) + canon Budi, Agus, Haru + researched names; >= 40 male-usable, >= 40 female-usable; no intra-list near-duplicates.
- [x] T003 [US2] `webapp/chargen/mantisnames.py`: `is_rokugani`, `MantisName`, `load_mantis_pool`, `odds`, `roll_case`, `pick_mantis` (case roll, eligibility, exclusion, fallback), meaning text.
- [x] T004 [US2] Config: `[mantis_names]` in `configspec.ini` (defaults 20/10/10/60) and `development-defaults.ini`.
- [x] T005 [US1/US2] Tests `webapp/chargen/test_mantisnames.py`: syllable checker; every rokuganized form parses; GM examples present; counts; case rates over 10,000 rolls within 2 points; fallback; exclusion; neutral; 100% coverage.
- [x] T006 [US1] Engine: Mantis path in `Character.__init__`; `to_dict` adds `mantis_name`, `naming_case`; test that non-Mantis naming is unchanged and Mantis samurai get Mantis names.
- [x] T007 [US3/FR-010] `pick_name.py` `mantis` token through `mantisnames`; tests in `test_pick_name.py`.
- [x] T008 [FR-011/FR-009] `/chargen` and `/synthesize` SKILL.md: pass `mantis` for a Mantis subject's name bank; `/chargen` notes the three Mantis naming outcomes; `/name` SKILL.md documents the token and the list.
- [x] T009 Deploy bundle: Makefile copies `pool-mantis.jsonl`.
- [x] T010 Gate `make done` green; commit; `sync-with-main.sh done`.

## Found and fixed in the work (Principle XIV)

- The `/name` skill's own tests were never run by the gate (`testpaths` covers only `webapp/`), and
  had rotted: 7 of 39 failed against the grown roster (sheet-app players and lineage names joined
  `used_given_names` on 2026-08-27) and the file took 4.5 minutes because every `pick()` refreshed
  the cache from Obsidian Portal, overwriting the test's tmp roster with the real one. Fixed by an
  autouse fixture (`.claude/skills/name/conftest.py`) and a new `skill-tests` gate phase; the
  folder now runs 93 tests in 0.15 s.

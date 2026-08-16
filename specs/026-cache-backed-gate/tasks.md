# Tasks: Cache-Backed Gate (026)

**Input**: spec.md, plan.md, research.md (R1-R8), data-model.md, contracts/gate-cache.md
**Feature**: `SPECIFY_FEATURE=026-cache-backed-gate` | no branch (session clone, main)
**Tests**: YES - constitution Principle X TDD + the contract's pinning-test table with teeth demos

All file paths are relative to `.claude/skills/diagram/` unless noted. Every Python task ends with
the whole affected test file run (`-n auto --no-cov` mid-loop); the gate runs ONCE at the end.

## Phase 1: Setup

- [x] T001 Add the deterministic combine step: one `python3 -m coverage combine --append` line
      (tolerant of nothing-to-combine) in `Makefile` `test` target, after pytest, before the two
      `coverage report` calls. Verify: `make done` still green (this is the phase's only
      gate-affecting change).

## Phase 2: Foundational

- [x] T002 Spike test `test_gencache.py::test_a_foreign_parallel_coverage_file_reaches_the_report`:
      write a tiny synthetic parallel-mode data file covering a marker line during a pytest run,
      assert the combined report sees it (mechanics per research R3). This is the load-bearing
      mechanism for US2 - it MUST pass before anything is built on it. If it cannot be made to
      pass, STOP and re-plan R3.

## Phase 3: User Story 1 - dependency changes invalidate automatically (P1)

**Goal**: installed-distribution + renderer-font keying (research R1). **Independent test**: warm
cache, perturb dependency state, all entries miss; restore, entries hit.

- [x] T003 [US1] RED: add `test_gencache.py::test_a_dependency_change_invalidates_every_entry`
      (monkeypatch the deps-input helper to a different value -> every warm entry misses; restore
      -> hits). Written first, failing (helper does not exist yet).
- [x] T004 [US1] Implement the dependency-state input in `gencache.py`: sorted installed
      `(name, version)` via `importlib.metadata.distributions()` + bytes-hash of the DejaVu face(s)
      the renderer loads (locate the font path the drawing code uses; if unresolvable, degrade to
      a never-match marker - conservative direction). Fold into the key beside `sys.version` /
      resvg. Docstring records R1's why.
- [x] T005 [US1] [P] Unit tests to 100% for the new helper including the degradation path;
      run whole `test_gencache.py` locally (`-n auto --no-cov`).

## Phase 4: User Story 2 - the gate skips generation on a verified hit (P2)

**Goal**: `gate_obtain` per contracts/gate-cache.md; sweep rewired; floors hold warm and cold.
**Independent test**: two back-to-back gates - second one generates nothing, identical verdict.

- [x] T006 [US2] Implement `gencache.gate_obtain(gen)` per the contract: HIT = restore artifacts +
      copy `coverage.data` in as `.coverage.gatehit-<map>-<pid>`; MISS (key moved / corrupt /
      coverage-less / `GATE_NO_CACHE=1`) = subprocess `python3 -m coverage run --parallel-mode`
      driving `run_and_record`+`store`, then attach `coverage.data` + child-reported `gen_cpu_s`
      to the entry (inside the temp dir BEFORE the meta.json publish - atomicity preserved, per
      data-model.md). Returns `(manifest_path, how, gen_cpu_s)`.
- [x] T007 [US2] Rewire `test_villages.py::_regen_and_gate` to call `gate_obtain`; budget assert
      against child-reported CPU on a miss only; `check_village.main` stays in-process on BOTH
      paths; adapt `test_slow_gen_budget_fires_and_the_override_silences_it` to the new runner
      (still SHOWN to fire). The immunity test is NOT touched.
- [x] T008 [US2] Pinning tests in `test_gencache.py` (contract table):
      `test_the_gate_reuses_a_verified_hit`, `test_a_hit_still_runs_current_checks`,
      `test_an_entry_without_coverage_data_is_a_gate_miss`,
      `test_gate_miss_stores_coverage_the_next_hit_replays`. Each written red-first where the old
      behavior allows; otherwise teeth demonstrated by reverting the behavior and watching the
      test fail. Record each demo's result as a checklist note here when done:
      - [x] teeth: reuse-hit - TEETH-OK (behavior reverted via sed, pinning test failed, restored)
      - [x] teeth: hit-still-checks - TEETH-OK (behavior reverted via sed, pinning test failed, restored)
      - [x] teeth: coverage-less-is-miss - TEETH-OK (behavior reverted via sed, pinning test failed, restored)
      - [x] teeth: store/replay round trip - TEETH-OK (behavior reverted via sed, pinning test failed, restored)
- [x] T009 [US2] Retire `test_gencache.py::test_the_gate_never_reads_the_cache` (delete, with the
      commit message naming the GM decision it dies by).
- [x] T010 [US2] Local whole-file runs (`test_gencache.py`, `test_villages.py`), then verify the
      story end-to-end: `GATE_NO_CACHE=1 make done` (cold) green, `make done` (warm) green,
      identical verdicts, both coverage floors hold on the warm run. This is US2's independent
      test executed for real.

## Phase 5: User Story 3 - bypass, doctrine, procedure (P3)

**Goal**: escape hatch pinned; no doc states the dead rule. **Independent test**: bypass
regenerates on a warm cache; grep finds no stale doctrine.

- [x] T011 [US3] Pinning test `test_gencache.py::test_gate_bypass_forces_regeneration`
      (monkeypatch env, own the environment - delenv first, per the ALLOW_SLOW_GENS lesson; the
      test must not be silenceable by an inherited bypass). Teeth demo: ignore the var, test
      fails: - [x] teeth: bypass - TEETH-OK (env check reverted via sed, test failed, restored)
- [x] T012 [US3] [P] Docs rewrite: `gencache.py` docstring ("WHAT IT DELIBERATELY DOES NOT DO" ->
      the new contract + GM 2026-08-16 reversal record + dependency-change procedure);
      `regen.py` docstring (gate now rides the same audited path); skill `CLAUDE.md` cache/sweep
      sections ("The cache is NEVER the source of truth" paragraph rewritten; "AUDIT IT" gains the
      gate note; dependency-change procedure added: after a pip-level change or container rebuild,
      one `GATE_NO_CACHE=1 make done`). Grep for `never reads the cache` / `NEVER the source of
      truth` afterward - zero stale statements.
- [x] T013 [US3] [P] `docs/iteration-loop.md` (repo root): add the GM 2026-08-16 threshold rule -
      a >=5% speedup to a WHOLE process is always above the caring threshold regardless of
      absolute seconds; per-function micro-wins are not, unless the function is the process.
      Cite this feature as the motivating instance.

## Phase 6: Polish & Verification

- [x] T014 [P] `timings.py`: add `warm_gate` benchmark (prime with one cached sweep, then time
      `make done`; `full_gate` stays the bypassed/cold measurement so ledger rows stay
      comparable); FIX `bench_hamlet` (`python3 -m check_village`, broken since 024); retarget
      `bench_cache` from frozen minami to sawada (heaviest LIVE map). Cover new/changed pure logic
      to 100%.
- [ ] T015 Run `python3 cache_audit.py` (mandatory - this feature changes how generation is
      driven; ~10 min, background it). Record PASS/FAIL here: ______
- [ ] T016 Run `python3 timings.py --note "026 cache-backed gate"` (background); verify SC-001
      (warm_gate >= 5% faster than full_gate) and SC-004 (green cold + warm); ledger block
      appended. Record the two numbers here: cold ______ warm ______
- [ ] T017 Final gate: `make done` backgrounded, not polled, log tail is the authority. Then the
      stop-work ritual: commit, `scripts/sync-with-main.sh done`.

## Dependencies

- T001 -> T002 (the combine line makes the spike deterministic)
- T002 blocks all of US2 (T006-T010); US1 (T003-T005) is independent of T002
- T004 -> T006 (the key must carry deps before gate_obtain trusts it end-to-end), so US1 lands
  before US2 flips the default - the GM's safety-precondition ordering
- T006 -> T007 -> T010; T008/T009 after T006 (need the new behavior to pin)
- T011 after T006; T012/T013 [P] anytime after T010's behavior is settled
- T014 [P] independent of US3; T015/T016/T017 last, in that order (audit before measurement is not
  required, but both before the final gate report)

## Parallel opportunities

- T005 with T006 (different files); T012 + T013 + T014 all [P] after T010
- The long runs (T015 audit, T016 timings) background while docs tasks proceed

## Implementation strategy

MVP = US1 alone (safer cache for the existing iteration path, no gate change). US2 is the payoff
and flips the default; US3 + polish make it honest and measured. Single session, sequential
stories, ~15 tasks + 5 teeth-demo sub-checks.

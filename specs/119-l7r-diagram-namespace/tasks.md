---
feature: 119-l7r-diagram-namespace
---

# Tasks: One `l7r` Namespace, `l7r.diagram`, and `sitegen`

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/import-surface.md](contracts/import-surface.md),
[quickstart.md](quickstart.md)

**Tests ARE requested**: three guard tests, each red-green per constitution Principle X. Each must
be observed to FAIL against a real breakage before it is trusted - a guard nobody has seen fire is
not a guard.

## Format: `[ID] [P?] [Story] Description`

- `[P]` = parallelizable (different files, no dependency on an incomplete task)
- `[US1]` / `[US2]` / `[US3]` = the user story from spec.md this serves

## Path Conventions

All paths are relative to the session clone `/gm-assistant/.clones/diagram-reorganize/`.
`WEBAPP` = `webapp/`. `SKILL` = `.claude/skills/diagram/`.

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Take the Principle XIII gate baseline on unmodified code in a DETACHED WORKTREE
      (`git worktree add --detach /tmp/119-base HEAD`), running `make done` in both
      `/tmp/119-base/.claude/skills/diagram` and `/tmp/119-base/webapp`; record both results
      verbatim in `specs/119-l7r-diagram-namespace/plan.md`'s Baseline table, including any
      PRE-EXISTING failure, which is ledgered and NOT fixed under this feature.
- [ ] T002 Take the pool byte-identity baseline in the same worktree: regenerate every generator
      with `python3 -m pipeline.regen --frozen-ok pool/*/*.gen.py`, then hash every artifact
      (`find pool -type f ! -name '*.gen.py' ! -name '*.notes.md' | sort | xargs sha256sum`) into
      `/tmp/119-baseline-hashes.txt`; record the artifact count in plan.md. This ONE manifest is
      the oracle for all three landings - no landing ever compares against another landing's output.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Blocks every user story**: nothing may be judged before T001/T002 exist, because without them a
failure cannot be classified as new or pre-existing.

- [ ] T003 Confirm the two baselines are complete and readable, and that `/tmp/119-base` is a
      detached worktree at the pre-feature HEAD (`git -C /tmp/119-base rev-parse HEAD`) - never a
      stash of the working tree.

---

## Phase 3: User Story 1 - The `l7r` prefix becomes shareable (Priority: P1) 🎯 MVP

**Goal**: `webapp/l7r/` becomes a PEP 420 namespace portion so the `l7r` prefix can be shared.

**Independent test**: `webapp make done` green, `cherryd --import l7r.app` serves the site, and a
scratch second `l7r/` portion on another `sys.path` root imports alongside `l7r.app`.

### Tests for User Story 1

- [ ] T004 [US1] Write `webapp/tests/test_namespace_portion.py` asserting `l7r.__file__ is None`
      with a failure message naming the cause ("something re-added webapp/l7r/__init__.py"), and
      PROVE IT RED by temporarily creating `webapp/l7r/__init__.py`, running the test, and
      recording the observed failure before deleting the file again.

### Implementation for User Story 1

- [ ] T005 [US1] Delete `webapp/l7r/__init__.py` and move its docstring content ("Importing this
      package wires the CherryPy tree") into `webapp/l7r/app.py`'s module docstring, where it
      becomes literally true; state there that `l7r` is a namespace portion shared with
      `l7r.diagram` and must never gain an `__init__.py`.
- [ ] T006 [P] [US1] Repoint the bare-import side-effect consumers to `import l7r.app`:
      `webapp/conftest.py`, `webapp/tests/test_character_rank_jitter.py`,
      `test_character_location.py`, `test_character_posts.py`, `test_character_rank_bonus.py`,
      `test_character_monk.py` (keep each one's existing explanatory comment).
- [ ] T007 [P] [US1] Repoint the launch paths: `webapp/Dockerfile` CMD to
      `["cherryd", "--import", "l7r.app"]`, `webapp/Makefile` serve target, and the
      `python3 -c "import l7r; from chargen import opcache; ..."` line in `webapp/Makefile`.
- [ ] T008 [US1] Verify no OTHER `l7r` reference depends on the deleted `__init__.py`: grep
      `webapp/` for `^\s*import l7r\b` and `from l7r import` and confirm every remaining hit is a
      submodule import (`from l7r import app as app_module` is fine and stays).
- [ ] T009 [US1] Run the webapp gate: `cd webapp && make done`. Compare failures against T001's
      baseline; zero NEW failures is the bar.
- [ ] T010 [US1] Smoke check: start the app the way the Dockerfile does
      (`cherryd --import l7r.app`), request the landing page and one sub-page, confirm both render,
      then stop it. "The import still works" is exactly what could have broken.

**Checkpoint**: commit landing 1 and run `scripts/sync-with-main.sh done` - three sibling diagram
sessions are live and this diff is a textual conflict magnet.

---

## Phase 4: User Story 2 - The diagram engine moves under `l7r.diagram` (Priority: P1)

**Goal**: the eight engine units live at `l7r/diagram/`, importable under exactly one dotted name.

**Independent test**: every pool artifact byte-identical to the T002 baseline, diagram `make done`
green, zero stale module paths by grep.

### Tests for User Story 2

- [ ] T011 [US2] Write `.claude/skills/diagram/tests/test_namespace_portion.py` asserting
      `l7r.__file__ is None`, and PROVE IT RED by temporarily creating
      `.claude/skills/diagram/l7r/__init__.py`, recording the observed failure, then deleting it.

### Implementation for User Story 2

- [ ] T012 [US2] Create `.claude/skills/diagram/l7r/diagram/__init__.py` and `git mv` the eight
      engine units into it: `settlement/`, `check_village/`, `waterfields/`, `hamletgen/`,
      `pipeline/`, `tools/`, `compound.py`, `citybudget.py`. Create NO `l7r/__init__.py`. DELETE
      the old trees outright rather than copying - a surviving directory is how one file acquires
      two module identities (research R2). Clear stale `__pycache__` under the old paths.
- [ ] T013 [US2] Repath all 245 absolute engine imports per
      [contracts/import-surface.md](contracts/import-surface.md). Intra-package relative imports
      (`from .geom import …`) are untouched by construction; assert that count is unchanged
      afterwards. Verify with a grep that no bare `from settlement`/`import check_village`/etc.
      survives anywhere in `.py`.
- [ ] T014 [US2] Repath the gate configuration in `.claude/skills/diagram/pyproject.toml` in all
      four places: `[tool.ruff.lint.per-file-ignores]` (5 keys), `[tool.mypy] files`,
      `[tool.coverage.run] source` (preserve the deliberate one-by-one listing style - longer, not
      looser), `[tool.coverage.run] omit`. Then `.claude/skills/diagram/Makefile`'s coverage
      `--include`/`--omit` globs, confirming they still select the `settlement/` tree at its new
      path (the ratchet floor depends on it).
- [ ] T015 [US2] Repath the 26 generator import lines under `pool/` and `wip/` - ONE line each.
      Then prove the `sys.path` bootstrap block (`HERE` / `SKILL = dirname(dirname(HERE))` /
      `sys.path.insert`) is byte-unchanged in every one of them via `git diff`; a changed bootstrap
      means `pool/` moved when it must not have.
- [ ] T016 [US2] Run the diagram gate: `cd .claude/skills/diagram && make done` (background it;
      act on the completion notification rather than polling). Add `explicit_package_bases = true`
      + `mypy_path` ONLY if mypy actually reports a duplicate-module error, and record it in
      research.md R2 if so.
- [ ] T017 [US2] Run the byte-identity sweep: regenerate every generator with `--frozen-ok` in a
      scratch copy, hash the artifacts, and `diff` against `/tmp/119-baseline-hashes.txt`. The diff
      MUST be empty. One differing byte stops the feature and is diagnosed, not accepted.
- [ ] T018 [P] [US2] Update the 39 live-doc command references across 13 files:
      `.claude/skills/diagram/CLAUDE.md` (18), `pipeline/CLAUDE.md` (4), `hamletgen/CLAUDE.md` (3),
      `SKILL.md` (3), `future-work.md` (2), `check_village/CLAUDE.md` (2), `tools/CLAUDE.md`,
      `settlements.md`, `migration-plan.md`, `hamletgen.md`, `docs/iteration-loop.md`,
      `.claude/agents/size-audit.md`, `.claude/agents/settlement-review.md`. Do NOT touch
      historical `specs/NNN-*/` artifacts - they are dated records (research R6).
- [ ] T019 [P] [US2] Update the structural prose that states WHERE engine code lives: the "Where
      things live" table in `.claude/skills/diagram/CLAUDE.md` (including the note that
      `compound.py` and `citybudget.py` stay single top-level files - still true, at a new path),
      and the Key Paths entries in the root `CLAUDE.md`.
- [ ] T020 [US2] Verify the new CLIs actually run:
      `python3 -m l7r.diagram.check_village <a pool manifest>` and
      `python3 -m l7r.diagram.hamletgen --batch 1 --seed 1` from the skill directory.

**Checkpoint**: commit landing 2 and run `scripts/sync-with-main.sh done`.

---

## Phase 5: User Story 3 - `sitegen` exists, and the growth rule is written down (Priority: P2)

**Goal**: a shared package for the tiers above hamlet, with a stated membership rule and a proven
one-way import direction.

**Independent test**: byte-identity again vs the ORIGINAL baseline, gate green, and no tier concept
anywhere in `sitegen`.

### Tests for User Story 3

- [ ] T021 [US3] Write a test asserting the import direction - nothing under
      `l7r/diagram/sitegen/` may import `hamletgen` or any other tier generator - and PROVE IT RED
      by temporarily adding such an import, recording the observed failure, then reverting.

### Implementation for User Story 3

- [ ] T022 [US3] Create `l7r/diagram/sitegen/` with `types.py` (`Pt`, `Poly`, `SQ_FT_PER_ACRE`),
      `geom.py` (the 94-line helper set) and `jobs.py` (`default_jobs`) - every member moved
      VERBATIM, its comments included. Remove the moved names from `hamletgen/consts.py`,
      `hamletgen/geom.py` and `hamletgen/driver.py`.
- [ ] T023 [US3] Repoint `hamletgen`'s intra-package importers of the moved names:
      `cluster.py`, `water.py`, `hinterland.py`, `sink.py`, `plan.py`, `homesteads.py`, `ways.py`,
      `driver.py`, `__init__.py`. `hamletgen`'s public surface (`HamletSpec`, `generate`, the
      `__main__` CLI) MUST be unchanged - confirm no generator under `pool/` or `wip/` needs an
      edit for this landing.
- [ ] T024 [US3] Add `l7r/diagram/sitegen/CLAUDE.md` whose FIRST lines state the membership rule
      (no tier concepts), the direction rule (tier generators import `sitegen`, never the reverse)
      and the growth rule (MOVE, never copy), with a row per module.
- [ ] T025 [US3] Add the three `sitegen` modules to `[tool.mypy] files` and
      `[tool.coverage.run] source`, and confirm 100% coverage - the moved helpers are already
      exercised through `hamletgen`, so a coverage hole means a helper lost its only caller.
- [ ] T026 [US3] Record the standing rules where a village-tier session will actually read them:
      `.claude/skills/diagram/migration-plan.md` section 5 (the architectural question, now
      ANSWERED: tiers share a stage library) and section 8 (say so explicitly if villages are being
      taken ahead of the four remaining hamlet archetypes, so the plan and the work do not
      disagree), plus `.claude/skills/diagram/hamletgen/CLAUDE.md` (the MOVE-don't-copy rule).
- [ ] T027 [US3] Run the diagram gate and the byte-identity sweep again, comparing against the
      ORIGINAL `/tmp/119-baseline-hashes.txt`, not against landing 2's output.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T028 Prove zero stale module paths repo-wide: grep `.py` for bare engine imports and live
      `.md` for old `python3 -m` forms; both must return nothing outside `specs/`.
- [ ] T029 Re-run BOTH gates end to end (`webapp make done`, diagram `make done`) and compare to
      T001's baseline. Zero new failures is the merge bar (Principle XIII); if anything regressed,
      the exits are fix, revert, or an explicit GM waiver - the work stays unpushed otherwise.
- [ ] T030 Confirm all three guard tests were observed RED and are now green, and that each names
      the specific breakage in its failure message.
- [ ] T031 Update `specs/119-l7r-diagram-namespace/spec.md` Status to Implemented with the measured
      closing numbers (artifacts compared, gate results, lines extracted), the way features 111-118
      record theirs.
- [ ] T032 Stop-work ritual: commit in the clone and run `scripts/sync-with-main.sh done` from
      inside it. Remove the `/tmp/119-base` worktree (`git worktree remove`).

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (T001-T002) blocks everything - a failure cannot be classified without a baseline.
- Phase 2 (T003) blocks all user stories.
- Phase 3 (US1) blocks Phase 4 (US2): the diagram portion cannot merge into a namespace that does
  not exist yet. This is a REAL dependency, not sequencing preference.
- Phase 4 (US2) blocks Phase 5 (US3): `sitegen` is created at its `l7r/diagram/` path.
- Phase 6 requires all three landings.

### Within Each User Story

- The guard test comes first and is proven RED before the change it guards.
- Move → repath imports → repath config → repath generators → gate → byte-identity sweep.
- Doc tasks are parallel with the gate, never a substitute for it.

### Parallel Opportunities

- T006 / T007 (webapp consumers vs launch paths) - different files.
- T018 / T019 (command references vs structural prose) - can run while T016's gate is in flight.

---

## Implementation Strategy

**MVP**: User Story 1 alone is shippable and valuable - it frees the `l7r` prefix for ANY second
portion, not just `/diagram`. If the feature had to stop there, nothing would be broken and the
capability would exist.

**Incremental delivery**: each landing commits and syncs to main separately. Three sibling diagram
sessions are live; a repo-wide textual diff held open for the length of all three landings is the
single most likely source of conflict pain.

**Not a delegated feature**: every task is executed in-session. No subagent output to spot-check,
and no `settlement-review` pass - a change that cannot alter output has a mechanical oracle
(feature 118's precedent).

## Notes

- The byte-identity sweep is the whole safety argument. If it ever diffs, the correct response is to
  diagnose the difference, not to re-baseline.
- `make done` reports all failures together - fix everything it lists, then re-run once.
- Background the gates and act on the completion notification; never poll.

# Tasks: the `land/` package

All tasks complete. Each line records what was DONE and the verification that was actually observed,
not what was intended - a checkbox ticked without a measurement behind it is the thing this file
exists to prevent.

## Phase 0 - baseline (before any edit)

- [x] **T001** Sync the clone in and allocate the spec number from main's state.
      *Observed*: highest `specs/NNN` was 119, so 120. Main moved again mid-feature (`0ce5071` ->
      `56f6dfb`, a peer's `waterfields/frame.py` change), which invalidated a first baseline and
      forced T003/T004 to be re-taken. Recorded in research.md R8.
- [x] **T002** Measure clause 12 so the "function size" half of the request is answered with data.
      *Observed*: worst member `near_ring_paddy` at 126 logical statements against a "suspect" line
      of a few hundred. **No function is decomposed.** Table in research.md R2.
- [x] **T003** Gate baseline, **in the clone** at `56f6dfb`.
      *Observed*: `gate green`, coverage TOTAL 95%, 450 missed lines.
- [x] **T004** Byte-identity baseline, **in a scratch copy**, `--no-cache --frozen-ok`.
      *Observed*: REGENERATED 28, CACHED 0, **893 artifacts** hashed.

## Phase 1 - design

- [x] **T005** Decide the partition axis. *Observed*: residue bucket, not a chain - four subjects
      with one directional edge between them (research.md R1). Axis is SUBJECT.
- [x] **T006** Census the relocation candidates' callees. *Observed*: 4 of 4 callees already in
      `homestead_parts.py` (research.md R3). Relocation chosen over a 27-line submodule.
- [x] **T007** Decide `surface_water_dist`'s home and price the alternative. *Observed*: `wet.py`;
      `_geom/` declined with reasons recorded in spec.md Out of Scope (research.md R4).
- [x] **T008** Write the partition member by member with measured spans. -> data-model.md
- [x] **T009** Write the surface contract C1-C4. -> contracts/surface.md

## Phase 2 - execution

- [x] **T010** Write the transformer, with refusals for every way the partition can be wrong.
      -> [split_land.py](split_land.py). Three novel hazards handled: the module-level TAIL, the
      out-of-package relocation (relative-import rewrite applied to `land/` blocks ONLY), and one
      asserted comment REPOINT.
- [x] **T011** Run it; prune headers; delete `land.py`; clear bytecode.
      *Observed*: 4 modules + `__init__.py` written, 3 members appended to `homestead_parts.py`,
      31 unused imports pruned, `land.py` `git rm`'d.
- [x] **T012** Cheap linters. *Observed*: `ruff format --check` 200 files formatted, `ruff check`
      all passed (after one auto-fixed import-order nit), `mypy --strict` clean on **118** source
      files (up from 114).
- [x] **T013** Comment conservation. *Observed*: **158 old, 158 new**, delta 0 in
      `homestead_parts.py`. Nothing lost.
- [x] **T014** Add the four surface guards to `tests/settlement/test_land.py`.
- [x] **T015** **Prove each guard FIRES** before trusting it. *Observed*, one sabotage each:
      dropping `NearRingMixin` from the bases fails C1; a duplicate `toe_band` fails C2; an
      `_attach_grove` stub in `cover.py` fails C3; removing the re-export fails C4 at collection.
      All four restored and green afterwards.
- [x] **T016** Whole affected test files (NOT a `-k` subset).
      *Observed*: `tests/settlement/ tests/hamletgen/ tests/check_village/` -> **2070 passed in
      64.62s**.
- [x] **T017** The byte-identity oracle.
      *Observed*: REGENERATED 28, CACHED 0, 893 = 893, **empty diff - BYTE-IDENTICAL**.
- [x] **T018** Full gate, backgrounded, not polled.
      *Observed*: `gate green`, TOTAL 95%, **450 missed lines - identical to baseline**. Per-module:
      `dikes.py` 100%, `wet.py` 100%, `nearring.py` 100%, `cover.py` 99%, `__init__.py` 100%,
      `homestead_parts.py` 99%. `SETTLEMENT_COV_FLOOR` unchanged at 94.
- [x] **T019** Confirm the gencache SEES the new package (an expectation converted to a check).
      *Observed*: `CACHED` -> perturb a literal in `land/cover.py` -> `REGENERATED` -> revert ->
      `REGENERATED`. The dependency walk reaches `settlement/land/*.py`.
- [x] **T020** Confirm `pool/` is clean. *Observed*: `git status --short pool` empty.

## Phase 3 - documentation

- [x] **T021** `settlement/land/CLAUDE.md` - the "look here when" index, plus the three things worth
      knowing before editing and the monkeypatch-path change.
- [x] **T022** `settlement/CLAUDE.md` - the `land.py` row becomes a `land/` package row; the
      `homestead_parts.py` row records the three arrivals.
- [x] **T023** `settlement/civic_grounds/CLAUDE.md` - its historical note said *"Only `land.py` is
      still whole"*, which this feature makes false. Updated, with the preserved-as-written
      paragraph above it left alone.
- [x] **T024** Sweep every remaining `settlement/land.py` reference in the skill's docs and comments
      to the right submodule. An index that lies is worse than no index.
- [x] **T025** Record the accepted limitations and the declined alternatives (spec.md Out of Scope),
      per the CLAUDE.md rule added 2026-08-17.

## Phase 4 - ship

- [x] **T026** Commit in the clone and run `scripts/sync-with-main.sh done`.

## Phase 5 - the base moved the file (unplanned; see research.md R9)

The stop-work ritual's pull brought in feature 119's second half, which relocated the whole engine
to `l7r/diagram/`. `land.py` was therefore RENAMED on main and DELETED here, which git correctly
refused to auto-resolve.

- [x] **T027** Diff the two blobs before choosing a resolution.
      *Observed*: main's `l7r/diagram/settlement/land.py` differs from the file this feature split by
      exactly **three lines**, all the relocation's `from waterfields import X` ->
      `from l7r.diagram.waterfields import X` rewrite. That turned a feared redo into a move.
- [x] **T028** Resolve: drop main's `land.py`, `git mv` the package to
      `l7r/diagram/settlement/land/`, apply the three-line rewrite (2 in `dikes.py`, 1 in
      `nearring.py`), delete the emptied old `settlement/` tree.
      *Observed*: the package's own relative imports needed nothing - `land/` sits at the same depth
      under `settlement/` either way, so only ABSOLUTE imports moved.
- [x] **T029** Repoint the guard-test imports this feature ADDED. Auto-merge follows renames for
      text that MOVED, never for text that is new, so all four still named the old module path.
      *Observed*: `from settlement.land import ...` x2, `from settlement.homestead_parts import ...`,
      and the `import settlement.land` in C4 -> all re-rooted at `l7r.diagram.settlement`.
- [x] **T030** Ruff read the plain `import l7r.diagram.settlement.land` as unused and deleted it.
      Rewritten to `importlib.import_module` so the linter has nothing to remove - the idiom
      `tests/*/test_surface.py` already uses.
- [x] **T033** **CORRECTION - the claim attached to T030 was wrong, and the correction is the
      finding.** T030 originally recorded that ruff's deletion left C4 resolving `settlement.land`
      through a side effect and therefore "silently weakened" it. That was reasoning offered as a
      result, and the GM asked the right question: was the underlying cause fixed, or just this
      instance? Measuring it answered neither - it dissolved the premise. All four combinations, run
      2026-08-17:

      | variant | clean | `land/__init__` drops the re-export | `surface_water_dist` moves out of `land/` |
      |---|---|---|---|
      | ruff-stripped | passed | error | failed |
      | `importlib` | passed | error | failed |

      **Identical teeth.** `settlement.land` is bound either way, because `core.py` does
      `from .land import LandMixin` - so the stripped assertion reached the same object by the same
      route. There was no weakening and nothing to fix. The `importlib` form stays because it is the
      established idiom and stops the F401 churn, not because it is stronger.

      The transferable lesson is the one this skill's CLAUDE.md already states under "A DIAGNOSTIC
      that restates what it observes will lie to you": **print the value and its provenance from ONE
      expression, or do not print the provenance at all.** A plausible mechanism written up as an
      observed one is a wrong answer wearing the costume of a measurement - and it went into a
      commit message and a spec doc before anyone ran it. Cost here was small (the guard was fine
      all along); the habit is what matters.
- [x] **T034** Census the GENERAL category the wrong claim was pointing at - a linter removing a
      genuinely load-bearing side-effect import - since that risk is real even though this was not
      an instance of it. *Observed*: the only side-effect imports in the skill are three lines in
      `hamletgen/consts.py`, already carrying `# noqa: F401` and the `X as X` re-export idiom; every
      package `__init__.py` where re-export IS the mechanism has a per-file `F401`/`F403` ignore in
      `pyproject.toml`; and the re-export surfaces are held by DERIVED-census guards
      (`tests/*/test_surface.py`, `pkgutil.iter_modules` + `import_module`) rather than by import
      statements a linter can touch. So the structural answer was already in place from feature 027,
      and no new mechanism is needed.
- [x] **T031** Re-verify EVERYTHING against the new base. A byte-identity oracle does not survive a
      base change, so both halves were re-taken at `origin/main` (`801dbd4`) via
      `git worktree add --detach` - the documented alternative to stashing, and the right tool for
      "give me a clean copy of another commit" too.
- [x] **T032** Smoke-check the composed surface after the move: all 14 pre-split members reachable
      on `Settlement`, `LandMixin` bases in order, `surface_water_dist` importable.

## Not done, deliberately

- **No `settlement-review` pass.** A byte-identical pool has no visual residue to judge; the maps
  are the same files. Reasoning in research.md R7, precedent in feature 118.
- **No function decomposed.** See T002.
- **No `pasture` move, no `surface_water_dist` -> `_geom/` move.** Both priced and declined in
  spec.md.
- **`migration-plan.md` status table untouched** - that table tracks hand-authored maps converting to
  scripted generation. This feature converts no map.

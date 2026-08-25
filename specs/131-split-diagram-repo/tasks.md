# Tasks: The Diagram Skill Becomes Its Own Repository

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

> [!IMPORTANT]
> **NOT STARTED.** Waits for the GM's "go" AND a quiet point: no other session holds an unpushed
> clone with diagram changes (T004 asks). Do NOT begin the real extraction (Phase 4) until the
> rehearsal (Phase 3) has passed every check. **Tick as you go** - a task is ticked when its
> verification passed.

## Phase 1: Setup and baseline

- [x] T001 Baseline in gm-assistant: last green `make done` in the diagram skill - record test count, wall-clock, `make hooks-test` suite count, and the commit, under Baseline below (constitution XIII: the new repository must match exactly)
- [x] T002 [P] By-hand pass over the 46 keyword-matched specs (research R1): confirm each is a diagram feature; record any that is not (it stays) under Moved set below
- [x] T003 [P] Enumerate the reference sweep: `grep -rn 'gm-assistant/.claude/skills/diagram\|/gm-assistant' .claude/settings.json scripts container-scripts docs CLAUDE.md .claude/skills/diagram/Makefile` plus the memory directory; classify each hit LIVE (must change) or HISTORICAL (left alone); record the list under Sweep below
- [ ] T004 **GM**: confirm no other session holds unpushed diagram work; create the GitHub repository (name per Assumptions, or say otherwise); generate a fine-grained PAT scoped to it (Contents rw); create the `main` ruleset (block force pushes, restrict deletions)

## Phase 2: Prepare the pieces (all in the clone, nothing pushed)

- [ ] T005 Write the new repository's CLAUDE.md: one project, the diagram loop, the command map, the session-clone rules with the new root, numbering continues from 132, the constitution as it stands - by editing the current one down, not from scratch
- [ ] T006 Write gm-assistant's post-split CLAUDE.md: diagram loop removed, `/diagram` listed as moved with the URL, the retained hooks table, the spec-number claim protocol unchanged
- [x] T007 Derive roots from git where cheap (research R4, plan note 3): `sync-with-main.sh`, `clone-sync-hooks.sh`; the diagram Makefile `guard` target (guard file - `GUARD_EDIT_OK` with the reason; its test companion updated). **FIRES**: the guard still refuses a run from the new repository's main tree; **STAYS QUIET**: a clone under the new root passes
- [ ] T008 `webapp/Makefile` gains the `hooks-test` phase (copied from the diagram Makefile) so gm-assistant's retained guards are RUN (FR-002); the four repository-wide guards (`gate-stamp.py`, `review-gate.sh`, `gate-hooks.sh`, `guard-file-hooks.sh`) trimmed to each repository's areas per FR-001's table, companions updated; `.claude/agents/` split per the table. `.claude/settings.json` for the new repository: check in rehearsal whether `$CLAUDE_PROJECT_DIR` resolves in hook commands; if yes use it, else the new absolute root. gm-assistant's `settings.json`: drop ONLY the diagram-only hooks (make-only, guard-file, gate); every COPY-TO-BOTH item in FR-001's table stays in gm-assistant untouched (`.specify/`, `docs/`, `container-scripts/`, `ruff.toml`, the content hooks)
- [ ] T009 `docs/session-clones.md`, `docs/container.md`, `scripts/launch-container.sh`, `container-scripts/append-system-prompt.md`: the second mount, the new root, the pointer in each direction
- [ ] T010 Feature 130's spec, plan and tasks: the route/delta section shrinks to "engine code vs docs" (the whole repository is the diagram now); record the change in its Review history as a consequence of 131, not a new request
- [ ] T011 Features 129 and 130: `**Blocked by**: 131-split-diagram-repo` in the spec header and a `T000` task "verify 131 landed: this directory is in the new repository and `make done` is green there" at the top of `tasks.md`

## Phase 3: Rehearsal (FR-011) - the whole procedure on a throwaway

- [ ] T012 Fresh clone to `/tmp/split-rehearsal`; `git filter-repo` with the path list from R1/T002; record the resulting commit count and repository size
- [ ] T013 In the rehearsal repository: apply T005/T007/T008/T009; `container-scripts/setup-dev-env.sh --check`; `make done` and `make hooks-test` in a clone under its `.clones/` - counts equal T001 (SC-001)
- [ ] T014 `git log --follow` on ten engine files chosen by `shuf` - full history present (SC-002); record the ten
- [ ] T015 Feature-127 quickstart in the rehearsal repository: every refusal reproduces (SC-005)
- [ ] T016 Rehearse the gm-assistant side on a second throwaway clone: the removal commit, the retained scripts, `webapp/make done` green, the retained hooks fire and the diagram-only ones are absent (SC-003)
- [ ] T017 Reference sweep grep in both rehearsal trees: zero LIVE hits (SC-004); record the count of HISTORICAL hits left alone
- [ ] T018 Discard both rehearsal trees; record under Rehearsal below that every check passed, with the numbers (SC-006)

## Phase 4: The real extraction (plan note 2 - removal LAST)

- [ ] T019 Fresh clone → `filter-repo` with the SAME path list → add the new remote → push `main` (the ruleset from T004 is already on it, so this is the first and last non-ff-free push)
- [ ] T020 Clone the new repository into the container at the new mount; run T013-T015 for real; record the numbers
- [ ] T021 Repoint CodeBuild: `GITHUB_REPO` on both projects (session's key suffices, R7); the GM pastes the new PAT into the existing secret (revoking the old one is optional housekeeping)
- [ ] T022 Copy the 32 diagram memory notes and their index lines into the new path's memory directory (R6); add a note in gm-assistant's memory saying where the diagram went
- [ ] T023 gm-assistant removal commit: delete ONLY the MOVE items of FR-001's table (the skill, the 47 spec directories, `make-only-hooks.sh`, `_hookmatch.py` and their companion, the three diagram review agents), keep every COPY and STAY item, apply T006/T008/T009; `webapp/make done` green; push through the ritual
- [ ] T024 The `Blocked by` lines and `T000` tasks (T011) land in the NEW repository, where 129 and 130 now live
- [ ] T025 Reference sweep grep across both real repositories and both memory directories: zero LIVE hits (SC-004)

## Phase 5: Close

- [ ] T026 The new repository's `timings.md`: a dated block "131 - first gate in the new repository" with T020's numbers beside T001's
- [ ] T027 Report to the GM: the URL, the assumptions made (name; copies vs shared; renders; numbering 132 / 200; the rehearsal), the three things that changed for them (two mounts; sessions for diagram work open in the new repository; feature = repo + number), and that 129/130 are now unblocked
- [ ] T028 Audit `dev/bypass-log/` for entries added during this feature (expected: none)

---

## Baseline (T001)

| | value |
|---|---|
| commit | `4ecdcedd` (clone tip at baseline; main `a3043335` + 129's header) |
| `make done` tests / wall-clock | **3,464 passed, 2 failed** (`test_every_live_pool_png_matches_its_own_svg_viewbox`, `test_crown_fills_covers_every_recorded_crown` - both the constitution's known gitignored-artifact gap: a fresh clone has no pool renders; NOT regressions), test phase 223.6 s |
| `make hooks-test` suites | 12 |

## Moved set (T002) - exceptions to the keyword census

None. All 46 keyword matches are diagram features (119, the `l7r` namespace, is the diagram's - the webapp's guard test stays in `webapp/`). The five that stay: 001, 002, 003, 004, 011. Plus 131 itself moves: 47 directories.

## Sweep (T003) - LIVE hits

85 `/gm-assistant` references in 24 files at recon; the rehearsal sweep found the ones the recon missed: `settlement/_geom/base.py` (the engine's own main-tree guard), `pipeline/render_cache.py` (`--main-repo` default), `buildings.md` (a link), `setup-dev-env.sh` (prose + the `claude()` wrapper path), `docs/session-clones.md` (two command lines). All derived or repointed in commit `f8b43e95`. HISTORICAL (left alone): every `specs/*` artifact, `dev/*-log/`, test fixtures that use the path as a synthetic string, comments describing the 2026-07 incidents, the constitution's own prose.

## Rehearsal (T018)

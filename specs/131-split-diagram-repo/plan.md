# Implementation Plan: The Diagram Skill Becomes Its Own Repository

**Spec**: [spec.md](spec.md) | **Request**: [gm-request.md](gm-request.md) - verbatim, the authority.
**Status**: PLANNED, NOT IMPLEMENTED - waits for the GM's "go" and for a quiet point in the hamlet
work. **Blocks** 129 and 130.

## Summary

Extract `.claude/skills/diagram/`, the 46 diagram spec-kit features, and the repository-level
machinery (`scripts/`, `.specify/`, `container-scripts/`, `docs/`, `ruff.toml`, CLAUDE.md) into a
new GitHub repository with full history via `git filter-repo`, keeping the internal layout
identical so the engine and every feature-127 guard are untouched. Remove only the MOVE items from
gm-assistant in one commit; everything its remaining content, spec-kit or the container uses is
COPIED TO BOTH (the constitution, the spec-kit scripts, the content hooks, the docs, `ruff.toml`). Sweep
every live reference to the old location; repoint CodeBuild; copy the diagram memory notes; mark
129 and 130 `Blocked by: 131`. Rehearse the whole thing on a throwaway copy first, because the real
extraction is the one step that is hard to walk back.

## Technical Context

**Language/Version**: Bash (the extraction, the sweep); `git-filter-repo` (Python, installed);
no new Python of our own.

**Primary Dependencies**: `git-filter-repo` 2.x; a new GitHub repository (GM creates); a new
fine-grained PAT and `main` ruleset for it (GM creates).

**Storage**: none new. The new repository's `.git`; the new memory directory.

**Testing**: the existing suites ARE the test - `make done` and `make hooks-test` green in the new
repository with the same counts (SC-001); `webapp/make done` green in gm-assistant (SC-003); the
feature-127 quickstart re-run (SC-005); a grep-based reference sweep (SC-004).

**Target Platform**: the dev container, with a second mount.

**Project Type**: repository surgery.

**Performance Goals**: none. **Constraints**: no engine change, no pool change, no gate change
(FR-012); rehearsal before the real run (FR-011).

**Scale/Scope**: 1 new repository; 1 extraction; 1 removal commit; ~6 files with absolute-path
roots; 2 CLAUDE.md rewrites; 32 memory notes copied; 2 spec headers marked; 2 CodeBuild projects
repointed; 3 GM actions (repo, token, ruleset).

**Single-artifact target**: not applicable - no generator change. Its analogue is the REHEARSAL:
the whole procedure proven on a throwaway copy before it runs for real.

**Every step is two steps**: rehearsal, then the real extraction - and each verification runs in
both.

## Performance bookends

Not applicable, stated rather than skipped: no generator is touched. `make done` wall-clock is
recorded before and after in the new repository's `timings.md` only to prove nothing slowed (SC-001).

## Constitution Check

- **I / II / III / VII / VIII / IX / XI**: no UI, no pool data, no generated content, no prose, no
  setting content, no kanji. N/A.
- **IV. One Canonical Home for GM Source**: the diagram research quotes no SOURCE blocks; the
  setting notes stay in the GM's `l7r` repo. N/A.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: no SOURCE block touched; history rewriting
  by `filter-repo` drops commits, never edits content.
- **VI. Verify Before Reporting Done**: every task names its check; the rehearsal is the proof
  before the real run.
- **X. Python Discipline (NON-NEGOTIABLE)**: no Python written. The moved suites keep their
  coverage gates.
- **XII. Historical Grounding (NON-NEGOTIABLE)**: no claim about the world. N/A.
- **XIII. No Known Regressions (NON-NEGOTIABLE)**: the baseline is the last green gate in
  gm-assistant (count + wall-clock, T001); the new repository must match it exactly. A test that
  passed in gm-assistant and fails in the new repository is a regression of this feature.
- **XIV. Fix Defects Where You Find Them**: the sweep will find stale absolute paths (R4); fixed by
  deriving roots from git where cheap.
- **XV. Keep Going**: three GM actions are planned stops (repository, token, ruleset), listed up
  front so they can be done before the session starts.
- **XVI. Build What Was Asked (NON-NEGOTIABLE)**: the six session's-call decisions are flagged in
  the spec and reviewed by `spec-fidelity`; none is widened during implementation.
- **XVII. A README Is Written By A Human**: the new repository gets NO README from the session; the
  GM writes one (or none). CLAUDE.md is the session's.
- **XVIII. A Guard Ships With Its Test**: no new guard; every moved guard's companion moves with it,
  and `make hooks-test` in both repositories proves the count.

**Gate: PASS.**

## Project Structure

```
NEW  l7r-diagram/                        (name: session's assumption)
├── .claude/skills/diagram/              identical, with history
├── .claude/settings.json                hooks repointed to the new root
├── .specify/                            COPY (constitution as it stands)
├── scripts/                             the diagram-only guards MOVE; the content hooks + ritual COPY
├── container-scripts/                   COPY + the new mount
├── docs/                                COPY, each trimmed to this repository's loop
├── specs/0NN..131                       the 46 diagram features + this one
├── ruff.toml, CLAUDE.md                 CLAUDE.md rewritten for one project

gm-assistant/                            after the removal commit
├── .claude/skills/                      diagram/ gone; /diagram listed as moved
├── scripts/                             content-skill hooks + ritual + companions kept; diagram-only guards removed
├── .specify/                            kept (constitution as it stands)
├── docs/                                all kept; iteration-loop.md / session-clones.md / container.md trimmed of the diagram loop
├── ruff.toml, container-scripts/        kept
├── specs/001,002,003,004,011            the five that stay
└── CLAUDE.md                            diagram loop removed; pointer to the new repository
```

## Design notes the tasks depend on

1. **Rehearsal = the real procedure on `/tmp/split-rehearsal`**, from a fresh clone, through every
   verification, then discarded. Only then the real run, from a fresh clone, pushed to the GM's new
   repository.
2. **Order of the real run**: extract → verify in the new repository → push → repoint CodeBuild →
   copy memory → THEN the gm-assistant removal commit → mark 129/130 → sweep. The removal is last
   so that at no moment does the diagram exist nowhere.
3. **Roots derived from git where cheap** (R4): `sync-with-main.sh` and `clone-sync-hooks.sh` take
   `MAIN` from `git rev-parse --show-toplevel` of the clone's parent; `settings.json` hook paths
   become `$CLAUDE_PROJECT_DIR/scripts/...` if the harness supports it (checked in rehearsal), else
   the new absolute root.
4. **The Makefile `guard` target** hardcodes `/gm-assistant/.clones/*`; it is a guard file, so the
   edit carries `GUARD_EDIT_OK` with the reason, and its test companion changes with it.
5. **Feature numbering** (spec Assumptions, session's call, GM confirms at "go"): the new
   repository continues from 132; gm-assistant restarts at 200, so numbers stay globally unique and
   every existing "feature NNN" reference stays unambiguous. CLAUDE.md says so in both.

## Complexity Tracking

| concern | why it is accepted |
|---|---|
| History rewriting | The GM asked for the skill to become its own repository; a repository without its history would lose 1,100 commits of recorded decisions this project runs on. `filter-repo` on a fresh clone rewrites nothing in gm-assistant. |
| Two copies of the content-skill hooks, the constitution, spec-kit and the docs | Session's call, flagged: the two projects' rules diverge on purpose; a shared package re-couples them. |
| A rehearsal before the real run (FR-011) | Session's call, flagged: the only one-way step is other sessions starting from the new repository; a throwaway run is the cheapest proof the path list is complete before that. |
| Three GM actions | Repository creation, a repository-scoped token, and a ruleset cannot be done with any credential the session holds, by design. |

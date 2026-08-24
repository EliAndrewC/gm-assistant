# Implementation Plan: Every Expensive Path Runs Through a Gated Make Target

**Spec**: [spec.md](spec.md) - APPROVED, `spec-fidelity` verdict FAITHFUL at round 3.
**Request**: [gm-request.md](gm-request.md) - verbatim, the authority. Not to be edited.

## Summary

Four guard layers make every operation reachable only through this project's make. Layer 1 (a
`PreToolUse` hook on command shape) is load-bearing because it runs in the harness, outside the
guarded process, before the command executes. Layer 2 (a process-tree determination) catches shapes
layer 1 does not anticipate, including in-process calls. Layer 3 guards the guard files. Layer 4 is
tests proving each layer fires AND stays quiet on the legitimate path.

Nothing in map geometry changes. No failing seed is addressed.

## Technical Context

**Language/Version**: Python 3.14 (determination + tests), Bash (hooks, following the five existing
`scripts/*-hooks.sh`), GNU Make.

**Primary Dependencies**: none new. `/proc` for ancestry; `json` for hook payloads; pytest.

**Storage**: `dev/bypass-log.jsonl` (exists, gains `outcome`).

**Testing**: pytest for the Python determination (mypy --strict, 100% coverage per Principle X);
`scripts/test-*-hooks.sh` for the hooks, following the established convention - **every existing hook
script already has a `test-` companion, and the two new ones get theirs.**

**Target Platform**: Linux container. `/proc` assumed; no portability claimed (spec Assumptions).

**Project Type**: developer tooling for this repo.

**Performance Goals**: the determination must not appear in any hot path. It is computed ONCE per
process and cached; the per-operation cost is one dict lookup. See research R4.

**Constraints**: must not slow the reference check measurably (SC-002); must not break the stop-work
ritual (SC-004).

**Scale/Scope**: 18 CLI entry points, 13 existing make targets, 5 existing hook scripts, 1 script line
in `sync-with-main.sh`.

**Single-artifact target**: **not applicable, and this is a real determination rather than a skip.**
The constitution's single-artifact rule governs GENERATOR changes, where the artifact is a map. This
feature changes no generator and draws nothing. Its analogue - the one thing proven first before
anything widens - is `make reference` remaining clean and prompt-free (SC-002), which is checked at
every step below.

**Every step is two steps.** The reference-settlement/pool split also governs generator work rather
than this. Its analogue here is enforced instead: **every guard task is two tasks - prove it FIRES,
and prove it does NOT fire on the legitimate path** (FR-015, FR-016). A task list carrying only the
first is not finished being planned.

## Performance bookends

**Not applicable, stated rather than skipped.** The bookends measure generator speed across seeds;
this feature does not touch the generator. The performance risk it does carry is different and is
handled at research R4: a determination placed in a hot path would be a serious regression, so it is
computed once per process and cached, and a test asserts the cached call count.

One number IS taken, because SC-002 demands it: `make reference` wall-clock before and after, which
must not move outside noise.

## Constitution Check

- **I. Accessibility-First Viewports**: no UI surface. N/A.
- **II. Bold, Intentional Design**: no UI. N/A. (Refusal messages follow the existing hook voice:
  say what was blocked, why, and the one command to run instead.)
- **III. Pool Data Conventions**: no pool data added or modified. N/A.
- **IV. One Canonical Home for GM Source**: no GM source moved. `gm-request.md` is a verbatim
  transcript inside the feature directory, not a relocation of `l7r.md`. N/A.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: no `SOURCE` block touched. **`gm-request.md`
  is treated as equivalent** - written before the spec, quoted from, never edited.
- **VI. Verify Before Reporting Done**: verification is listed per task; the gate runs once at the
  end; `make reference` is the cheap check throughout. **This feature's own subject is the ordering
  this principle describes**, so getting it wrong is self-demonstrating.
- **VII. De-Localized Generation by Default**: nothing generated. N/A.
- **VIII. Direct Voice Over Framing Distance**: no in-world prose. N/A.
- **IX. Setting Integration**: no setting content. N/A.
- **X. Python Discipline (NON-NEGOTIABLE)**: new Python is `mypy --strict` and 100% covered. The
  determination module is small and single-purpose; no file approaches the ~1,000-line split bar.
- **XI. Japanese Authenticity**: no kanji. N/A.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: no historical claim. The research ladder's
  analogue - measure before you assert - IS honored: every mechanism claim in research.md is backed
  by a run, not by reasoning. Two of them contradicted my prior assumptions (R1, R3).
- **XIII. No Known Regressions (NON-NEGOTIABLE)**: baseline taken in a detached worktree before the
  first edit (T001). The specific regression risk here is a guard firing on legitimate work, which
  FR-016 tests cover directly.
- **XIV. Fix Defects Where You Find Them (NON-NEGOTIABLE)**: expected to surface ungated paths nobody
  had noticed; those are fixed in this feature, since they ARE this feature.
- **XV. Keep Going (NON-NEGOTIABLE)**: no stopping points planned. If a guard proves unbuildable, the
  spec's SC-006 clause already dictates the outcome - record it as a residual bypass in Assumptions
  and exclude it from SC-006 explicitly, rather than leaving a silent hole.
- **XVI. Build What Was Asked (NON-NEGOTIABLE)**: the spec passed independent fidelity review at
  round 3 after two carve-outs of mine were caught and removed. **Any exception discovered during
  implementation goes back to `spec-fidelity` in Mode 1 before it is written**, and this plan
  introduces none.

**Gate: PASS.** No violation requires justification; every N/A above is argued rather than asserted.

## Project Structure

### Documentation (this feature)

```
specs/127-gated-make-commands/
├── gm-request.md      # verbatim GM request - the authority, never edited
├── spec.md            # APPROVED (FAITHFUL, round 3)
├── plan.md            # this file
├── research.md        # measured mechanism findings
├── data-model.md      # the operation registry and the audit entry
├── quickstart.md      # how to verify the whole thing by hand
├── checklists/
└── tasks.md
```

### Source Code

```
.claude/skills/diagram/
├── Makefile                              # + a target per operation, + render-sync
└── l7r/diagram/
    └── _invocation.py                    # NEW - the determination (layer 2)
        tests/test_invocation.py          # NEW - FR-015 + FR-016 for layer 2
    tests/conftest.py                     # + assert the suite itself is under make

scripts/
├── make-only-hooks.sh                    # NEW - layer 1 (command shape)
├── test-make-only-hooks.sh               # NEW - its companion, per convention
├── guard-file-hooks.sh                   # NEW - layer 3 (edits to guard files)
├── test-guard-file-hooks.sh              # NEW - its companion
└── sync-with-main.sh                     # line 138: bare python3 -m -> make target

.claude/settings.json                     # wire the two new hooks
```

## Design

### Layer 2: the determination (`_invocation.py`)

One public function. Raises rather than returns, because a caller who forgets to check a boolean is
exactly the failure this feature exists to prevent:

```
assert_via_make(operation: str, target: str) -> None
```

The verdict is computed **once per process and cached** (research R4). Its logic:

1. Walk `/proc/<pid>/stat` PPid to PID 1, collecting `(comm, pid)`.
2. For each ancestor whose `comm` is `make` or `gmake`, read its `/proc/<pid>/cwd` and
   `/proc/<pid>/cmdline`.
3. Accept when that make's `cwd` is inside this repository AND its argv contains no `-f`/`--file`/
   `--makefile` naming a path outside the repository.
4. Otherwise refuse, naming `target`.

Deliberately NOT used: any environment variable. FR-003 forbids it, and the GM's reasoning is
recorded in `gm-request.md`.

**Placement rule, which is the part most likely to be got wrong later**: `assert_via_make` is called
at the TOP of an operation, never inside a loop, never in library helpers. A comment at the point of
call says so, per the project's ordering-comment rule.

### Layer 1: `make-only-hooks.sh`

`PreToolUse` on `Bash`. Blocks and names the make target:

| pattern | why |
|---|---|
| `python3 -m l7r.diagram.<entry point>` | tier 1, the observed failure |
| `pytest` / `python -m pytest` | tier 1, and the suite is the 4.5-minute cost |
| `make -f` / `--file` / `--makefile` | tier 4, forging a makefile |
| inline `REF_WHY=` / `REF_OK=` before a command | tier 2, the observed override |

Must NOT block: any ordinary `make <target>`, any read of a source file, anything under `scripts/`.

### Layer 3: `guard-file-hooks.sh`

`PreToolUse` on `Edit|Write|NotebookEdit`, matching `Makefile`, `scripts/*-hooks.sh`, and
`.claude/settings.json`. **Not `.claude/agents/*.md`** - removed at round 1 of the fidelity review as
unrequested, and because it would obstruct the project's own procedure for improving review subagents.

### Layer 4: the tests

Two per guard, per FR-015/FR-016. The FR-015 direction is the one that is easy to fake, so the bar is
the project's own subagent-check rule: **the test must FAIL when the guard is removed.** T0xx verifies
that by removing each guard in a scratch copy and observing red.

## Complexity Tracking

| concern | why it is accepted |
|---|---|
| Two new hook scripts rather than extending an existing one | Each existing hook is single-purpose with its own test companion; folding four new patterns into `gate-hooks.sh` would make one script carry two unrelated jobs. Follows the established structure. |
| A determination that reads `/proc` | The only mechanism that satisfies FR-003's "MUST NOT depend on any value a caller can set". Measured to work through every nesting shape this repo uses (research R1). |
| `render-sync` gets a target exempt from reference-first ordering | FR-009a, adjudicated FAITHFUL at round 3. It is exempt from an ORDERING rule, not from a guard. |

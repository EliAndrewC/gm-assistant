# Research: mechanism findings, all measured

**Rule followed here**: every claim below was produced by running something, not by reasoning about
what should happen. Two of the five contradicted my prior assumption, and both would have shipped as
design errors (R1's pool nesting, R3's webapp import).

---

## R1 - Process-tree ancestry detects make through every nesting shape this repo uses

**Decision**: walk `/proc/<pid>/stat` PPid to PID 1 and accept if `make` appears anywhere.

**Measured** 2026-08-24, by probe:

| invocation | chain | make seen |
|---|---|---|
| `make` -> python | `python3 <- make <- bash` | yes |
| `make` -> `sh -c` -> python | `python3 <- sh <- make <- bash` | yes |
| `multiprocessing.Pool` children | `python3 <- python3 <- python3 <- make <- bash` | yes |
| bare `python3` | `python3 <- bash <- claude` | no (correct) |

**Rationale**: make runs recipe lines through `/bin/sh -c`, so the immediate parent is `sh` and a
parent-only check would fail on every recipe. Two nesting shapes this repo actually uses - pytest-xdist
workers and `cohort()`'s fan-out - sit three levels down and are still detected.

**Alternatives considered**: parent-process-only (fails on every make recipe, since the parent is
`sh`); an environment variable exported by make (rejected by the GM in `gm-request.md`, because it is
spoofable by the operator this feature guards against, and FR-003 now forbids it).

---

## R2 - A naive ancestry check is defeated by a foreign makefile

**Decision**: also read the make process's `cwd` and its `-f`/`--file`/`--makefile` argument, and
accept only a make belonging to this repository.

**Measured**: `make -f /tmp/evil.mk` produced `python3 <- make <- bash` and PASSED a bare ancestry
check. This is the hole that turned "run it through make" into "run it through THIS project's make".

**Rationale**: without this, the guard is defeated by a two-line file, which is well inside the
workaround tier the GM wants closed.

**Alternatives considered**: matching on the makefile's content hash (brittle, and breaks legitimately
whenever the Makefile is edited); trusting `MAKEFILE_LIST` (an environment value, so FR-003 forbids it).

---

## R3 - Nothing outside the skill directory imports `l7r.diagram` at runtime

**Decision**: the determination may sit on the expensive OPERATIONS themselves, not only on CLI
entry points - which is what closes the in-process bypass (FR-008).

**Measured**: searched `webapp/` and `scripts/` for runtime imports of `l7r.diagram`; none. The only
mention is a docstring in `webapp/l7r/app.py` explaining why the `l7r` namespace is SHARED. The only
non-skill caller of an expensive operation is `sync-with-main.sh`, which runs
`l7r.diagram.pipeline.render_cache` as a module.

**Rationale**: round 1 of the spec asserted that the webapp imports the engine to render maps, and
used that to argue the guard must live on entry points only - which would have left
`python3 -c "import ...; generate(...)"` open, a bypass needing no git diff and readable as
diligence. The assertion came from a `CLAUDE.md` sentence describing why the namespace is shared,
i.e. a capability, not a caller. **A capability sentence is not a usage measurement**, and the
distinction cost a real hole in the spec until the fidelity reviewer forced the check.

**Consequence recorded in the spec's Assumptions**: if the webapp later grows a rendering path,
FR-008 must be revisited rather than quietly exempted.

---

## R4 - The determination must be computed once per process, not per call

**Decision**: cache the verdict in a module-level global; `assert_via_make` is called at the TOP of an
operation only, never in a loop or a library helper.

**Rationale**: this engine's entire performance history is one shape - *a per-candidate scan of
geometry that does not change during the scan* (`dev/performance.md`). A `/proc` walk is exactly that
shape if placed carelessly: reading several files per call, inside a placer loop, would be far more
expensive than anything it guards. The ancestry cannot change during a process's life, so caching is
correct rather than merely fast.

**Alternatives considered**: checking on every call (same defect class the project has fixed
repeatedly); checking only in `__main__` blocks (fails FR-008, leaves the in-process bypass open).

**Test obligation**: a test asserts the `/proc` walk happens once across repeated calls, so a later
refactor that drops the cache is caught rather than silently slow.

---

## R5 - The hook layer already intercepts what layer 3 needs

**Decision**: implement layer 3 as a `PreToolUse` hook on `Edit|Write|NotebookEdit`.

**Measured**: `.claude/settings.json` already registers `PreToolUse` on `Edit|Write|NotebookEdit`
(clone-sync, gate) and on `Bash` (no-poll, no-branch, gate). Five hook scripts exist, and **every one
has a `scripts/test-<name>-hooks.sh` companion** - a convention this feature follows rather than
invents.

**Rationale**: the hook runs in the harness, outside the guarded process, before the command executes.
That is why it is the load-bearing layer and the Python determination is defense in depth: the hook
costs zero time on a refusal, and it can see command SHAPES that no in-process check can (a bare
`pytest`, a foreign makefile).

**Alternatives considered**: implementing everything in Python (cannot see a command before it runs,
and cannot guard `pytest`, which is not our code).


---

## R6 - A detached-worktree baseline is invalid for tests that read gitignored artifacts

**Decision**: take the baseline in the worktree as Principle XIII requires, but VERIFY any failure
there against the clone before calling it pre-existing.

**Measured** 2026-08-24: the worktree gate reported 2 failed / 3420 passed. Both failures
(`test_every_live_pool_png_matches_its_own_svg_viewbox`,
`test_crown_fills_covers_every_recorded_crown`) pass in the clone on the same commit. The worktree
held 20 pool PNGs; the clone holds 28. Renders are gitignored, so `git worktree add` does not bring
them and the tests that read them fail for a reason that has nothing to do with the code.

**Rationale**: this cuts both ways and the dangerous direction is the quiet one. A spurious baseline
FAILURE is loud and gets investigated. A spurious baseline failure that later "passes" would read as
a fix nobody made - and worse, a test that only passes in the worktree would hide a real regression.

**Consequence**: a worktree baseline is a starting point, not a verdict. Every failure it reports is
checked against the clone before being called pre-existing.

**This probably belongs in the constitution rather than in one feature's research file**, since
Principle XIII mandates the worktree procedure for every feature and says nothing about this. Flagged
for the GM rather than edited in, because amending the constitution was not part of this feature's
request.


---

## R7 - A mutation test must assert its own mutation applied

**Decision**: every guard-removal check replaces text through an anchored operation that fails loudly
when the anchor is missing, never through a regex that can silently match nothing.

**Measured** 2026-08-24, during T034: a `sed -E` mutation of `guard-file-hooks.sh` did not match
(the real line has one space before `;;`, the pattern assumed two). The file was therefore unchanged,
the test suite passed 17/17, and the honest-looking conclusion was "removing this guard changes
nothing, so the guard is decoration". A `diff` against the original disproved it; re-run with a real
mutation, the same suite fails 7 of 17.

**Rationale**: the failure is silent and its output is indistinguishable from a real finding. Worse,
it is wrong in the expensive direction - it argues for DELETING a guard that works.

**Alternatives considered**: eyeballing the mutated file (does not scale and is what was skipped);
`diff`-then-run (works, and is what caught it, but relies on remembering to look). The anchored
replace is the version that cannot be forgotten, because it raises instead of proceeding.

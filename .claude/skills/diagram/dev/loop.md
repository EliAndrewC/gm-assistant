# The iteration loop: timings, sweeps, and what to run before the gate

**Load this file when:** You are about to run the gate or a pool sweep, you want the diagram-specific timing numbers, or you are deciding how much to re-run after a change.

Split out of [`../CLAUDE.md`](../CLAUDE.md) so it is not in every diagram session's
context. The text is verbatim; the short always-on version of each rule stays in the index.

## Gate and sweep timings (the motivating-artifact loop, concretely)

The root "iterate on the motivating artifact, sweep once at the end" rule has these diagram
numbers. A single map's regen + gate is ~1-7s; the heaviest LIVE maps are the scripted hamlets
(Sawada ~20s, Kashikawa ~16s solo CPU - `GEN_TIME_BUDGETS` says why that is inherent, not a bug).
The old heavy maps (Minami ~14.5s, Nagahara / Tango / Kikuta / Hoshizora ~10s after three
optimization passes) are FROZEN since 2026-08-16 and never regenerate - see "The legacy pool is
FROZEN" in [`pool.md`](pool.md):

    DIAGRAM_SKIP_RENDER=1 python3 pool/<type>/<map>.gen.py && python3 -m l7r.diagram.check_village pool/<type>/<map>.json

**...or let the CACHE skip the work entirely** (2026-08-08). `pipeline/regen.py` regenerates a map only if
something that map depends on actually changed, and prints `CACHED` or `REGENERATED` every time:

    python3 -m l7r.diagram.pipeline.regen pool/hamlets/sawada.gen.py              # ~20s cold, ~1s cached
    python3 -m l7r.diagram.pipeline.regen pool/*/*.gen.py                         # every LIVE map, fanned out (frozen legacy maps print FROZEN, skipped)
    python3 -m l7r.diagram.pipeline.regen --no-cache pool/hamlets/inashiro.gen.py # force the work

Multi-map runs fan out across worker processes (cpus minus 2; `--jobs 1` for serial), as do
`tools/cohort_audit.py` and `python3 -m l7r.diagram.hamletgen --batch`. The audit since 2026-08-15, when the
timings ledger showed the serial cohort was the biggest available win; the batch CLI since
2026-08-16, when a profile found that round had MISSED it - the fan-toe pond fix spent **17.3 of its
45.7 minutes** on two serial 24-seed rolls, ~11 min of it as critical-path idle (**526s -> 71s,
7.4x**, with all 24 verdicts identical, re-proven per differing seed against a serial roll on the
same code). `default_jobs` in `hamletgen/driver.py` is the one definition of the cpus-minus-2
courtesy; the audit imports it. Wall clock for a fanned-out sweep is bounded by its single slowest
map, so
per-map cost is what remains worth optimizing. Parallelism cannot change a verdict (each map is a
pure function of its spec; `gencache.store` publishes atomically), and the per-map output is
captured in the worker and printed in order, so a parallel run reads like a serial one.
(A whole-pool regen is an ITERATION convenience, never a pre-gate step: the gate verifies the pool
itself and render-sync regenerates main's renders from main's own tip - the 2026-08-16 rule, with
the evidence, is in [`docs/iteration-loop.md`](../../../../docs/iteration-loop.md).)

## The gate total is a BUDGET, not a score - and timings live in timings.md

**TIMINGS ARE TRACKED IN [`timings.md`](../timings.md), MEASURED BY `python3 -m l7r.diagram.tools.timings`** - one dated
block per run, each benchmark carrying its BREAKDOWN as well as its total, so a slow loop can be
attributed instead of merely noticed. Do not write fresh timings into prose here: this paragraph
used to say the full sweep was "~2 to 2.5 minutes" and was still saying it on 2026-08-15, when the
measured gate was past four. Nobody was wrong; nobody re-measured, and prose cannot tell you that.

Read the gate's own total as a BUDGET rather than a score - it carries every unit test in the skill
and grows as rules are added, for reasons unrelated to generator speed. **Score a perf change by A/B-ing the
ONE map against HEAD**, which is how both passes were measured.

(Measured 2026-07-25: it had drifted to 112-215s across six runs, well past
the "~1 minute" this file used to claim from 2026-07-20; indexing the two worst checks that same day
brought it back to 77s. Re-measure and update this number when it drifts again - a stale figure here
is what makes a session mis-plan its loop.) So run the red/green loop against the ONE map
(or fixture) that shows the defect, where cycles are near-free, and reserve the full sweep for AFTER
that map is green. The sweep is MANDATORY, though, whenever shared engine code changed
(the `settlement/` package, the `check_village/` package, the `waterfields/` package, a scripted engine): every LIVE
pool map is a downstream artifact of the engine, so the sweep is what proves "no other map
regressed" instead of hoping it. LIVE means the scripted maps only - the hand-authored pool is
FROZEN (see "The legacy pool is FROZEN" in [`pool.md`](pool.md)) and is deliberately allowed to go stale.
Anti-patterns on record: the scale-bar feature used the full suite as its FIRST check of an engine
change - a failure that would have surfaced in ~6s on one map surfaced 17 minutes in; the
swept-collar check (11m07s wall) is the feature the project-wide 78%-turn-latency profile was taken
from.

## NEVER re-run what `make done` just ran, and never run pytest without `-n auto`

The single biggest time sink ever measured on this skill (2026-07-25, a 69-minute feature profiled
from the session transcript): **13.2 minutes - 19% of the whole feature's wall clock - went to one
`python3 -m pytest tests/test_regressions.py` that `make done` had already run, in parallel, minutes
earlier.** Two compounding mistakes, both cheap to avoid:

- **`make done` runs `pytest -n auto`** (see the Makefile), which is ~7x faster than serial on this
  box: the 695-manifest regression replay is ~2 min under the gate and **13.4 min serial**. If you
  ever invoke pytest directly, pass `-n auto`. There is no reason to run it serially.
- **A green `make done` already covers `tests/test_regressions.py`, `tests/test_villages.py`, and every unit
  test.** Re-running any of them "to be sure" buys nothing - the gate is the proof. Re-run only what
  actually changed since the gate went green, and if that is markdown, re-run nothing (root
  CLAUDE.md, "docs-only diffs skip the gate").
- **And do not run a pytest BESIDE the running gate** - not merely wasteful, but a source of false
  RED. Both runs regenerate the same live maps in the same tree, and
  `test_the_real_pool_round_trips_through_the_cache` snapshots a manifest and reads it back: with a
  second writer mid-write it read `b''` and failed a gate that was otherwise clean (2026-08-16,
  feature 116 - cost one full 2-minute gate cycle). Determinism makes concurrent writers safe for
  the BYTES; it does not make them safe for a test that reads a file someone else is rewriting. Same
  rule the byte-identity sweep already carries in the other direction (specs/116 quickstart step 2).

## NEVER poll a backgrounded command - and it is now ENFORCED

Backgrounding the gate and then *watching* it is worse than running it in the foreground. Profile of
a 31-minute feature (2026-07-25): **10.9 minutes - 35% of the whole task - went to polling two gates
that had already finished.** The gates took 97s and 98s; the waits took 351s and 401s, both running
their full iteration budget because of this:

    for i in $(seq 1 80); do if ! pgrep -f "make done" >/dev/null 2>&1; then break; fi; command sleep 5; done

`pgrep -f "make done"` **matches its own shell** - the pattern is an argument of the very command
line being searched - so the `break` can never fire. And the loop was pointless anyway: a
backgrounded Bash command NOTIFIES you when it exits. Background the gate, spend the turn on the
docs or the commit message, and act on the notification.

[`scripts/no-poll-hooks.sh`](../../../../scripts/no-poll-hooks.sh) (tested by `test-no-poll-hooks.sh`)
now BLOCKS the pattern at PreToolUse: `pgrep -f` / `pkill -f` with a literal pattern, any loop
containing a `sleep`, and the `command sleep` / `/bin/sleep` / `env sleep` forms that exist only to
dodge the harness's own foreground-sleep guard. A genuine wait on EXTERNAL state (a server port)
passes by putting `POLL_OK` in the command with a note saying what it waits for. Same rationale as
the batching hook: "background the final gate" was already written down here, and the session
followed it and then blocked on the gate anyway.

**And keep the backgrounded command simple enough that its EXIT CODE is real.** Run it as
`cd <dir> && make done > <log> 2>&1` and nothing more. A wrapper ending in `; echo EXIT=$?` makes the
SHELL exit 0 no matter what make did, so the harness notifies "exit code 0" for a gate that FAILED -
which happened on 2026-07-27: the paddy-well gate was reported green, its log's own last line was
`EXIT=2`, and the three failures it hid were pointing at a real design error in the new rule rather
than a slip. The log's tail is the authority; the notification is a summary of the wrapper. Put the
`cd` inside the same command too - a timed-out call can leave the shell's cwd somewhere else, and the
next `make done` then runs where there is no Makefile (or, worse, somewhere it should not).

## Before the gate, run the WHOLE affected test file - not a `-k` subset

That same profile paid an extra gate round trip (98s plus two turns) for a failure a local run would
have caught: the change altered geometry an existing test depended on, and the pre-gate check was
`pytest -k torii`, which did not include that test. The whole files for the modules you touched cost
~45s and reach every test the change can. So: cheap linters, then whole files, then the gate ONCE.

    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy
    python3 -m pytest tests/settlement/ tests/check_village/ -q -n auto --no-cov    # the files you touched, WHOLE
    make done                                                                  # once, backgrounded, not watched

### Probe vs survey: when `-x` pays (GM 2026-08-15)

Every test run is one of two things, and fail-fast is right for exactly one of them:

- **A PROBE** - "did anything break?", and you will fix whatever surfaces one at a time. Add `-x`:
  the first failure arrives in seconds and you were going straight back to the code anyway. This is
  the mid-iteration whole-file run after an engine change.
- **A SURVEY** - you need the failure SET to scope a problem: how far did this ripple, is this one
  bug or five? Run everything, no `-x`. The pattern of failures is the diagnostic.

The decision follows from RERUN COST: when a rerun is cheap, `-x` costs nothing; when a rerun
costs minutes, one complete run beats N fail-fast runs. That is why `make done` stays
report-everything (the GM's 2026-07-25 decision - every phase runs, all failures report together,
fix them all, re-run once) and why the coverage gate could not take `-x` anyway - coverage needs
the full run. Two caveats: a `-x` run that fails says nothing about the tests it never reached, so
it never substitutes for the whole-file pass before the gate - it is for iterating, not for
clearing; and under `-n auto`, xdist stops soon after the first failure rather than instantly,
which is still most of the saving.

## Run the cheap linters BEFORE the full gate

`make done` runs lint -> format -> typecheck -> test+coverage and STOPS at the first failure, so a
trivial formatting or type slip makes you pay a full ~1-min gate run to discover it, fix, and pay
again - the failures surface one per gate run, not all at once. After writing engine code and
BEFORE `make done`, run the seconds-long prefix yourself:

    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy

That catches format + lint + type errors in one cheap shot. Only then spend the gate run on tests
+ coverage. (The old warning here about local names colliding "in the huge gate() scope" retired
with feature 022 - gate() is a registry of segment functions now, each with its own scope.)

## Update the predictably-affected tests in the SAME edit

Touching a `settlement/` method breaks its unit tests deterministically - you know which ones
before you run anything. `channel_footbridges` has `test_channel_footbridges_*` (in `tests/settlement/`)
and the `_footbridge_map` (in `tests/check_village/`) fixture; changing placement semantics (e.g. "a plank now
needs cultivation on both banks") means those setups need cultivated ground added. Update them in
the same turn as the engine change, don't discover the breakage via a failed pool sweep. Grep for
the method name in `test_*.py` before editing.

## Converge on a new rule with ONE pool-wide dry-run, not one variant per turn

When adding a placement rule or check, the pool IS the test bed: the right predicate is the one
that flags exactly the defective features and spares every good one across all 13+ maps. Don't
test candidate rules one-per-turn against one map. Write ONE script that loads every pool manifest
and, for each candidate predicate (marsh-only vs both-banks-cultivated vs cultivated+village+dike
...), prints what each would drop/keep per map - then read it once and pick the winner. This is how
the footbridge rule's edge cases (polder toe-planks cross onto the DIKE; village-edge planks cross
to houses; dry-to-wet crossings) surfaced in one pass instead of five.

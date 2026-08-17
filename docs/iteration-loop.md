# Iteration-loop efficiency: the measured rationale

*Project reference, split out of [`../CLAUDE.md`](../CLAUDE.md) so it is loaded on demand rather than in every session's context. CLAUDE.md keeps the short always-on version of these rules and points here for the full spec.*

**Load this file when:** you want the evidence behind the loop rules in CLAUDE.md, or you are about to argue with one of them. Every rule here was paid for in measured wall-clock; the incident detail lives here so the rules themselves can stay short.

---

**Iteration-loop efficiency** (profiled with the GM, 2026-07-20): a transcript-timestamp profile of a representative small feature showed **78% of wall time was model turn latency and only 22% tool execution** - tool speed is NOT the bottleneck; the NUMBER of sequential turns is. This holds project-wide (webapp + skills). Standing practice:

- **Batch into fewer, bigger turns.** Group independent recon (greps, file reads, artifact inspections) as parallel tool calls in ONE turn instead of one lookup per turn, and apply a planned multi-edit to a file in one turn rather than edit-per-turn. Only serialize when the next step genuinely depends on the previous result - do not batch past a real decision point, and never skip looking at a result that could change the plan.
- **Docs-only diffs skip the gate.** If everything changed since the last green gate is markdown/docs, do not re-run the gate (`make done`) - it runs once at stop-work for the code that changed. (This redundancy has cost a full gate run before: a re-run after only a docs edit.)
- **Before changing ORDERING or architecture, read the paths and settle the design first.** When a change touches *when* something happens relative to something else - draw order, placement phases, which registry a feature is recorded in, what runs before/after a flush - read every path involved in ONE batched pass and decide the sequence up front. The failure mode is discovering the ordering one gate failure at a time: 2026-07-25 turned a small rule ("no tree drawn on a roof") into four fix-fail-read cycles and ~13 minutes, because each fix revealed the next ordering fact. Those facts were all readable in advance. This is advisory - no hook can detect it - so it is backed up where it bites: the `/diagram` engine now carries a **DRAW ORDER** map in [`.claude/skills/diagram/CLAUDE.md`](../.claude/skills/diagram/CLAUDE.md) plus pointer comments at the registries and the order-sensitive methods themselves, so the rule is in front of you at the moment you would break it. Where you add ordering-critical code elsewhere, do the same: a comment at the point of change beats a rule in a document nobody re-reads.
- **Batching is ENFORCED, not advised** (GM 2026-07-25, [`scripts/batching-hooks.sh`](../scripts/batching-hooks.sh), tested by [`scripts/test-batching-hooks.sh`](../scripts/test-batching-hooks.sh)). When **3 of the last 6 turns** each made a single quick read-only call, a PreToolUse hook BLOCKS the next recon-shaped call and its message carries the whole counter-playbook (batch independent lookups, fold a retry-patch + regen + check into one asserted script, put the action in the same command as the read, never pad with no-ops) so no session rediscovers the strategies. Only quick single reads are ever the blocked call - substantive work (heredocs, `&&`/`;` folds, pytest/make/git-commit runs) always passes, because a 2026-08-09 profile of a patch-grind session found 49 of its 52 blocks landing on patch scripts or already-folded commands, one firing per 14 turns (~9 min of pure block latency) and an induced no-op padding turn. The bar also re-arms higher after each firing (3 doubling toward the window of 6) and decays back to 3 as turns batch, so a reminder stays a reminder instead of a wall. It classifies by measurement, not guesswork: calls in one message arrive milliseconds apart while calls in separate turns are a full round trip apart, and "quick" is the call's actual measured duration. This exists because the doctrine below was written on 2026-07-20 and a profiled feature five days later still batched **zero times in 139 calls** - 104 of which finished in under 2 seconds, doing 29 seconds of work between them at a cost of ~23 minutes of latency. Documentation you have to remember is not a control.

  **Re-tuned 2026-08-08, and the re-tune is the interesting part.** The original counted *consecutive* serial turns and reset to zero on any batched turn or any slow call. A profile of the caption-resize session says that let nearly everything through: **147 of 162 tool round trips (91%) made exactly one call**, costing **22.7 minutes of model latency for 4.0 minutes of tool execution** - and across all of it the hook fired **twice**. The 15 batched turns were scattered through the serial runs, and each one wiped a streak of five that was one turn from tripping. So the counter is now a ROLLING WINDOW - *how many of the last 6 turns were serial and cheap* - with the threshold down to 3; a batched or slow turn is one `0` that ages out instead of an amnesty for everything around it. A block still clears the window, so a genuinely serial chain can never deadlock: worst case one interruption per 3 serial turns, and at 9.2s per round trip a block that turns the next three single calls into one message has already paid for itself. Three implementation traps are recorded in the script and pinned by tests: bash's `${s: -n}` returns the EMPTY string when `n` exceeds the length (so an unguarded trim erased the history on every write and the hook could never fire); on a batched turn the FIRST `posttool` already sees `calls=2`, so the turn's history entry has to be appended at `pretool` or the batch silently overwrites the previous turn's entry; and a **backgrounded** call returns in milliseconds, so the duration test read `make done --run_in_background` as the cheapest possible recon and blocked the one thing these rules most want you to do - `run_in_background: true` is now exempt from both the count and the block. (A backgrounded turn is still a TURN and still ages the window, which is correct: the window asks how much of your RECENT work was one-call recon.)

- **A `-k` subset is not a pre-gate check, and that is ENFORCED too** (GM 2026-08-08, [`scripts/gate-hooks.sh`](../scripts/gate-hooks.sh), tested by [`scripts/test-gate-hooks.sh`](../scripts/test-gate-hooks.sh)). If the only local pytest run since your last `.py` edit used `-k`, the hook BLOCKS `make done` once and tells you to run the whole file. The rule itself is older - the diagram dev-loop doc has had a section heading saying exactly this since 2026-07-25 - which is the point: a session read it, ran `-k "kura_side or punishment"`, went to the gate, and the gate died on `test_place_punishment_spot_probes_for_a_clear_caption_seat`, a test in the same file on the same function that the filter did not select. A whole-file run costs ~45s; that gate cycle cost 3.9 minutes of idle plus the fix turns. A source edit clears the flag (an earlier run predates the code and cannot vouch for it), a run without `-k` clears it, and `GATE_OK` in the command overrides with a reason. Fourth control of the same kind, for the same reason as the other three.
- **`make done` runs every phase and reports all failures together** (both Makefiles, 2026-07-25). It used to stop at the first failing phase, so a lint slip hid a type error hid a coverage hole and each hidden failure cost another full gate run to discover. Fix everything it lists, then re-run once. When the coverage gate fails it also runs [`scripts/uncovered-in-diff.py`](../scripts/uncovered-in-diff.py), which intersects the coverage miss with `git diff` and prints **the lines you changed that no test reaches**, with their source text - so the retry is a certain fix instead of a hunt through a 5,000-line module.
- **Never re-run a suite the gate just ran, and never run pytest without `-n auto`.** Both Makefiles run `pytest -n auto`; serial pytest is ~7x slower on this box. A green `make done` is the proof that every test in it passed - re-running one of its files "to be sure" buys nothing. Measured cost of getting this wrong (2026-07-25, transcript profile of a 69-minute feature): **13.2 minutes, 19% of the whole feature's wall clock**, spent re-running a regression suite serially that the gate had already run in parallel minutes earlier. It was the single largest time sink in the profile - larger than every real gate run combined.
- **Read derived data from the recorded artifact, not by re-running the generator.** Second-largest sink in that same profile: 7.6 minutes across three runs of an analysis script that re-ran all 17 map generators to compute something the manifests already contained - the same analysis reading the JSON took 0.2s. Regenerate when you need to change what a generator DRAWS; read its output when you need to know what it drew.
- **Iterate on the motivating artifact; run the full test bed exactly once, at the end.** The red/green loop runs against the one artifact (map, fixture, page) that exhibits the defect - a single-artifact rebuild is cheap, so cycles are near-free. The full sweep (the whole test suite / every generated artifact) is reserved for AFTER the motivating artifact is in a good state - but it is MANDATORY then whenever shared code changed, since every downstream artifact depends on it and the sweep is what turns "no other case has this bug" from a hope into a verified claim. Anti-pattern: using the full suite as the FIRST verification of a shared-code change - a failure that would surface in seconds on one artifact surfaces many minutes in. Package-specific gate timings and sweep mechanics live in that skill's dev-loop doc (e.g. [`.claude/skills/diagram/CLAUDE.md`](../.claude/skills/diagram/CLAUDE.md)).
- **Background the final gate - and NEVER poll it** (GM 2026-07-25, now ENFORCED by [`scripts/no-poll-hooks.sh`](../scripts/no-poll-hooks.sh), tested by [`scripts/test-no-poll-hooks.sh`](../scripts/test-no-poll-hooks.sh)). Start the stop-work gate with `run_in_background`, write the docs/commit message while it runs, and act on the COMPLETION NOTIFICATION the harness sends; report done only after it comes back green. Watching a backgrounded command is worse than running it in the foreground, and a transcript profile proved how much worse: **10.9 minutes - 35% of a 31-minute feature - went to polling two gates that had already finished** (they took 97s and 98s; the waits took 351s and 401s). The wait loop used `pgrep -f "make done"`, which **matches its own shell** - the pattern is an argument of the very command line being searched - so its `break` could never fire, and `command sleep` was quietly evading the harness's own foreground-`sleep` block. The hook now refuses all of it at PreToolUse: `pgrep -f`/`pkill -f` on a literal pattern, any loop containing a `sleep`, and the `command sleep` / `/bin/sleep` / `env sleep` bypass forms. A real wait on EXTERNAL state the harness cannot see (a dev-server port, a remote queue) passes by putting `POLL_OK` in the command with a note saying what it waits for. This is the third control of the same kind, for the same reason: the "background the final gate" instruction was already written here, and the session followed it and then blocked on the gate anyway.
- **A review agent is the most expensive thing you wait on - SCOPE it, SPLIT it, launch it EARLY** (GM 2026-08-08). Profiled on the caption-resize session: one `settlement-review` agent, handed two maps with no scope, ran a full audit - **12.3 minutes, 22% of the task's whole wall clock**, with the session idle for 11.4 of them, and two of its five findings were pre-existing defects unrelated to the change. The agents now take **`DELTA: <what changed>`** and review the change, whatever the re-pack moved, and whatever the change made incoherent with its neighbors, naming the sweeps they skipped; `FULL` stays the default for a new or heavily-rewritten artifact. Run **one artifact per agent, in parallel** - the sweeps share no work across artifacts, so bundling them just serializes two audits behind one notification. And launch the moment the artifact is final, before the visual pass and the commit: everything you do while it runs is free, everything after it is added on. This does NOT weaken Principle I - the review still happens, it is just asked the question you actually have.
- **Resolve the session's clone NAME in turn 1, not after the recon** (GM 2026-08-08). The clone-name check is now announced by [`scripts/clone-sync-hooks.sh`](../scripts/clone-sync-hooks.sh) on the FIRST prompt of any session with no claimed clone, because the pretool backstop only speaks at the first EDIT and that is far too late: a session spent 4.7 minutes on recon and planning, discovered only then that its name did not resolve, and the GM's `/rename` became **4.6 minutes of dead wall-clock** instead of something that could have overlapped the analysis. A blocking question you can see coming should be asked while you still have other work to do.
- **Do NOT cut the ritual steps** (regression-fixture freeze, overlap-registry classification, record-the-why docs, the stop-work ritual). GM-confirmed 2026-07-20: they cost ~2 minutes per feature and are why the regression rate stays near zero. The savings come from turn structure, never from skipping guardrails.

## The 5% threshold: a whole-process speedup is never "only N seconds" (GM 2026-08-16)

Stated while deciding feature 026 (the cache-backed gate): **a >=5% wall-clock speedup to a whole
process - a gate run, a sweep, a full generation pass - is always above the threshold of caring,
even when the absolute saving is a handful of seconds.** 10 s off a 180 s gate is more than 5% and
matters; 30 s off is a sixth of the whole run and is extremely significant. The reasoning is the
same one at the top of this file: iteration cost compounds, because the gate runs many times a day.

The distinction that keeps this from licensing micro-optimization: it applies to END-TO-END
processes, not individual functions. A 5% win inside one function is usually below the threshold -
unless that function effectively IS the process (the `main` of a scripted run), in which case it
is the process and the rule applies. When weighing a perf change to a loop, compute the
percentage, not just the seconds, and never argue "it's only N seconds" against a >=5%
whole-process win.
## The 2026-08-16 profile: the cut-bank fix, and where the time goes now

First full transcript profile taken AFTER the 2026-08 performance refactors (pool-regen fan-out,
cache-backed gate, batched crop inspection, batching hooks), on a representative small engine fix
(the cut-bank scrub margin): **14m33s prompt-to-verified-in-main**, breaking down as **60% LLM
turn latency (520s), 28% idle waiting on background work (249s), 12% foreground tool execution
(102s)**. Compare 2026-07-20's 78%/22% split on much larger absolute tool time: both halves
shrank. The findings that set the next round of rules:

- **The gate was NEVER on the critical path.** It ran 177s and finished 92s BEFORE the
  settlement-review DELTA agent (350s) - the critical path was diagnosis -> design ->
  implementation -> the REVIEW tail (84s past the green gate) -> wrap-up (57s). Speeding the gate
  further buys nothing on this task shape; launching the review earlier and making it cheaper buys
  the tail. Hence the sharpened review-launch rule (diagram CLAUDE.md, "Invoking a review agent")
  and `tools/scatter_audit.py` (feature 108), which converts the review's ~21-tool-use hand parse into
  one seconds-fast script.
- **Seven long reasoning turns were 273s of the 520s LLM time**, and the largest (75s) partly
  re-derived a recorded open decision. Hence the open-decision-sketch convention (diagram
  CLAUDE.md, "An OPEN DECISION carries an implementation sketch").
- **A 38s foreground pool-regen sweep bought nothing** - the rule, with its render claim VERIFIED
  against the render model rather than assumed: foreground-regenerate only the MOTIVATING map (a
  session needs its render for its own crop inspection); run the whole affected test file; do NOT
  run a pre-gate `pipeline/regen.py pool/*/*.gen.py` sweep. The gate verifies the pool itself
  (`DIAGRAM_SKIP_RENDER` + gencache), and `sync-with-main.sh` render-sync REGENERATES main's
  renders from main's own committed tip (RENDER MODEL, GM 2026-07-22) - so clone-side renders of
  non-motivating maps feed nothing at all.
- **Projected floor for tasks of this shape: ~12 minutes** - roughly 8 minutes of genuinely serial
  reasoning and implementation with the review tail fully overlapped. The next profile taken after
  these rules land compares against that number.

## The 2026-08-16 profile #2: the fan-toe pond fix (45.7 min), and the cohort fan-out it bought

Second post-refactor profile, on a GM-reported map defect (a field pond spilling across its plot).
**45.7 minutes** prompt-to-synced, attributed with every second in exactly one bucket: **44% LLM
generation (1206s over 148 responses), 40% idle waiting on background work (1087s), 9% unit tests
(235s), 6% hamlet generation (178s), 1% git/sync/lint/crops**. The review agents cost nothing -
launched early, they finished inside the cohort's shadow, which is the launch-early rule paying off.

Why a "simple" fix ran long, and what each finding bought:

- **The two 24-seed cohort rolls were 17.3 min of the 45.7, ~11 min of it critical-path idle.** The
  cohort is the verification step of every placement-rule change, and `python3 -m l7r.diagram.hamletgen --batch`
  was still SERIAL - `regen.py` and `cohort_audit.py` had been fanned out in the 2026-08-15 round
  and this CLI was simply missed. Fixed the same day: **526s -> 71s (7.4x)**. Two lessons past the
  fix itself. First, when a perf round parallelizes a class of work, census every entry point into
  that class - the one nobody profiles is the one that stays serial. Second, **the verdict-identity
  check has to control for what else moved**: the parallel run differed from the serial baseline on
  3 of 24 maps, which looks damning until you notice the baseline predated a mid-task merge of
  another session's engine round (whose own notes predicted exactly that `field_ringed` marginal
  flip). Re-rolling only the three differing seeds serially on the CURRENT code proved the match in
  ~45s. Diff against the same code, not against an older log.
- **A second iteration (~8 min) because the first fix used the check's PREDICATE but not its full
  INPUT SET.** Placement fitted the pond against its host plot; the check scans every plot ring plus
  the drain hem, and a comb fan's rings overlap at the fan/grid seams. The existing "placement and
  its check must read the SAME manifest source" rule covers the data source; this sharpens it to the
  EXTENT of that source. The cohort caught it, which is the argument for cohorts over single maps.
- **~4-5 min (~10%) lost to three failed heredoc patch scripts**, all quoting slips in
  Python-that-rewrites-Python, none of them wrong anchors. Hence the "edit with `Edit`" rule in
  CLAUDE.md - it batches into one turn just as well and cannot fail this way.
- **The mid-task merge conflict was cheap** (~4.5 min including a second gate and regenerating four
  maps, ~1 min of it the actual resolution). Concurrent sessions colliding is inherent; nothing here
  suggests a process change.
- **Projected shape after the fan-out: ~28-30 min for this task, ~20 of it model latency.** Past
  that point the remaining cost is reasoning and the verification rituals, which is where it should
  be.

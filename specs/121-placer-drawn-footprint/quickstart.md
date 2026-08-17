# Quickstart: reproducing the red state, the measurement, and the gate

All commands run from `.claude/skills/diagram/` **inside the session clone**. Never in main's tree.

## 1. Take the baseline (before touching anything)

```bash
git worktree add --detach <scratchpad>/base121 HEAD          # never a stash
cd <scratchpad>/base121/.claude/skills/diagram
python3 -m l7r.diagram.tools.cohort_audit --count 24 --seed 1 > baseline-cohort.log 2>&1
make done > baseline-gate.log 2>&1
```

**Known artifact**: in a detached worktree `.git` is a *file*, not a directory, so `scripts/gate-stamp.py` raises `NotADirectoryError` writing its green-stamp. The gate itself still runs to completion and prints `gate green`. Read the log; do not read the traceback as a gate failure.

## 2. Manufacture the red state (check before fix)

The lane defect is **latent** at the shipped `LANE_CLEARANCE = 48.0` - the drawn steading clears the tread by margin, not by test. To see it, lower the constant to the plain-house blanket figure and roll the cohort:

```bash
# in l7r/diagram/hamletgen/consts.py: LANE_CLEARANCE = 32.0
python3 -m l7r.diagram.tools.cohort_audit --count 24 --seed 1 --only houses_clear_of_lanes
```

Expect roughly half the cohort to fail with a house corner on a lane tread (12 of 24 when this was last measured, 2026-08-12). **That failing cohort is the test for item 3.** It must go green at that same clearance after the fix, with nothing else regressing.

## 3. Measure refusal attribution

Compute the diagnostic **beside** the real verdict in one wrapper, so the map generated is the real map:

- count refusals where the exact rotated-quad test also says no (**real occupancy**);
- count refusals where only the circumscribed circle says no (**approximation-only**);
- report the change in the pool of legal seats.

**Print the value and its provenance from ONE expression, or print no provenance at all.** The skill has two recorded incidents of a probe that derived its number and its explanation separately and produced a confident, wholly wrong finding - one of which became a documented "genuine geometric conflict" that did not exist.

Target: approximation-only refusals reach **zero**, with real-occupancy refusals unchanged. A rise in the latter means the tightened verdict is refusing things it should not.

## 4. Iterate on ONE map, sweep once at the end

```bash
DIAGRAM_SKIP_RENDER=1 python3 pool/hamlets/inashiro.gen.py \
  && python3 -m l7r.diagram.check_village pool/hamlets/inashiro.json
```

Then, once - and this final sweep is mandatory because shared code changed:

```bash
python3 -m l7r.diagram.pipeline.regen pool/*/*.gen.py   # frozen legacy maps print FROZEN and are skipped
python3 -m l7r.diagram.tools.cohort_audit --count 24 --seed 1
```

## 5. The gate

```bash
make done          # ruff + ruff format --check + mypy --strict + pytest + coverage floor
```

Run the **whole** affected test file locally before the gate, never a `-k` subset - a filter selects the tests you were thinking about, and a change breaks the ones you were not. Background the final gate and act on the completion notification; never poll it. `make done > log 2>&1` and nothing more - a trailing `echo EXIT=$?` makes a failed gate notify as exit 0.

## 6. Review before done

Each of the four live scripted hamlets whose output moves gets an independent `settlement-review`. Spot-check the artifacts against what the review says; "the subagent said it was done" is not verification.

## The four live maps

`pool/hamlets/{inashiro,kashikawa,mizuguchi,sawada}.gen.py`. Everything else in the Mode B pool is a frozen exhibit - it prints `FROZEN`, is not regenerated, and its violations of post-freeze rules are **not bugs**.

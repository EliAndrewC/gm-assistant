# Quickstart: verifying feature 126

**Feature**: 126-derived-lanes-and-form

Everything below runs from `.claude/skills/diagram/` inside the session clone. Never in main's tree.

## The baseline this is measured against

Taken on unmodified `HEAD` (8ec2a91) in a detached worktree, per Principle XIII - never by stashing,
because a stash mutates the tree under any review agent currently reading it:

```
git worktree add --detach scratchpad/base125 HEAD
( cd scratchpad/base125/.claude/skills/diagram && python3 -m l7r.diagram.tools.cohort_audit --count 48 )
( cd scratchpad/base125/.claude/skills/diagram && make done )
```

Recorded at `scratchpad/base_cohort.log` and `scratchpad/base_gate.log`.

## The gate

```
( cd .claude/skills/diagram && make done )
```

Runs ruff, format check, `mypy --strict`, pytest and the coverage floor together, and reports ALL
failures at once. Background it; never poll it. Never re-run what it just ran.

## The cohort

```
( cd .claude/skills/diagram && python3 -m l7r.diagram.tools.cohort_audit --count 48 )
```

This is the test bed for the feature. Compare against `base_cohort.log`.

**Because the form is now rolled, per-seed comparison degrades.** Where a seed's form changed, a
straight before/after diff is not meaningful. The governing rule, from the constitution:

- the pass RATE must not drop, **and**
- every newly-failing check must be individually diagnosed.

Also compare WITHIN a form where possible - a nucleated seed that stayed nucleated is still a fair
per-seed comparison.

## Checking the form knob does what it claims

```
( cd .claude/skills/diagram && python3 -m l7r.diagram.tools.cohort_audit --count 48 )
```

then read the reported form distribution. Acceptance (SC-003): at least three forms present, none
above 70% of the cohort. Determinism (SC-004): roll any seed twice and get an identical map.

## The four live pool hamlets

```
( cd .claude/skills/diagram && python3 -m l7r.diagram.pipeline.regen pool/hamlets/inashiro.gen.py )
```

Regenerate only the motivating map while iterating. The pool sweep before the gate is pure waste -
the gate verifies the pool itself, and render-sync regenerates main's renders from main's own tip.

## Independent review (required, not optional)

One `settlement-review` per re-rolled pool map, with **at least one map per form** in the reviewed
set. The author of a map is not a reliable reviewer of it, and this feature's entire deliverable is
visual.

## The walk-through page (a deliverable of this feature)

```
( cd .claude/skills/diagram && python3 -m l7r.diagram.tools.placement_stages )
```

Regenerate after the stages are renamed and reordered, **and rewrite the affected `NOTES` prose** -
the page explains WHY each stage sits where it does, and this feature changes those answers. A
re-render alone would leave the page confidently describing the old order.

## What "done" requires

- `make done` green
- cohort pass rate at or above baseline, every new failure diagnosed
- three forms present in the cohort, none dominant
- settlement-review clean on every re-rolled map, covering all three forms
- research written to `research/homesteads.md`, not only to this feature's `research.md`
- `dev/placement.md` STAGES table and `hamlet-placement.html` both updated to the new order

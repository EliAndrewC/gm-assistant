# `tools/` - diagnostics, audits and by-hand utilities

Things you RUN, by hand, when a map comes out wrong or a number needs measuring. **Nothing in this
directory is imported by a generator or by the engine** - that is the membership rule for the
folder, and it is what makes these modules safe to change without thinking about map output. (They
are still inside `gencache.engine_files()`, deliberately: the cache stays conservative rather than
clever about what can reach a gen. See [`../pipeline/CLAUDE.md`](../pipeline/CLAUDE.md).)

Run them as modules, from the skill root:

    python3 -m l7r.diagram.tools.why_placed pool/provincial-cities/nagahara.gen.py --at 1102.6,1429.5

Not `python3 tools/why_placed.py`. A package module run as a loose script puts `tools/` on
`sys.path` instead of the skill root, so the same file can end up imported twice under two names.

## Which tool answers which question

| You are asking | Reach for |
|---|---|
| Who put this thing here? What refused to put anything here? | `why_placed` |
| Where can this feature legally go, under all the interacting rules? | `site_justice` |
| Is there too much empty space in this Mode A compound? Does its SVG break a geometric rule? | `pack_audit` |
| Is drawn ground cover standing somewhere the engine's keep-outs should have stopped it? | `scatter_audit` |
| Does using the generation cache ever change what a map looks like? | `cache_audit` |
| I fixed one hamlet - does the fix generalize across a cohort, and what exactly collides? | `cohort_audit` |
| I want to look closely at one spot on a rendered map, in manifest coordinates | `crop_map` |
| How long does this loop actually take, and where does the time go? | `timings` |
| Rebuild the frozen negative-fixture corpus in `pool/regressions/` | `make_regressions` |

Each module's own docstring carries the WHY it exists, usually with the incident that produced it.
Read that before extending one. The skill's [`../CLAUDE.md`](../../../CLAUDE.md) carries the operational
guidance for the two that change how you debug: "Ask the GEN who placed it" (`why_placed`) and
"Siting a feature with interacting rules" (`site_justice`).

## The rule these share: a diagnostic OBSERVES, it never restates

`site_justice` adjudicates a candidate seat by building a trial manifest and running
`check_village.gate()` on it. `why_placed` reads its refusal causes off the real `_in_blocked` /
`_near_corridor` / `_hard_clear` as they return. Neither re-implements a rule, and that is not
style: the predecessor of `site_justice` was a scratchpad script that re-derived every rule as its
own predicate, and it drifted **within a single session** - a relaxation made to satisfy one map
persisted and put Nagahara's boundary stone in a field off the highway. A tool that re-derives a
rule will eventually disagree with the checker and then tell you the wrong thing with total
confidence.

`pack_audit` and `scatter_audit` are the exception that proves the rule: Mode A has no manifest and
scatter is draw-time ink, so both parse the rendered SVG. They are the source of truth for their
own questions rather than a restatement of someone else's.

## Coverage

`pack_audit`, `site_justice` and `scatter_audit` are under the 100% rule - they are pure logic over
a parsed artifact, and their verdicts ship. `cache_audit`, `cohort_audit`, `crop_map`, `timings`
and `make_regressions` are not: they are drivers whose whole behavior is subprocess orchestration.
The measured set is named module-by-module in `pyproject.toml` rather than by directory, so that
boundary stays explicit instead of becoming a side effect of which folder a file lands in - a new
tool dropped in here does not silently owe 100% coverage on the day it arrives.

## Known stale, recorded rather than quietly fixed

`make_regressions` reads `check_village.py` for the list of `check("...")` names. That file has not
existed since feature 024 split the gate into the `check_village/` package, so the tool raises
`FileNotFoundError` there. This predates the 2026-08-16 reorganization and was left alone by it.
The check names are now derivable from `check_village.registry`, or readable from the frozen
[`../tests/fixtures/gate_check_names.json`](../../../tests/fixtures/gate_check_names.json).

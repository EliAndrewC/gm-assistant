# Operation registry (draft, T003)

Enumerated by walking the tree, NOT inferred from module paths - `tools/` holds both a
25-minute cohort and a manifest read, so no path heuristic classifies correctly.

`cost` decides PROMPTING only. REFUSAL applies to every row.

| module | kind | cost | make target |
|---|---|---|---|
| `l7r.diagram.check_village` | package CLI | cheap | _TBD_ |
| `l7r.diagram.citybudget` | script main | cheap | _TBD_ |
| `l7r.diagram.compound` | script main | **expensive** | _TBD_ |
| `l7r.diagram.hamletgen` | package CLI | expensive | _TBD_ |
| `l7r.diagram.pipeline.pool_index` | script main | expensive | _TBD_ |
| `l7r.diagram.pipeline.regen` | script main | expensive | _TBD_ |
| `l7r.diagram.pipeline.render_cache` | script main | expensive | _TBD_ |
| `l7r.diagram.tools.cache_audit` | script main | expensive | _TBD_ |
| `l7r.diagram.tools.cohort_audit` | script main | expensive | _TBD_ |
| `l7r.diagram.tools.crop_map` | script main | cheap | _TBD_ |
| `l7r.diagram.tools.jogs` | script main | cheap | _TBD_ |
| `l7r.diagram.tools.make_regressions` | script main | expensive | _TBD_ |
| `l7r.diagram.tools.mapcheck` | script main | expensive | _TBD_ |
| `l7r.diagram.tools.pack_audit` | script main | cheap | _TBD_ |
| `l7r.diagram.tools.perf_snapshot` | script main | expensive | _TBD_ |
| `l7r.diagram.tools.placement_stages` | script main | expensive | _TBD_ |
| `l7r.diagram.tools.scatter_audit` | script main | cheap | _TBD_ |
| `l7r.diagram.tools.site_justice` | script main | cheap | _TBD_ |
| `l7r.diagram.tools.timings` | script main | expensive | _TBD_ |
| `l7r.diagram.tools.why_placed` | script main | **expensive** | _TBD_ |

**20 entry points.** Existing make targets (13): `bypass-audit`, `done`, `format`, `guard`, `lint`, `maps`, `perf`, `perf-report`, `quick`, `reference`, `test`, `test-full`, `typecheck`

**Gap**: every row above with `_TBD_` needs a target (FR-001). A refusal must be able to
name one, so the registry and the Makefile are two views of the same list and a guard test
asserts they agree.


## Classification findings (T003) - two corrections, one of them material

Costs were decided by reading what each module DOES, not by its path. Two came out against my
prior assumption:

- **`tools.why_placed` is EXPENSIVE, not a manifest reader.** It calls
  `runpy.run_path(path, run_name="__main__")` (line 227) - it RE-RUNS THE GENERATOR to capture
  refusal causes off the live predicates. This matters beyond the row: round 1 of spec.md argued
  that gating diagnostics would "push a session toward regenerating a map", and `why_placed` was
  one of the three diagnostics named. For that one, running the diagnostic **IS** regenerating the
  map. The argument was not merely wrong in the way the fidelity reviewer identified; its example
  was wrong too.
- **`compound` is EXPENSIVE.** Its `main()` composes and writes a Mode A compound SVG (line 399).
  It has no `__main__.py`, which is why an earlier count of "18 entry points" missed it and
  `citybudget` both. The walk found 20.

Genuinely cheap, verified: `site_justice` (adjudicates against an EXISTING manifest, and exists
precisely to avoid "a regenerate-and-check cycle per guess"), `pack_audit` and `scatter_audit`
(parse a rendered SVG, stated read-only), `crop_map`, `jogs`, `check_village` (gates a manifest
that already exists), `citybudget` (pure arithmetic).

**Open for T006**: `tools.timings` and `pipeline.pool_index` are classified expensive on the
conservative side without measurement. Over-classifying costs a prompt on something that may not
need one; under-classifying leaves an expensive path unprompted. T006 resolves both by timing them
rather than by reading them.

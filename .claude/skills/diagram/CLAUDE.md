# /diagram engine - dev loop

Guidance for *working on the diagram engine* (`settlement.py`, `check_village.py`, the pool
generators), as opposed to *invoking* `/diagram` to draw a map (that is `SKILL.md`). This file
auto-loads whenever a session edits files in this directory - which is exactly when it applies.

The project-wide iteration doctrine lives in the root [`CLAUDE.md`](../../../CLAUDE.md)
"Iteration-loop efficiency" section (batch recon into fewer bigger turns; iterate on the ONE
motivating map, then sweep the pool once at the end; background the final gate; never cut the
ritual/guardrail steps). Read that first. Below are the DIAGRAM-SPECIFIC lessons that section
does not cover - each earned by costing real round-trips.

## Batch the rendered-map inspection

Reading a map means: render -> crop the region(s) of interest -> Read the PNG. The turn-latency
killer is doing this serially, one crop per turn (`crop -> Read -> crop -> Read ...`). ~78% of
wall time is model-turn latency (root CLAUDE.md, 2026-07-20 profile), so each extra round-trip is
pure cost. Instead: in ONE Bash call, crop EVERY region you want to look at (all four viewports of
a defect, before/after of several maps, the toe + the top + a control), then Read them together in
the next turn. A footbridge review that touched 3 maps should be ~2 turns of imagery, not ~10.
Coordinate mapping helper: manifest coords -> PNG px is `(coord - viewBox_origin) * (png_w /
viewBox_w)`; grep the `.svg` `viewBox` once and reuse it for every crop on that map.

## Run the cheap linters BEFORE the full gate

`make done` runs lint -> format -> typecheck -> test+coverage and STOPS at the first failure, so a
trivial formatting or type slip makes you pay a full ~1-min gate run to discover it, fix, and pay
again - the failures surface one per gate run, not all at once. After writing engine code and
BEFORE `make done`, run the seconds-long prefix yourself:

    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy

That catches format + lint + type errors in one cheap shot (a common one: a local variable name
like `a`/`ux` that collides with an existing binding in the huge `gate()` scope - mypy flags it,
the full gate would too but slower). Only then spend the gate run on tests + coverage.

## Update the predictably-affected tests in the SAME edit

Touching a `settlement.py` method breaks its unit tests deterministically - you know which ones
before you run anything. `channel_footbridges` has `test_settlement.py::test_channel_footbridges_*`
and the `test_checks.py::_footbridge_map` fixture; changing placement semantics (e.g. "a plank now
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

## Placement and its check must read the SAME manifest source

A recurring engine trap (footbridges 2026-07-22; recorded in [`settlements.md`](settlements.md)
under "PLANK BRIDGES"): the generator in `settlement.py` and the validator in `check_village.py`
must classify terrain from the SAME data, or they disagree and a feature the generator dropped is
demanded by the check (or vice versa). Read the MANIFEST fields (`M["fields"]` outlines +
`M["dry_plots"]`), NOT engine-internal blocking lists like `self.field_polys` that some gens leave
empty. When a new check pairs with new placement logic, factor the shared predicate so both sides
provably use it.

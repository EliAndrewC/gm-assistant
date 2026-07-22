# Quickstart: implementing & verifying Near-Ring Farmland Density

**Feature**: 013-near-ring-farmland | **Date**: 2026-07-22

All work happens in the session clone (`.clones/diagram-town`), inside `.claude/skills/diagram/`. Never run generators or tests against main `/gm-assistant`.

## The red/green loop (per the iteration-efficiency doctrine)

Iterate on the **one motivating map** (Hirameki first, then Tango), not the whole pool. Single-map regen + gate is ~1-7s, so cycles are near-free. Reserve the full-pool sweep for the end.

1. **Check-first (red).** Add `near_ring_cultivated_fraction` and its test in `test_checks.py`. Save the current (undensified) Hirameki manifest as `pool/regressions/near_ring_cultivated_fraction_fires_on_sparse_hirameki.json`. Run the check against it and confirm it FIRES (the sparse map fails the dense threshold). This is the failing test that proves the check has teeth before any fix exists.
2. **Engine (green).** Implement `s.near_ring_cropland(...)` + the `meta(near_ring_density=...)` read + the derived-band logic in `settlement.py` (and any dry-plot hill keep-out gap in `check_village.py`). Unit-test the geometry in `test_settlement.py` to 100% line coverage.
3. **Redesign the motivating map.** In `hirameki.gen.py`: drop the near-ring `s.commons([...])` polys (keep only true frame-margin ones), call `s.near_ring_cropland(...)` after the paddy combs. Regenerate just Hirameki and run the gate:
   ```
   # from .claude/skills/diagram/, regenerate + validate the single map
   python3 pool/towns/hirameki.gen.py        # (or the project's single-map regen entrypoint)
   pytest test_checks.py -k hirameki -q       # plus the new check
   ```
   Iterate until the near ring reads packed AND the whole gate is green, including `near_ring_cultivated_fraction`, `town_margins_clothed`, `town_farmers_plurality`, population/caste bands, and every overlap/water check.
4. **Re-reconcile town population.** If step 3 added farmhouses at town scale, adjust `meta(population=...)` so `town_caste_count`/`households_consistent` stay in band (plurality is only helped).
5. **Repeat for Tango** (city; fill OUTSIDE the wall, respect moat/gates/ward fences; city farmhouses do not touch the population figure).
6. **Tunability proof.** Set `meta(near_ring_density="thin")` on a variant (or a suitable existing dry map) and confirm the near ring renders visibly thinner and still passes.

## The mandatory full-pool sweep (shared-engine change)

Because `settlement.py` / `check_village.py` changed, EVERY pool map is a downstream artifact. After the motivating maps are good:

```
# from .claude/skills/diagram/
make done        # regenerates every pool map + runs ruff + format + mypy --strict + pytest + 100% cov + the full gate
```

Fix any downstream map the engine change disturbed. **Village and hamlet maps MUST stay behavior-unchanged** (they never call the new method and their scale is out of scope) - confirm their manifests/renders did not move (SC-005).

## Principle XII closing gate (REQUIRED before "done")

The automated gate proves internal consistency, never historical truth. Before reporting done, open the rendered PNGs (not the code) and confirm each Element from research.md Part A:

- **Hirameki.png / Tango.png**: does the near ring READ as embedded in farmland (Element 1)? Is scrub only at the frame margins / on the hill / at the wet toe (Element 2)? Is it a quilt of paddy + dry fields + gardens, not a monoculture (Element 3)? Is there no paddy on any slope (Element 4)?
- **The thin variant**: visibly thinner near ring than the dense default (Element 5)?
- Spot-check Hoshizora and Nagahara for regressions.

Record the review outcome in each map's review log (the maps carry a review-log convention). If the picture contradicts a Part A element, fix the map, do not rationalize the code.

## Definition of done (maps to the spec's Success Criteria)

- SC-001/002: Hirameki + Tango near rings read packed; walls/moat/roads/compounds unchanged.
- SC-003: full-pool `make done` green.
- SC-004: a thin-tier map is visibly thinner and passes.
- SC-005: village/hamlet maps unchanged.
- SC-006: the "why" is in `settlements.md` (Historical grounding) and beside the threshold constant.

Then run the stop-work ritual: commit in the clone, `bash scripts/sync-with-main.sh done` (push + render-sync). Do NOT re-run the gate for docs-only follow-ups.

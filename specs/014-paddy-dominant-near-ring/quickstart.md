# Quickstart: implementing & verifying Paddy-Dominant Near-Ring Farmland

**Feature**: 014-paddy-dominant-near-ring | **Date**: 2026-07-22

All work in the session clone (`.clones/diagram-town`), inside `.claude/skills/diagram/`. Never run generators/tests against main `/gm-assistant`.

## The red/green loop (iterate on ONE map)

Single-map regen + gate is ~1-7s; reserve the full pool sweep for the end.

1. **Check-first (red).** Add `near_ring_paddy_dominant` + its tests to `test_checks.py`. Freeze the current (013, dry-grain-dominant) Hirameki manifest as `pool/regressions/near_ring_paddy_dominant_fires_on_dry_dominant_hirameki.json` (regen Hirameki as-is first). Confirm the check FIRES on it (paddy cells < dry-grain cells) before the engine work.
2. **Engine (green).** Implement `s.near_ring_paddy(...)` (basin filler with water-abutment gating), factoring `_paddy_plots`/`_paddy_surface` out of `paddy_field` if cleaner. Unit-test to 100% (water-abutment gating: keeps a stream-abutting basin, keeps an off-edge basin, drops a no-water basin, drops a stream-crossing basin, keeps basins off the pond core, respects keep-outs).
3. **Recompose Hirameki.** In `hirameki.gen.py`: call `s.near_ring_paddy(<flat-floor bbox>)` (basins along the two streams / off-edge), then demote `near_ring_cropland` to a margin-grain pass (drier/higher bbox, low garden_frac, paddy region in `avoid`) + a near-town garden band (tight bbox, garden_frac≈0.85). Enlarge the combs if the floor needs more watered paddy. Iterate:
   ```
   DIAGRAM_SKIP_RENDER=1 python3 pool/towns/hirameki.gen.py && python3 check_village.py pool/towns/hirameki.json
   ```
   until `near_ring_paddy_dominant` passes AND `near_ring_cultivated_fraction` (still packed) AND `fields_show_water_source` (no waterless paddy) AND every existing check pass.
4. **Render + eyeball** (Principle XII): the near ring reads as *rice paddy* with grain accents on the margins and gardens by the town - not a sea of dry grain.
5. **Repeat** for Tango, Nagahara (cities: extramural basins off-edge or farmhouse-ringed, moat/wall untouched), Hoshizora (thin, but paddy-led).

## The mandatory full-pool sweep

Shared engine changed (`settlement.py`, `check_village.py`), so every map is downstream:

```
make done   # regen every map + ruff + format + mypy --strict + pytest + 100% cov + full gate
```

Fix any downstream disturbance. **Villages/hamlets MUST be byte-unchanged** (they never call the new method) - confirm their tracked `.json` manifests did not move.

## Principle XII closing gate (REQUIRED before done)

The automated gate proves internal consistency, never historical truth - the 013 maps passed every check while depicting the wrong crop. So open the rendered PNGs (not the code) and confirm:

- **Hirameki / Tango / Nagahara**: the flat near ring reads **paddy-dominant** (wet rice is the visually dominant crop), dry grain sits on the drier/higher margins, gardens hug the town, and no paddy sits on ground with no visible water.
- **Hoshizora (thin)**: still visibly thinner than the dense maps, but its cultivation is paddy-led, not dry-grain-led.
- Confirm nothing crosses a wall/moat and gate bridges are intact on the cities.

If a picture still reads dry-grain-heavy, fix the MAP (more near-ring paddy where water reaches / thinner margin grain / lower tier if the near ring genuinely lacks water) - do not relax the check.

## Definition of done (maps to Success Criteria)

- SC-001/002: Hirameki + Tango + Nagahara near rings read paddy-dominant; city walls/moat/estates unchanged.
- SC-003: zero `fields_show_water_source` violations; full-pool `make done` green.
- SC-004: Hoshizora thin + paddy-led, passes at the thin tier.
- SC-005: 013's packed density preserved (`near_ring_cultivated_fraction` still passes).
- SC-006: villages/hamlets unchanged.
- SC-007: corrected "why" + recorded rejection present in `settlements.md` and by the check.

Then the stop-work ritual: commit; `bash scripts/sync-with-main.sh done`.

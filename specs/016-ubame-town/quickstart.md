# Quickstart: regenerating and gating the Ubame map

All commands run from `.claude/skills/diagram/` **inside the session clone**, never in main's tree.

## Regenerate one map and gate it (the fast loop, ~1-7 s)

```sh
DIAGRAM_SKIP_RENDER=1 python3 pool/towns/ubame.gen.py && python3 check_village.py pool/towns/ubame.json
```

`check_village.py` must print ALL CHECKS PASSED. Skipping the raster keeps the loop cheap - the gate
reads the JSON manifest and never looks at the PNG.

## Regenerate with a picture

```sh
python3 pool/towns/ubame.gen.py                      # writes .svg + .json + .png (resvg, 2600px)
DIAGRAM_PNG_WIDTH=1300 python3 pool/towns/ubame.gen.py   # quick low-res eyeball
```

Never call `resvg` by hand for a Mode B map - `s.finish()` rasterizes, so the PNG cannot drift from
the SVG.

## Look at it

```sh
python3 crop_map.py pool/towns/ubame --whole --zoom 0.4          # the whole sheet, downscaled
python3 crop_map.py pool/towns/ubame 1900,300,260 700,1100,220   # x,y,radius in world coords
```

Crop **every** region you want in ONE call, then read the PNGs together - serial crop-read-crop-read
is the expensive shape.

## Confirm a new check actually runs

An opt-in or feature-gated check that never executes looks exactly like one that passes:

```sh
for m in pool/*/*.json; do
  printf '%s ' "$m"
  python3 check_village.py "$m" | grep -c charcoal_yard_keeps_fire_gap
done
```

A `0` on a map that plainly has the feature is the bug.

## Verify a new check has teeth (red before green)

Each new check ships with a negative fixture in `pool/regressions/`, carrying a `_regression` block
naming the checks it must trip. `test_regressions.py` globs the directory, so a new file needs no
wiring:

```sh
python3 -m pytest test_regressions.py -q -n auto --no-cov -k ubame
```

## The full gate

```sh
python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy   # seconds - run FIRST
python3 -m pytest test_settlement.py test_checks.py -q -n auto --no-cov  # whole files you touched
make done                                                                # once, backgrounded, NOT polled
```

`make done` runs lint, format check, mypy, `pytest -n auto` and the 100% coverage floor, and
regenerates every pool map - which is what proves no existing map regressed. It takes ~80 s. Do not
re-run anything it just ran, and never invoke pytest serially (~7x slower here).

## Stop-work ritual

From inside the clone, every time work stops:

```sh
git add -A && git commit -m "..."
../../scripts/sync-with-main.sh done
```

Never `git push --force`.

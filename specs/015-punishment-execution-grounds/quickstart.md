# Quickstart: Punishment Spots and Execution Grounds

**Feature**: 015-punishment-execution-grounds

## Adding both features to a town or city spec

```python
# --- in the urban core, BEFORE the packs (it must reserve its ground) ---
# the punishment ground: cangue frame, flogging post, kneeling stone, on the market
# frontage where the most feet pass. The crime rides on the cangue - no second board.
s.punishment_spot(980, 1240, rot=90)

# --- outside, beside the funerary cluster (phase 4, before scrub and groves) ---
# the boundary stone where the road leaves clean ground...
s.boundary_marker(1710, 1880)
# ...and the ground beyond it. County tier: bare, unfenced, and disused.
s.execution_ground(1840, 1975, rot=15)
```

Opt a backwater seat out entirely:

```python
s.meta(punishment_spot=False, execution_ground=False)
```

## The rules you will trip over

- The execution ground must be **outside** the wall (or 120+ ft from any dwelling), **on** the road (within 120 ft), **past** the boundary marker, **150+ ft** from any cemetery / cremation ground / ossuary / mausoleum, and **off** all farmland.
- The punishment spot must be **inside** the core and within ~60 ft of a street.
- Neither may appear on a hamlet or village map.

## Dev loop

```bash
cd .claude/skills/diagram

# one map: regenerate + gate (~1-7s)
DIAGRAM_SKIP_RENDER=1 python3 pool/towns/hoshizora.gen.py && python3 check_village.py pool/towns/hoshizora.json

# did the new check actually RUN on this map? (0 = it silently never ran)
python3 check_village.py pool/towns/hoshizora.json | grep -c execution_ground_by_the_road

# cheap linters before the gate
python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy

# whole touched test files
python3 -m pytest test_settlement.py test_checks.py -q -n auto --no-cov

# the gate, ONCE, backgrounded, never polled (~80s)
make done
```

## Looking at the picture (the Principle XII closing gate)

`make done` proves internal consistency, never historical truth. Batch every crop into one call, then read them together:

```bash
python3 crop_map.py pool/towns/hoshizora 1840,1975,260 980,1240,180
python3 crop_map.py pool/provincial-cities/tango --box 2050,700,2500,1100 --zoom 1.5
```

Ask of each: does the ground read as *outside* the settlement, as bare waste ground rather than a field, as *disused* at county tier, as on the road past the stone, and as a visibly different place from the burial cluster?

# Quickstart: verifying the land-use overlay grounding

All commands run from `/gm-assistant/.claude/skills/diagram/`.

## 1. The dike-pond overlay is gone

```sh
python3 -c "from settlement import KNOBS; print(KNOBS['land_use_overlay'].values)"
# -> ['none', 'lotus', 'tea_fringe']
```

Pinning the removed value must raise, not warn:

```sh
python3 -c "
from settlement import Settlement
s = Settlement(W=800, H=800, seed=1)
s.pin_knob('land_use_overlay', 'mulberry_fishpond')
s.resolve('land_use_overlay')
"
# -> ValueError
```

The dike-pond system is still reachable where it belongs:

```sh
python3 -c "from settlement import KNOBS; print('mulberry_dike_fishpond' in KNOBS['field_archetype'].values)"
# -> True
```

## 2. Lotus sits only on wet ground

Regenerate a lotus map and run the gate:

```sh
python3 pool/rolled-a.gen.py && python3 check_village.py pool/rolled-a.json
# -> ALL CHECKS PASSED
```

Then check placement independently of the gate - every lotus centroid must appear in `wet_plots`:

```sh
python3 -c "
import json
d = json.load(open('pool/rolled-a.json'))
wet = {tuple(p) for p in d['wet_plots']}
lot = [r for r in d['land_use'] if r['overlay'] == 'lotus']
off = [p for r in lot for p in r['plots'] if tuple(p) not in wet]
print('lotus plots:', sum(len(r['plots']) for r in lot), 'off wet ground:', len(off))
"
# -> off wet ground: 0
```

## 3. The closing bookend (Principle XII)

The above proves internal consistency only. Read the rendered images and judge them as pictures:

```sh
# pool/rolled-a.png       - lotus must be confined to the low bottom ground on the drain,
#                           contiguous with it, NOT scattered across the upper field
# pool/kuwabata.png       - the dike-pond landscape must read as a whole converted district,
#                           not as ponds sprinkled among rice
```

A map that passes step 2 and fails this step is exactly the failure mode Principle XII exists for.

## 4. Full gate

```sh
ruff check . && ruff format --check . && mypy --strict settlement.py check_village.py waterfields.py
python3 -m pytest -q   # must be 100% coverage
```

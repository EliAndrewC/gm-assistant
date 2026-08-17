"""The village population distribution and the homestead-bundle pitch.

NOT geometry, and not really _geom's business: a population roll belongs with rolling.py, which is
its only consumer. They are here because feature 025's positional cut put them here, and they are
isolated in a module of their own so that the eventual move is a one-file change - feature 116's
seats.py/byres.py precedent.

Split from settlement/_geom.py by feature 117 - see settlement/_geom/CLAUDE.md for the index.
"""

import random

# A village runs ~200-500 inhabitants, averaging ~350 (budgets.md). The spread is deliberately NOT a bell
# curve - the tails are only modestly rarer than the mode - so a generated village varies widely in size while
# still clustering on 350. Households = population / 5 (the "dwellings x5" rule). Weights sum to 100.
_VILLAGE_POP_DIST = ((200, 10), (250, 10), (300, 15), (350, 30), (400, 15), (450, 10), (500, 10))


# Ground one HOMESTEAD BUNDLE takes, in real feet, used to size a nucleated cluster's band. The
# bundle's reserved rects come to ~71 x 57 ft; `_fits` then spaces bundles by circumscribed circles
# rather than real footprints, so the effective pitch is larger again. See `roll_village`, which
# explains what the wrong number does and why it does not fail as a shortfall.
BUNDLE_PITCH_FT = 92.0


def village_population(rng: random.Random) -> int:
    """Draw a village population (200-500, mode 350) from the weighted distribution, using the passed
    random.Random so the draw is DETERMINISTIC from the map seed. Returns the integer population."""
    return rng.choices([p for p, _ in _VILLAGE_POP_DIST], weights=[w for _, w in _VILLAGE_POP_DIST])[0]

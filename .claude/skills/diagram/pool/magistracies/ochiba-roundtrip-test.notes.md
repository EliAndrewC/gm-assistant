# ochiba-roundtrip-test - design notes (round-trip TEST artifact)

This is NOT a replacement for `ochiba-magistracy.svg`. It is the OUTPUT of feeding the
EXISTING hand-authored Ochiba's real program (envelope, court-spine, and building masses
measured off the finished map at 3 px = 1 ft) back through the perimeter-first placer
([`../compound.py`](../compound.py), feature 008), to test whether the placer composes
Ochiba the way the GM hand-composed it.

Regenerate: `python3 pool/magistracies/ochiba-roundtrip-test.gen.py` (from the skill dir). The program lives
in [`ochiba-roundtrip-test.gen.py`](ochiba-roundtrip-test.gen.py) as `ochiba_program()`.

Garden pavilions and point features (bath, wells, latrines, porch, privy, fire-tubs) are NOT
massed perimeter buildings - they are hand-placed in the final map regardless - so they are
omitted here; the placer only arranges the wall-ranging masses.

## What the test found (and drove)

The FIRST round-trip (before the placer fixes) placed 14 of 15 and dropped `residence (E)`,
exposing two real limits in the old placer: it could not rank the servants BEHIND the
residence (it only hugged walls), and its crude per-court corner reservation let a short
building block a whole corner it did not occupy. Those two findings drove the feature-008
placer rework:

1. **Second rank.** A building can be tagged `rank=2`; it sits offset inward past the rank-1
   row on its wall. Ochiba's servants (`rank=2`, N wall) now form the rear service strip
   BEHIND the residence, exactly as the hand-map ranks them.
2. **2-D collision + placement tiers.** The corner reservation is gone. Buildings are placed
   in tiers - N/S rows first (they own the corners), then E/W columns (which flow BELOW the
   N/S buildings), then the divider hall last (which flows CENTERED between the E/W columns) -
   each sliding along its wall past every obstacle via real rectangle overlap.

## Result: the placer now reproduces Ochiba

With both fixes it places all 15 with zero overflow, and the composition matches the
hand-authored map: the residence owns the N corners, the kitchen flows below the NW corner,
the servants rank behind the residence, the karo backs the divider, the Inari shrine +
cinnabar workshop hug the E wall, and in the outer court the office hall sits centered behind
the oshirasu with the tax-archive column on the W wall and the granary/barracks/cell column on
the E wall. Coverage 36%, perimeter-hugging 61%.

## Verdict

The live `ochiba-magistracy.svg` is UNCHANGED - this remains a scaffold/test artifact, because
the finished map carries particulars the placer does not (the two-block flying-geese massing,
the garden bath pavilion, altars/relics/annotations, wells, latrines, fire-tubs). But the
round-trip achieved its goal: the placer can now express a fully-composed residential court,
not just an administrative one. A NEW manor can start from a draft like this and be
hand-refined, and the residential-court composition will already be right.

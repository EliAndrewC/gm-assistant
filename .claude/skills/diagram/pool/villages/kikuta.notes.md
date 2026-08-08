# Design notes: Kikuta, the ROLL-ENGINE village

*Reconstructed 2026-08-08 from the generator's docstring and comments. Everything below is sourced
from `kikuta.gen.py`.*

**Subject**: an average farming village, regenerated from scratch on the **feature-005 roll engine**.

**Why it exists, and what makes it different from every other village in the pool**: almost nothing
here was chosen by hand. The cluster's position and shape, the internal lane skeleton (and therefore
the headman's seat), the water source, the paddy grain and plot texture, the field archetype and any
land-use overlay are all **ROLLED from the seed** by `s.roll_village`. No coordinate in the gen was
picked by a person. That is the entire point of the map: it is the knob engine's demonstration, and
the shortest gen in the pool (106 lines) because of it.

Read that as a constraint when reviewing: a feature sitting somewhere odd here is usually the roll,
not an authoring choice, and the fix belongs in the knob's `typing_rule` rather than in a coordinate.

## The two FIXED facts, both GM-set

| Fact | Value | Why |
|---|---|---|
| Fall | NW-high, water falls SOUTH-EAST (`down_deg=45`) | the one piece of terrain the roll is not allowed to choose |
| The shrine | **Shrine to Benten with a SEVEN-torii sando**, the village burial ground in the same precinct | the priestess performs the funerary rites. "This is what keeps Kikuta Kikuta" - its identity against Hoshigaoka, which the twin-detector reads |

Seven arches is canonical, not decorative: an approach carries either 1-2 arches or exactly 7, never
3-6.

## Review log

- **2026-08-08 RNG re-roll** (positional/scoped randomness, engine-wide). Kikuta needed no fixes -
  it was already among the first maps to come out **fully isolated** (0 of 69 manifest keys drift
  from an upstream change in draw count) once a farmhouse's rake and kura became position-seeded.
- **2026-08-08 caption pass.** "Shrine to Benten" dropped from 13 pt to 9 pt with every other
  religious hall caption. At 13 it was drawn wider than the 88x60 ft hall it names, beside 9-11 pt
  neighbors on a map whose glyphs are half a city's size.

## Known open

- **No `notes.md` existed for this map until 2026-08-08**, so anything settled between its authoring
  and that date lives only in gen comments and may not be recorded here. Treat gaps as unrecorded
  rather than as decided.

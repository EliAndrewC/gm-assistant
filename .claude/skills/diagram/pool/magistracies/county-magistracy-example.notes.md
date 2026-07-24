# county-magistracy-example - design notes (placer worked example)

This is NOT a hand-authored map. It is the worked-example OUTPUT of the perimeter-first
placer ([`../compound.py`](../compound.py), feature 008): `county_magistracy_program()`
declares a generic county magistracy entirely in FEET (envelope, the reserved court-spine,
and buildings sized in feet with wall tags), and `place()` + `emit_svg()` compose it.

Regenerate: `python3 pool/magistracies/county-magistracy-example.gen.py` (from the skill dir).

Purpose: demonstrate that the toolchain can get the COMPOSITION right - buildings ring the
walls (~56% perimeter-hugging), the garden -> oshirasu -> forecourt court-spine is held open
in the center (plus the practice ground beside the barracks, per the buildings.md program
item: a keiko-earth zone the placer reserves like any spine court, emitted with its weapon
rack and two tategi striking-post markers; the hand-refined map moves the rack flush to the
adjacent lodging's wall), coverage lands in the jin'ya band (38%), and nothing overflows. It is a
SCAFFOLD: a real magistracy starts from a draft like this and is hand-refined into a final
pool SVG (particulars, relics, annotations, the scale bar, and the crop are added by hand).

Not run through building-review / size-audit as a finished map (it is a placer example, not a
finished instance); the packing/composition metrics are checked via pack_audit.

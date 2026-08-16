"""Water-first paddy engine (warp threads) for the /diagram settlement maps.

THE INVERSION (why this module exists): fields are grown AROUND the water network, never
the other way round. The generator lays the irrigation skeleton first - one pond sluice, a
head-race, supply canals along the HIGH margins, delivery ditches dropping downhill - and
the paddy plots are carved BETWEEN those lines, so the map cannot help but communicate the
hydrology. The old approach (draw a field blob, decorate it with water) reads as random no
matter how it is tuned; see settlements.md 'Water-first fields v2' for the full grounding.

ENGINE: every plot-column boundary is a warp THREAD marched downhill in lockstep fall-steps,
clamped so threads can never cross and never pinch closer than one plot width (GAP). The
blue delivery ditch is just a thread's dug PREFIX; below it the same line continues as a
plain bund. Offtakes SPAWN from their parent thread mid-march, so they always take off
exactly on the parent's real path. Crossings and orphan ditches are impossible by
construction - the geometry is validated by how it is built, not by post-hoc repair.

SLOPE IS A KNOB, NOT A CONSTANT: everything is computed in the contour(u)/fall(f) frame
derived from `down_deg` (screen angle of the downhill direction). Kikuta is NW-high
(down_deg=45, i.e. SE); southern Lion lands slope south-to-north (down_deg=-90 -> N is a
future case); Dragon the reverse; Unicorn east-flowing. Nothing in the thread march or the
plot carve assumes SE. (The drain and the supply canals are given headings RELATIVE to
`down_deg`, so the whole system rotates together.)

Returns plain data (channels, plots, stats); the caller draws SVG via Settlement. RNG is a
LOCAL random.Random(seed) so field generation never ripples other features' placement.
"""

# DERIVED SURFACE (feature 110, constitution clause 14): the star imports ARE the re-export
# mechanism - every submodule's public names resolve from the package root exactly as they did
# from the monolith. The aliased block carries the underscore names with external consumers
# (settlement/fields.py, test_hamletgen.py, test_settlement/test_core.py); guard:
# test_waterfields_surface.py. Never add logic here.
from .banks import *
from .carve import *
from .carve import _bund_beans as _bund_beans
from .comb import *
from .frame import *
from .frame import _Frame as _Frame
from .frame import _miter_normals as _miter_normals
from .frame import _seg_d as _seg_d
from .palette import *
from .palette import _RICE_GREEN as _RICE_GREEN
from .polder import *

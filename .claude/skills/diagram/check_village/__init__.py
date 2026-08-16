"""Automated checks for a Mode B settlement-map manifest (diagram skill).

Reads the JSON manifest the generator emits and asserts the Mode B rules. The
UNIVERSAL invariants (no overlaps, houses off corridors and field-adjacent, every
field ringed, no cultivation on a hill, houses face south, headman largest,
channels anchored at both ends and gently winding) are always checked. The
VILLAGE-SPECIFIC expectations are read from manifest["meta"] and from each
channel's frm/to anchors, so this validator works for any village/hamlet rather
than assuming one village's layout. Exit 0 if all pass, 1 otherwise.

The skill's plain-English / persona review still applies on top of this gate -
and remember a green check on the wrong geometry is worse than no check, so the
manifest records the *rendered* (smoothed) boundary and you still eyeball a crop.

Many checks are pure rendering/geometry (no overlaps, lanes layered, labels clear) and need no
justification. But where a check encodes a HISTORICAL or SETTING finding - who lives where, well
densities, the Shinto/Buddhist split, caste geography, the commerce-fronts-the-street pattern - the
reasoning (the "why") lives in settlements.md's "Historical grounding: the why behind the realism checks"
section; such checks below carry a brief `# WHY:` pointer to it. (Project policy: research-driven
rules record their why next to the rule - see CLAUDE.md "Generation Behavior".)

Package surface (feature 027, superseding 024's verbatim roster): the star imports
below re-export every submodule's public names - mypy treats star-imported public
names as explicitly exported even under strict's no_implicit_reexport, so no
__all__ is needed (probe-verified against mypy 2.3.0; see
specs/027-init-star-imports/research.md R1). The previous ~3,000 lines of explicit
import rosters plus a duplicate __all__ roster said nothing the stars do not say,
and cost every reader the whole roster to learn it. The six underscore names with
external consumers are re-exported via the `as`-alias idiom below; every other
underscore name is package-private - if something outside the package genuinely
needs one, add it to the aliased block (or import it from its submodule directly).
test_check_village_surface.py guards the two properties this design relies on:
no silent star-import shadowing across submodules (no public name bound to two
different objects), and the consumed surface (census:
specs/027-init-star-imports/census.md) keeps resolving.
"""

from .common_01_geometry import *
from .common_01_geometry import (
    _LABEL_EXEMPT as _LABEL_EXEMPT,
)
from .common_01_geometry import (
    _LABEL_GROUP as _LABEL_GROUP,
)
from .common_01_geometry import (
    _MATRIX_OUTSTANDING as _MATRIX_OUTSTANDING,
)
from .common_01_geometry import (
    _OVERLAP_EXEMPT as _OVERLAP_EXEMPT,
)
from .common_01_geometry import (
    _OVERLAP_STRUCTS as _OVERLAP_STRUCTS,
)
from .common_02_overlap_policy import *
from .common_02_overlap_policy import _ward_interior as _ward_interior
from .common_03_capacity import *
from .driver import *
from .registry import *
from .segments_01_city_frame_and_yards import *
from .segments_02_capital_and_walls import *
from .segments_03_structures_and_wards import *
from .segments_04_homesteads import *
from .segments_05_fields_and_funerary import *
from .segments_06_ways_and_bridges import *
from .segments_07_water import *
from .segments_08_town_and_fire import *
from .segments_09_justice_and_tanning import *
from .segments_10_city_battery_a import *
from .segments_10_city_battery_b import *
from .segments_10_city_battery_c import *
from .segments_11_polders_and_edges import *

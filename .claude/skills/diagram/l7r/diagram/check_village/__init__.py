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
tests/check_village/test_surface.py guards the two properties this design relies on:
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
from .segments_01a_city_ring_and_frame import *
from .segments_01b_quarters_and_civic_reserve import *
from .segments_01c_work_yards_and_matrix import *
from .segments_02a_capital_budget_and_ministries import *
from .segments_02b_capital_ways_and_burial import *
from .segments_02c_walls_gates_and_housing import *
from .segments_03a_overlaps_and_ward_fences import *
from .segments_03b_structures_vs_water_and_streets import *
from .segments_03c_clusters_and_labels import *
from .segments_04a_margins_lanes_and_wells import *
from .segments_04b_yards_gardens_and_sheds import *
from .segments_04c_groves_and_shading import *
from .segments_05a_field_cover_and_cremation import *
from .segments_05b_graveyards_and_channel_sources import *
from .segments_05c_streams_and_field_ditches import *
from .segments_05d_supply_roadways_and_commons import *
from .segments_06a_bridges_and_gate_roads import *
from .segments_06b_bridge_labels_and_reach import *
from .segments_06c_decks_yards_and_moat_clearances import *
from .segments_07a_channels_and_bridge_spans import *
from .segments_07b_ponds_hems_and_land_fall import *
from .segments_07c_moats_drains_and_edges import *
from .segments_08a_ponds_marshes_and_drainage import *
from .segments_08b_flow_bands_and_the_burakumin_seam import *
from .segments_08c_town_trades_and_theater import *
from .segments_08d_kosatsuba_and_paddy_basins import *
from .segments_09a_justice_grounds_and_land_fall import *
from .segments_09b_tanning_yards import *
from .segments_10a_city_castes_and_dojos import *
from .segments_10b_city_civic_and_commerce import *
from .segments_10c_city_gates_and_wall_towers import *
from .segments_10d_city_temples_and_estates import *
from .segments_10e_city_governor_and_quarters import *
from .segments_10f_city_labels_and_works import *
from .segments_10g_city_streets_and_docks import *
from .segments_10h_city_torii_and_estate_grounds import *
from .segments_11a_taxfree_terraces_and_dikeponds import *
from .segments_11b_polder_dikes_and_waivers import *

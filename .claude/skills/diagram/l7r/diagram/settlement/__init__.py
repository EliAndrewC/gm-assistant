"""Settlement-map library for the diagram skill (Mode B).

The TRULY COMMON machinery for drawing Rokugani village/hamlet plans lives here:
the palette, organic fields with irregular crop basins, south-facing house glyphs,
hills + shrines + torii, ponds/streams/channels, size-aware house placement, and
the JSON manifest that check_village.py validates.

A specific settlement (see kikuta.gen.py, hikari-no-sato.gen.py) is a thin
script: it instantiates Settlement, declares its fields/water/shrine/houses, and
calls finish(). What varies village to village - number and shape of fields, the
irrigation source (pond vs stream vs field-to-field), torii count, whether a hill
carries the shrine, whether blight left abandoned houses - is passed in, not baked
here. Those declarations are echoed into manifest["meta"] so the validator can
adapt its checks per village instead of assuming one village's specifics.
"""

from ._geom import BUNDLE_PITCH_FT as BUNDLE_PITCH_FT
from ._geom import FARMHOUSE_EAVE_GAP_FT as FARMHOUSE_EAVE_GAP_FT
from ._geom import GOVERNOR_CAPTION_FS as GOVERNOR_CAPTION_FS
from ._geom import HALL_CAPTION_FS as HALL_CAPTION_FS
from ._geom import LABEL_AIR_CAP as LABEL_AIR_CAP
from ._geom import LABEL_MIN_AIR as LABEL_MIN_AIR
from ._geom import LANDING_FT as LANDING_FT
from ._geom import PLANK_ABUTMENT as PLANK_ABUTMENT
from ._geom import PLANK_BANK_REACH as PLANK_BANK_REACH
from ._geom import TORII_PITCH_FT as TORII_PITCH_FT
from ._geom import Indexed as Indexed
from ._geom import PointGrid as PointGrid
from ._geom import SeatMemo as SeatMemo
from ._geom import _assert_not_main_tree as _assert_not_main_tree
from ._geom import _union_area as _union_area
from ._geom import box_gap as box_gap
from ._geom import boxed_grid as boxed_grid
from ._geom import boxed_hit as boxed_hit
from ._geom import boxed_polys as boxed_polys
from ._geom import boxed_seg_hit as boxed_seg_hit
from ._geom import boxed_segs as boxed_segs
from ._geom import edge_dist as edge_dist
from ._geom import fillet_polyline as fillet_polyline
from ._geom import forest_frame_span as forest_frame_span
from ._geom import forest_reveal_x as forest_reveal_x
from ._geom import kido_bar_deg as kido_bar_deg
from ._geom import label_aabb as label_aabb
from ._geom import label_quad as label_quad
from ._geom import label_tilt as label_tilt
from ._geom import lane_runs as lane_runs
from ._geom import lane_through_gate as lane_through_gate
from ._geom import linear_tilt as linear_tilt
from ._geom import linear_tilt_full as linear_tilt_full
from ._geom import paddy_wet_rings as paddy_wet_rings
from ._geom import point_in_poly as point_in_poly
from ._geom import point_quad_dist as point_quad_dist
from ._geom import poly_gap as poly_gap
from ._geom import quad_hits_seg as quad_hits_seg
from ._geom import rail_quad as rail_quad
from ._geom import rects_overlap as rects_overlap
from ._geom import region_blocked as region_blocked
from ._geom import ring_touches as ring_touches
from ._geom import rot_rect as rot_rect
from ._geom import sat_overlap as sat_overlap
from ._geom import seg_closest as seg_closest
from ._geom import seg_dist as seg_dist
from ._geom import seg_in_ellipse_core as seg_in_ellipse_core
from ._geom import seg_intersect as seg_intersect
from ._geom import segments_cross as segments_cross
from ._geom import street_runs as street_runs
from ._geom import stroke_quads as stroke_quads
from ._geom import tilt_caption_seat as tilt_caption_seat
from ._geom import torii_halfbox as torii_halfbox
from ._geom import torii_wall_conflicts as torii_wall_conflicts
from ._geom import tower_quad as tower_quad
from ._geom import trough_quad as trough_quad
from ._geom import village_population as village_population
from ._geom import ward_interior as ward_interior
from ._geom import way_beds as way_beds
from ._geom import wellhead_quad as wellhead_quad
from ._knobs import BOUNDARY_MARKER_FT as BOUNDARY_MARKER_FT
from ._knobs import BOUNDARY_MARKER_MIN_PX as BOUNDARY_MARKER_MIN_PX
from ._knobs import BOUNDARY_STONE_CLEAR_FT as BOUNDARY_STONE_CLEAR_FT
from ._knobs import EXECUTION_GROUND_DEAD_CLEAR_FT as EXECUTION_GROUND_DEAD_CLEAR_FT
from ._knobs import KIDO_TOWER_KEEPCLEAR as KIDO_TOWER_KEEPCLEAR
from ._knobs import KNOBS as KNOBS
from ._knobs import KOSATSUBA_MARKER_MIN_PX as KOSATSUBA_MARKER_MIN_PX
from ._knobs import LANE_SKELETONS as LANE_SKELETONS
from ._knobs import LANE_WEBS as LANE_WEBS
from ._knobs import MERCHANT_ESTATE_WEIGHTS as MERCHANT_ESTATE_WEIGHTS
from ._knobs import PUNISHMENT_SPOT_FT as PUNISHMENT_SPOT_FT
from ._knobs import WALL_DEFENSE as WALL_DEFENSE
from ._knobs import Knob as Knob
from ._knobs import _centroid as _centroid
from ._knobs import _sharp_corners as _sharp_corners
from ._knobs import bridge_carried_ways as bridge_carried_ways
from ._knobs import bridge_crossed_waters as bridge_crossed_waters
from ._knobs import crop_boxes as crop_boxes
from ._knobs import execution_ground_ft as execution_ground_ft
from ._knobs import knob_rng as knob_rng
from ._knobs import machi_mouths as machi_mouths
from ._knobs import moat_current_at as moat_current_at
from ._knobs import moat_swept_tap as moat_swept_tap
from ._knobs import register_knob as register_knob
from ._knobs import resolve_knob as resolve_knob
from ._knobs import roll_merchant_estate_count as roll_merchant_estate_count
from ._knobs import roll_torii_count as roll_torii_count
from ._knobs import scope_seed as scope_seed
from ._knobs import skeleton_layout as skeleton_layout
from ._knobs import wall_tower_spacing_px as wall_tower_spacing_px
from ._knobs import web_cuts as web_cuts
from .core import Settlement as Settlement
from .land import surface_water_dist as surface_water_dist
from .shrines_wells import COURTYARD_REACH as COURTYARD_REACH
from .shrines_wells import courtyard_annex_span as courtyard_annex_span

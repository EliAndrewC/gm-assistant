"""Gate checks for supply roadways, commons, graveyards and channel sources (test_segments_05_fields_and_funerary split by feature 122; tests verbatim)."""

from l7r.diagram import check_village
from tests.check_village._builders import (
    _MOAT,
    _PADDY,
    WALL,
    _city_dead,
    _crem_cem,
    _crem_road,
    _crem_temple,
    _paddy_field_rec,
    _town_dead,
    _water_grave,
    bldg,
    f,
    manifest,
)


# ---- field_ditches_reach_source_and_sink (role-aware: supply->source, drain->sink) ----------
def test_walled_graveyards_inside_and_outside_passes_when_mixed():
    assert "walled_graveyards_inside_and_outside" not in f(_city_dead())


def test_walled_exterior_cemetery_larger_fires_when_not_larger():
    # the outside common ground is no bigger than the cramped intramural one
    assert "walled_exterior_cemetery_larger" in f(_city_dead(cems=[(300, 300), (700, 300), (100, 100, 60, 40)]))


def test_walled_exterior_cemetery_larger_passes_when_larger():
    assert "walled_exterior_cemetery_larger" not in f(_city_dead())


def test_cemetery_in_temple_precinct_exempts_a_nonparish_grave():
    # an inside graveyard far from any temple is exempt when parish=False (a non-parish plot)
    assert "cemetery_in_temple_precinct" not in f(_city_dead(cems=[(300, 300), (700, 300), (100, 100), (500, 500, 60, 44, False)]))


def test_cemetery_in_temple_precinct_fires_on_an_inside_parish_grave_off_temple():
    assert "cemetery_in_temple_precinct" in f(_city_dead(cems=[(300, 300), (700, 300), (100, 100), (500, 500, 60, 44, True)]))


def test_funerary_set_back_from_water_fires_near_a_stream():
    assert "funerary_set_back_from_water" in f(_water_grave({"streams": [{"poly": [[300, 340], [600, 340]], "frm": None, "to": None, "w": 9}]}))


def test_funerary_set_back_from_water_fires_near_a_pond():
    assert "funerary_set_back_from_water" in f(_water_grave({"pond": [400, 300, 60, 40]}))


def test_funerary_set_back_from_water_passes_when_clear_of_water():
    assert "funerary_set_back_from_water" not in f(_water_grave({"streams": [{"poly": [[300, 600], [600, 600]], "frm": None, "to": None, "w": 9}], "pond": [900, 900, 60, 40]}))


def test_funerary_set_back_scales_grave_ok_by_a_stream_fails_by_a_moat():
    # a graveyard whose nearest corner is 90px from the watercourse: fine by a narrow stream (floor 75),
    # too close to a moat (set-back 110)
    def M(width):
        return {
            "meta": {"scale": "village"},
            "cemeteries": [{"x": 300, "y": 270, "w": 50, "h": 36, "rot": 0, "parish": True}],
            "streams": [{"poly": [[200, 378], [600, 378]], "frm": None, "to": None, "w": width}],
        }

    assert "funerary_set_back_from_water" not in f(M(6))  # narrow stream: floor 75, corner 90px away -> ok
    assert "funerary_set_back_from_water" in f(M(22))  # moat-width: set-back 110 -> 90px too close


def test_funerary_set_back_cremation_may_sit_nearer_than_a_grave():
    # at the SAME 50px corner distance from a wide watercourse: the cremation ground passes, a graveyard fires
    base = {"meta": {"scale": "village"}, "streams": [{"poly": [[200, 378], [600, 378]], "frm": None, "to": None, "w": 22}]}
    grave = {**base, "cemeteries": [{"x": 300, "y": 310, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    crem = {**base, "cremation_grounds": [{"x": 300, "y": 288, "w": 116, "h": 80, "rot": 0}]}
    assert "funerary_set_back_from_water" in f(grave)
    assert "funerary_set_back_from_water" not in f(crem)


def test_funerary_set_back_inside_wall_grave_exempt_from_moat():
    # a graveyard just inside the wall is shielded from the (outside) moat by the rampart -> exempt
    WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]
    M = {"meta": {"scale": "city"}, "wall": WALLSQ, "moat": _MOAT, "moat_width": 22, "cemeteries": [{"x": 230, "y": 500, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    assert "funerary_set_back_from_water" not in f(M)


def test_funerary_set_back_outside_wall_grave_subject_to_moat():
    WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]
    M = {"meta": {"scale": "city"}, "wall": WALLSQ, "moat": _MOAT, "moat_width": 22, "cemeteries": [{"x": 120, "y": 500, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    assert "funerary_set_back_from_water" in f(M)


def test_funerary_set_back_fires_near_a_rice_paddy():
    # a burial ground hard against a flood-prone paddy edge
    M = {"meta": {"scale": "village"}, "fields": [_PADDY], "cemeteries": [{"x": 300, "y": 300, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    assert "funerary_set_back_from_water" in f(M)


def test_funerary_set_back_paddy_needs_more_than_creek_distance():
    # ~35px from a paddy edge: fine for a creek, but a flooded paddy needs a real margin -> still fires
    near = {"meta": {"scale": "village"}, "fields": [_PADDY], "cemeteries": [{"x": 300, "y": 277, "w": 50, "h": 36, "rot": 0, "parish": True}]}  # corner ~35px from the paddy
    assert "funerary_set_back_from_water" in f(near)
    far = {"meta": {"scale": "village"}, "fields": [_PADDY], "cemeteries": [{"x": 300, "y": 255, "w": 50, "h": 36, "rot": 0, "parish": True}]}  # corner ~57px -> clear
    assert "funerary_set_back_from_water" not in f(far)


def test_funerary_set_back_cremation_may_sit_by_a_paddy():
    # the cremation ground is exempt from the paddy set-back (a fire site, not flood-sensitive graves)
    M = {"meta": {"scale": "village"}, "fields": [_PADDY], "cremation_grounds": [{"x": 300, "y": 280, "w": 116, "h": 80, "rot": 0}]}
    assert "funerary_set_back_from_water" not in f(M)


def test_cremation_ground_by_external_cemetery_passes_when_adjacent():
    assert "cremation_ground_by_external_cemetery" not in f(_crem_cem((300, 300), (300, 420)))


def test_cremation_ground_by_external_cemetery_fires_when_far():
    assert "cremation_ground_by_external_cemetery" in f(_crem_cem((300, 300), (900, 900)))


def test_cremation_ground_by_external_cemetery_fires_when_only_internal_cemetery():
    # walled: cremation outside, but the only cemetery is INSIDE the wall (even adjacent) -> not external -> fires
    assert "cremation_ground_by_external_cemetery" in f(_crem_cem((150, 500), (250, 500), walled=True))


def test_cremation_ground_by_external_cemetery_passes_walled_with_external():
    # walled: cremation + cemetery both outside the wall, adjacent -> ok
    assert "cremation_ground_by_external_cemetery" not in f(_crem_cem((150, 500), (150, 620), walled=True))


def test_cremation_set_back_from_road_fires_when_on_the_road():
    assert "cremation_ground_set_back_from_main_road" in f(_crem_road((300, 260), (300, 360)))  # 60px off the road


def test_cremation_set_back_from_road_passes_when_far():
    assert "cremation_ground_set_back_from_main_road" not in f(_crem_road((300, 500), (300, 600)))


def test_cremation_set_back_from_road_passes_when_no_main_road():
    M = _crem_road((300, 260), (300, 360))
    del M["road"]  # a settlement on minor streets only - nothing to be set back from
    assert "cremation_ground_set_back_from_main_road" not in f(M)


def test_cremation_not_between_temple_and_road_fires_when_between():
    # cremation on the road side of its monastery (closer to the road than the temple), yet still
    # clear of the road's own set-back floor - only the between-temple-and-road rule should object
    fails = f(_crem_temple((300, 360)))
    assert "cremation_ground_not_between_temple_and_road" in fails
    assert "cremation_ground_set_back_from_main_road" not in fails  # isolates the new rule


def test_cremation_not_between_temple_and_road_passes_when_behind():
    assert "cremation_ground_not_between_temple_and_road" not in f(_crem_temple((300, 640)))


def test_cremation_not_between_temple_and_road_passes_when_no_temple_nearby():
    # no temple within association range -> nothing to be "in front of"
    assert "cremation_ground_not_between_temple_and_road" not in f(_crem_temple((300, 360), mon_xy=(300, 1500)))


def test_city_temples_have_graveyards_fires_when_a_temple_unserved():
    assert "city_temples_have_graveyards" in f(_city_dead(temples=[(320, 320, "A", True), (680, 700, "B", True)]))


def test_city_temples_have_graveyards_exempts_a_flagged_temple():
    assert "city_temples_have_graveyards" not in f(_city_dead(temples=[(320, 320, "A", True), (680, 700, "B", False)]))


def test_city_has_mausoleum_fires_when_missing():
    assert "city_has_mausoleum" in f(_city_dead(maus=[]))


def test_city_has_mausoleum_fires_when_outside_walls():
    assert "city_has_mausoleum" in f(_city_dead(maus=[(100, 100)]))


def test_city_has_mausoleum_fires_when_far_from_quarter():
    assert "city_has_mausoleum" in f(_city_dead(maus=[(260, 740)], gov=(740, 260)))


def test_city_has_mausoleum_passes_when_by_quarter():
    assert "city_has_mausoleum" not in f(_city_dead())


def test_city_has_cremation_ground_fires_when_inside_walls():
    assert "city_has_cremation_ground" in f(_city_dead(crem=[(500, 400)]))


def test_city_has_cremation_ground_passes_when_outside():
    assert "city_has_cremation_ground" not in f(_city_dead())


def test_city_has_ossuary_fires_when_far_from_cremation():
    assert "city_has_ossuary" in f(_city_dead(oss=[(900, 100)]))


def test_city_has_ossuary_passes_when_by_cremation():
    assert "city_has_ossuary" not in f(_city_dead())


def test_town_has_cremation_ground_fires_when_missing():
    assert "town_has_cremation_ground" in f(_town_dead([]))


def test_town_has_cremation_ground_fires_when_among_dwellings():
    assert "town_has_cremation_ground" in f(_town_dead([(320, 300)]))


def test_town_has_cremation_ground_passes_when_at_the_edge():
    assert "town_has_cremation_ground" not in f(_town_dead([(900, 900)]))


def test_sacred_and_graves_off_marsh_fires_and_passes_on_dry_ground():
    # a shrine hall or a graveyard must NOT sit on a reed marsh (the wet valley toe) - only on dry ground.
    marsh = [[400, 400], [700, 400], [700, 700], [400, 700]]  # a toe marsh
    base = {"meta": {"scale": "village"}, "houses": [bldg(200, 200, "laborer")], "marshes": [{"x": 550, "y": 550, "w": 300, "h": 300, "role": "toe", "poly": marsh}]}
    on_shrine = {**base, "religious": [{"x": 550, "y": 550, "w": 96, "h": 64, "kind": "shrine"}]}
    assert "sacred_and_graves_off_marsh" in f(on_shrine)
    on_grave = {**base, "cemeteries": [{"x": 560, "y": 560, "w": 82, "h": 58, "rot": 0}]}
    assert "sacred_and_graves_off_marsh" in f(on_grave)
    dry = {**base, "religious": [{"x": 900, "y": 900, "w": 96, "h": 64, "kind": "shrine"}], "cemeteries": [{"x": 1000, "y": 1000, "w": 82, "h": 58, "rot": 0}]}
    assert "sacred_and_graves_off_marsh" not in f(dry)
    # a pond_fringe (thin decorative shore ring) is exempt - a shrine may sit beside a pond
    fringe = {**base, "marshes": [{"x": 550, "y": 550, "w": 300, "h": 300, "role": "pond_fringe", "poly": marsh}], "religious": [{"x": 550, "y": 550, "w": 96, "h": 64, "kind": "shrine"}]}
    assert "sacred_and_graves_off_marsh" not in f(fringe)


# ---- channel_source_anchored: a channel that claims a FOREST source ------------------------
# A watercourse anchor of kind "forest" is grounded iff a forest polygon exists AND the anchor
# point lies inside it. A channel declaring a forest source whose tap sits OUTSIDE the drawn
# forest is ungrounded and must fire (exercises the forest branch of anchored()).
def test_channel_source_anchored_fires_when_forest_tap_is_outside_the_forest():
    M = {
        "forest": [[100, 100], [300, 100], [300, 300], [100, 300]],
        "channels": [{"poly": [[500, 500], [510, 400], [520, 300]], "frm": {"kind": "forest"}, "to": {"kind": "offmap"}}],
    }
    assert "channel_source_anchored[0]" in f(M)


# ---- roads_clear_of_marsh / pond_clear_of_paddies / no_structure_on_paddy (GM, Hoshizora 2026-07) ----
def test_roads_clear_of_marsh_fires_when_the_road_runs_through_a_reed_fringe():
    M = {"meta": {}, "road": [[100, 500], [900, 500]], "marshes": [{"x": 500, "y": 500, "w": 120, "h": 80, "poly": [[440, 460], [560, 460], [560, 540], [440, 540]]}]}
    assert "roads_clear_of_marsh" in f(M)


def test_roads_clear_of_marsh_passes_when_the_marsh_sits_off_the_road():
    M = {"meta": {}, "road": [[100, 500], [900, 500]], "marshes": [{"x": 500, "y": 700, "w": 120, "h": 80, "poly": [[440, 660], [560, 660], [560, 740], [440, 740]]}]}
    assert "roads_clear_of_marsh" not in f(M)


def test_pond_clear_of_paddies_fires_when_the_pond_laps_the_crop():
    M = {"meta": {}, "pond": [320, 320, 80, 60], "fields": [_paddy_field_rec()]}
    assert "pond_clear_of_paddies" in f(M)


def test_pond_clear_of_paddies_passes_when_the_pond_sits_beside_the_crop():
    M = {"meta": {}, "pond": [120, 120, 60, 40], "fields": [_paddy_field_rec()]}
    assert "pond_clear_of_paddies" not in f(M)


def test_roads_clear_of_marsh_skips_a_degenerate_marsh_poly():
    # a marsh record whose poly is a bare 2-point sliver carries no area to test - skipped, no crash
    M = {"meta": {}, "road": [[100, 500], [900, 500]], "marshes": [{"x": 500, "y": 500, "w": 10, "h": 10, "poly": [[490, 495], [510, 505]]}]}
    assert "roads_clear_of_marsh" not in f(M)


def test_roads_clear_of_marsh_exempts_a_defense_belt_causeway():
    # the approach road CROSSES the defensive wet belt on a causeway (the renderer keeps the tread bare via
    # the corridor skip) - few, constricted approaches are the belt's military purpose, not a placement error
    M = {"meta": {}, "road": [[100, 500], [900, 500]], "wall": WALL, "marshes": [{"x": 500, "y": 500, "w": 120, "h": 80, "role": "defense", "poly": [[440, 460], [560, 460], [560, 540], [440, 540]]}]}
    assert "roads_clear_of_marsh" not in f(M)


def test_town_monasteries_have_graveyards_fires_when_unserved():
    M = {"meta": {"scale": "town"}, "religious": [{"x": 500, "y": 500, "w": 100, "h": 70, "kind": "monastery"}]}
    assert "town_monasteries_have_graveyards" in f(M)


def test_town_monasteries_have_graveyards_passes_with_precinct_ground_or_opt_out():
    M = {"meta": {"scale": "town"}, "religious": [{"x": 500, "y": 500, "w": 100, "h": 70, "kind": "monastery"}], "cemeteries": [{"x": 560, "y": 420, "w": 80, "h": 60, "rot": 0}]}
    assert "town_monasteries_have_graveyards" not in f(M)
    M2 = {"meta": {"scale": "town"}, "religious": [{"x": 500, "y": 500, "w": 100, "h": 70, "kind": "monastery", "graveyard": False}]}
    assert "town_monasteries_have_graveyards" not in f(M2)


def test_town_has_ossuary_fires_when_missing():
    M = {"meta": {"scale": "town"}, "cremation_grounds": [{"x": 200, "y": 800, "w": 75, "h": 52, "rot": 0}]}
    assert "town_has_ossuary" in f(M)


def test_town_has_ossuary_passes_beside_the_cremation_ground():
    M = {"meta": {"scale": "town"}, "cremation_grounds": [{"x": 200, "y": 800, "w": 75, "h": 52, "rot": 0}], "ossuaries": [{"x": 260, "y": 860, "w": 20, "h": 20, "rot": 0}]}
    assert "town_has_ossuary" not in f(M)


def test_geometry_within_canvas_fires_on_a_stray_town_wall_vertex():
    M = {"meta": {"scale": "town", "W": 2000, "H": 1300}, "wall": [[300, 300], [9999999, 300], [700, 700]]}
    assert "geometry_within_canvas" in f(M)


# ---- dry_plots_off_hill (feature 013): a hill slope carries dry hill-crops/tea/woodland/scrub, never
# flooded paddy - and the near-ring dry-field tiler must not stray onto it either (no_field_on_hill
# reads only M["fields"], so this closes the dry-plot half).
def test_dry_plots_off_hill_fires_when_a_plot_sits_on_the_hill():
    M = {"meta": {"scale": "town"}, "hill": [500, 500, 200, 150], "dry_plots": [{"poly": [[480, 480], [520, 480], [520, 520], [480, 520]], "crop": "soy", "theta": 0.0}]}
    assert "dry_plots_off_hill" in f(M)


def test_dry_plots_off_hill_passes_when_plots_avoid_the_hill():
    M = {"meta": {"scale": "town"}, "hill": [500, 500, 200, 150], "dry_plots": [{"poly": [[50, 50], [90, 50], [90, 90], [50, 90]], "crop": "soy", "theta": 0.0}]}
    assert "dry_plots_off_hill" not in f(M)


# ---- comb_supply_commands_both_flanks (2026-08-16) -----------------------------------------------
# A gravity canal commands only ground BELOW it, so a comb fan planted on both sides of its
# bunsuiguchi fork must DRAW supply down both margins (research/water.md "The head-race forks -
# supply commands both flanks"). The check reads the `fork` build_comb records on the field.


def _both_flanks_manifest(arm_b=True, west_sliver=False):
    """A comb fan falling due south, fork at (500, 300): canal A inked down the east margin, plots
    on both flanks (or only a sliver on the west when `west_sliver`), canal B optional."""
    west_x = (460, 490) if west_sliver else (210, 260)
    fld = {
        "name": "f",
        "kind": "paddy",
        "down_deg": 90,
        "fork": [500.0, 300.0],
        "outline": [[200, 300], [800, 300], [800, 900], [200, 900]],
        "bbox": [200, 300, 800, 900],
        "plot_rings": [
            [[west_x[0], 340], [west_x[1], 340], [west_x[1], 390], [west_x[0], 390]],
            [[740, 340], [790, 340], [790, 390], [740, 390]],
            [[480, 600], [520, 600], [520, 640], [480, 640]],
        ],
    }
    ditches = [
        {"field": "f", "role": "main", "w": 7.0, "poly": [[500, 260], [500, 300]]},
        {"field": "f", "role": "main", "w": 6.0, "poly": [[500, 300], [700, 420], [790, 520]]},
        {"field": "f", "role": "drain", "w": 3.0, "poly": [[210, 880], [790, 880]]},
    ]
    if arm_b:
        ditches.append({"field": "f", "role": "main", "w": 5.6, "poly": [[500, 300], [350, 420], [290, 520]]})
    return manifest(fields=[fld], field_ditches=ditches)


def test_comb_supply_commands_both_flanks_fires_on_a_bare_flank():
    fails = check_village.gate(_both_flanks_manifest(arm_b=False), verbose=False, only={"comb_supply_commands_both_flanks"})
    assert "comb_supply_commands_both_flanks" in fails


def test_comb_supply_commands_both_flanks_passes_with_both_arms_inked():
    fails = check_village.gate(_both_flanks_manifest(arm_b=True), verbose=False, only={"comb_supply_commands_both_flanks"})
    assert "comb_supply_commands_both_flanks" not in fails


def test_comb_supply_commands_both_flanks_spares_a_sliver_flank():
    # under ~150 ft of paddy past the fork demands no second arm - a genuinely lopsided fan is honest
    fails = check_village.gate(_both_flanks_manifest(arm_b=False, west_sliver=True), verbose=False, only={"comb_supply_commands_both_flanks"})
    assert "comb_supply_commands_both_flanks" not in fails


def test_comb_supply_commands_both_flanks_skips_manifests_without_a_fork():
    # legacy manifests record no fork (conversion, not retrofit, is their fix - migration doctrine)
    M = _both_flanks_manifest(arm_b=False)
    del M["fields"][0]["fork"]
    fails = check_village.gate(M, verbose=False, only={"comb_supply_commands_both_flanks"})
    assert "comb_supply_commands_both_flanks" not in fails


def test_comb_supply_commands_both_flanks_skips_a_field_with_no_declared_fall():
    M = _both_flanks_manifest(arm_b=False)
    del M["fields"][0]["down_deg"]
    fails = check_village.gate(M, verbose=False, only={"comb_supply_commands_both_flanks"})
    assert "comb_supply_commands_both_flanks" not in fails


def test_comb_supply_commands_both_flanks_reads_the_map_fall_when_the_field_has_none():
    M = _both_flanks_manifest(arm_b=False)
    del M["fields"][0]["down_deg"]
    M["meta"]["down_deg"] = 90
    fails = check_village.gate(M, verbose=False, only={"comb_supply_commands_both_flanks"})
    assert "comb_supply_commands_both_flanks" in fails


# ---- woodland_commons_within_the_frame: a coppice the crop cuts off is drawn but not shown ----
def _wood_M(polys, view=(100, 100, 800, 800), gen="hamletgen", role="woodland"):
    M = {"meta": {"scale": "hamlet", "W": 1200, "H": 1200}, "commons": [{"role": role, "poly": p} for p in polys]}
    if view is not None:
        M["meta"]["view"] = list(view)
    if gen:
        M["meta"]["generated_by"] = gen
    return M


def _wood_f(M):
    return check_village.gate(M, verbose=False, only={"woodland_commons_within_the_frame"})


def test_woodland_commons_fires_on_a_parcel_wholly_outside_the_view():
    # the Sawada shape: seated above the kept window, drawn onto ground the crop discards
    assert "woodland_commons_within_the_frame" in _wood_f(_wood_M([[[0, 0], [50, 0], [50, 50], [0, 50]]]))


def test_woodland_commons_fires_on_a_parcel_mostly_outside_the_view():
    # half in, half out (50% < the 70% line): Sawada's third parcel, cropped under the title
    assert "woodland_commons_within_the_frame" in _wood_f(_wood_M([[[50, 200], [150, 200], [150, 300], [50, 300]]]))


def test_woodland_commons_passes_inside_the_view():
    assert "woodland_commons_within_the_frame" not in _wood_f(_wood_M([[[200, 200], [400, 200], [400, 400], [200, 400]]]))


def test_woodland_commons_tolerates_a_parcel_clipping_at_the_edge():
    # 75% inside: a wood CLIPPING at the frame reads as "more wood that way", which is fine
    assert "woodland_commons_within_the_frame" not in _wood_f(_wood_M([[[75, 200], [175, 200], [175, 300], [75, 300]]]))


def test_woodland_commons_ignores_the_grazing_bleed():
    # the grazing scrub deliberately bleeds off every edge - only woodland parcels are held
    assert "woodland_commons_within_the_frame" not in _wood_f(_wood_M([[[0, 0], [50, 0], [50, 50], [0, 50]]], role="grazing"))


def test_woodland_commons_ignores_a_parcel_with_no_poly():
    assert "woodland_commons_within_the_frame" not in _wood_f(_wood_M([[]]))


def test_woodland_commons_skips_an_uncropped_map():
    assert "woodland_commons_within_the_frame" not in _wood_f(_wood_M([[[0, 0], [50, 0], [50, 50], [0, 50]]], view=None))


def test_woodland_commons_skips_legacy_maps():
    assert "woodland_commons_within_the_frame" not in _wood_f(_wood_M([[[0, 0], [50, 0], [50, 50], [0, 50]]], gen=None))


# ---- woodland_commons_on_dry_ground: a coppice does not stand in the marsh --------------------
def _wood_dry_M(polys, marsh=None, gen="hamletgen", role="woodland"):
    M = _wood_M(polys, view=(0, 0, 1200, 1200), gen=gen, role=role)
    if marsh is not None:
        M["marshes"] = [{"poly": marsh}]
    return M


_TOE_MARSH = [[0, 500], [600, 500], [600, 1100], [0, 1100]]


def _wood_dry_f(M):
    return check_village.gate(M, verbose=False, only={"woodland_commons_on_dry_ground"})


def test_woodland_dry_fires_on_a_parcel_wholly_in_the_marsh():
    # the Inashiro capture: 100% wet, zero crowns of ink - an empty rectangle claiming a woodland
    assert "woodland_commons_on_dry_ground" in _wood_dry_f(_wood_dry_M([[[100, 600], [350, 600], [350, 850], [100, 850]]], marsh=_TOE_MARSH))


def test_woodland_dry_fires_on_a_parcel_mostly_in_the_marsh():
    # straddling the marsh edge, ~60% wet (the Mizuguchi capture's degree)
    assert "woodland_commons_on_dry_ground" in _wood_dry_f(_wood_dry_M([[[100, 350], [350, 350], [350, 750], [100, 750]]], marsh=_TOE_MARSH))


def test_woodland_dry_tolerates_a_marsh_fringe():
    # ~20% wet: a stand may lap the haze a little without losing its read
    assert "woodland_commons_on_dry_ground" not in _wood_dry_f(_wood_dry_M([[[100, 300], [350, 300], [350, 550], [100, 550]]], marsh=_TOE_MARSH))


def test_woodland_dry_passes_on_dry_ground():
    assert "woodland_commons_on_dry_ground" not in _wood_dry_f(_wood_dry_M([[[100, 100], [350, 100], [350, 350], [100, 350]]], marsh=_TOE_MARSH))


def test_woodland_dry_skips_a_map_with_no_marsh():
    assert "woodland_commons_on_dry_ground" not in _wood_dry_f(_wood_dry_M([[[100, 600], [350, 600], [350, 850], [100, 850]]]))


def test_woodland_dry_ignores_a_degenerate_marsh_poly():
    assert "woodland_commons_on_dry_ground" not in _wood_dry_f(_wood_dry_M([[[100, 600], [350, 600], [350, 850], [100, 850]]], marsh=[[0, 500], [600, 500]]))


def test_woodland_dry_ignores_the_grazing_bleed():
    assert "woodland_commons_on_dry_ground" not in _wood_dry_f(_wood_dry_M([[[100, 600], [350, 600], [350, 850], [100, 850]]], marsh=_TOE_MARSH, role="grazing"))


def test_woodland_dry_ignores_a_parcel_with_no_poly():
    assert "woodland_commons_on_dry_ground" not in _wood_dry_f(_wood_dry_M([[]], marsh=_TOE_MARSH))


def test_woodland_dry_skips_legacy_maps():
    assert "woodland_commons_on_dry_ground" not in _wood_dry_f(_wood_dry_M([[[100, 600], [350, 600], [350, 850], [100, 850]]], marsh=_TOE_MARSH, gen=None))


# ---- woodland_commons_visibly_stocked: a claimed woodland must record its canopy ---------------
def _stock_M(crowns_vals, gen="hamletgen", role="woodland"):
    M = {"meta": {"scale": "hamlet", "W": 1200, "H": 1200}, "commons": []}
    for i, cv in enumerate(crowns_vals):
        rec = {"role": role, "x": 100 + 300 * i, "y": 100, "w": 250, "h": 250, "rot": 0, "seq": i + 1, "poly": [[0, 0], [250, 0], [250, 250], [0, 250]]}
        if cv is not None:
            rec["crowns"] = cv
        M["commons"].append(rec)
    if gen:
        M["meta"]["generated_by"] = gen
    return M


def _stock_f(M):
    return check_village.gate(M, verbose=False, only={"woodland_commons_visibly_stocked"})


def test_woodland_stocked_fires_on_an_unrecorded_canopy():
    # the pre-recording state: crowns were SVG ink only, so a parcel could ship with none
    assert "woodland_commons_visibly_stocked" in _stock_f(_stock_M([None]))


def test_woodland_stocked_fires_on_a_bare_parcel():
    # Inashiro's 100%-marsh capture drew ZERO crowns behind a green gate - never again
    assert "woodland_commons_visibly_stocked" in _stock_f(_stock_M([2]))


def test_woodland_stocked_passes_a_stocked_parcel():
    assert "woodland_commons_visibly_stocked" not in _stock_f(_stock_M([12, 35]))


def test_woodland_stocked_ignores_the_grazing_bleed():
    assert "woodland_commons_visibly_stocked" not in _stock_f(_stock_M([None], role="grazing"))


def test_woodland_stocked_skips_legacy_maps():
    assert "woodland_commons_visibly_stocked" not in _stock_f(_stock_M([None], gen=None))

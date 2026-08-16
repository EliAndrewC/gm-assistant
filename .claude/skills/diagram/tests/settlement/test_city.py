"""Split from test_settlement.py by feature 025 - see test_settlement/CLAUDE.md for the index."""

import math
import re

import settlement
from settlement import Settlement, seg_dist
from tests.settlement._builders import _cap020, _caption_size, _crop_settlement, _inwall_settlement, _plank_bed, _town


def test_gapped_ring_merges_when_first_vertex_is_not_a_gate():
    # a closed wall ring whose FIRST vertex is not a gate: the run after the last gap must merge back
    # into the first, leaving one continuous subpath (not a spurious break at the start point)
    s = Settlement(1000, 1000, seed=1)
    ring = [(100, 100), (300, 100), (300, 300), (100, 300), (100, 100)]  # closed square
    d = s._gapped_ring(ring, [(300, 100)], gap=20, closed=True)  # one gate, at a NON-first vertex
    assert d.count("M") == 1


def test_wall_walk_crosses_multiple_edges():
    # walking further than one wall edge: the accumulate-and-step branch must carry across edges. A run
    # of short 50px edges, gate at index 4, walking 120px west crosses edges 4->3->2 to land at x=180.
    s = Settlement(1000, 1000, seed=1)
    pts = [(100, 100), (150, 100), (200, 100), (250, 100), (300, 100), (300, 150)]
    x, y, ang = s._wall_walk(pts, 4, 120, west=True)
    assert abs(x - 180) < 1e-6 and abs(y - 100) < 1e-6
    assert abs(ang - 180) < 1e-6  # the run is horizontal; walking west the edge points in -x


def test_city_wall_tower_slides_along_the_wall_for_a_kido():
    # tower_skip: a mural tower yields its vertex to a future kido, but the vertex stays COVERED by
    # a tower a short way along the wall (not a whole-vertex jump leaving a bare, indefensible arc).
    # At this crop's ftpx=1 the default garrison spacing is ~278px, so the flanking towers straddle
    # the yielded vertex at ~half-spacing (~140px) - well inside a bare-stretch (~one full segment).
    import math as m

    s = _crop_settlement()
    pts = [(round(1000 + 400 * m.cos(2 * m.pi * i / 12)), round(700 + 400 * m.sin(2 * m.pi * i / 12))) for i in range(12)]
    s.city_wall(pts, gates=(), tower_skip=[pts[6]])
    ds = [m.hypot(t["x"] - pts[6][0], t["y"] - pts[6][1]) for t in s.M["wall_towers"]]
    assert all(d > 45 for d in ds)  # the vertex is yielded...
    assert any(d < 180 for d in ds)  # ...but a tower still stands a short slide away (< a full segment)


def test_city_wall_tower_drops_when_boxed_in_on_both_sides():
    # ...and when the slide finds no clear ground either way, the tower is dropped (the 75-deg
    # spacing check tolerates one gap)
    import math as m

    s = _crop_settlement()
    pts = [(round(1000 + 400 * m.cos(2 * m.pi * i / 12)), round(700 + 400 * m.sin(2 * m.pi * i / 12))) for i in range(12)]
    s.city_wall(pts, gates=(), tower_skip=[pts[5], pts[6], pts[7]])
    assert all(m.hypot(t["x"] - pts[6][0], t["y"] - pts[6][1]) > 60 for t in s.M["wall_towers"])


def test_river_canal_dock_jetty_water_gate_defaults():
    # exercise the river-city glyph methods with their DEFAULT widths/lengths + the moat(river=)
    # open-arc path and the water-gate tower-skip vertex (Nagahara passes explicit sizes; this
    # covers the default branches).
    import math as m

    s = _crop_settlement()
    s.meta(name="R", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 300 * m.cos(2 * m.pi * i / 16)), round(700 + 300 * m.sin(2 * m.pi * i / 16))) for i in range(16)]
    river = [(1360, 300), (1360, 1100)]  # a river just east of the wall
    s.river(river)  # default width
    s.moat(pts, gap=24, river=river)  # open-arc moat joining the river
    s.water_gate(pts[0][0], pts[0][1])  # arch on the east gate vertex (default rot)
    s.canal([(1350, 700), (1100, 700)])  # default width
    s.dock(1050, 700, 54, 34)
    s.jetty(1330, 600)  # default length
    s.city_wall(pts, gates=[pts[4]], water_gates=[pts[0]])  # water gate skips its mural-tower vertex
    assert s.M["river"]["w"] > 0 and s.M["canals"] and s.M["docks"] and s.M["jetties"] and s.M["water_gates"]
    assert s.M["moat"][0] != s.M["moat"][-1]  # OPEN arc (ends do not close on themselves)


def test_moat_river_junction_feet_tilt_with_the_current():
    # GM 2026-07-24 hydrology review: the junction feet are NOT square rfoot tees. The upstream
    # (inlet) end shifts UPSTREAM off its square foot - a near-square, sediment-wary intake with
    # only a slight tilt - and the downstream (outlet) end sweeps DOWNSTREAM further (confluences
    # merge at downstream angles). River pts run upstream-first; a vertical river makes the
    # shifts pure y offsets, so the asymmetry is directly measurable.
    import math as m

    s = _crop_settlement()
    s.meta(name="RT", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 300 * m.cos(2 * m.pi * i / 16)), round(700 + 300 * m.sin(2 * m.pi * i / 16))) for i in range(16)]
    river = [(1360, 100), (1360, 1300)]  # flows top -> bottom (upstream-first)
    for ring in (pts, pts[::-1]):  # both ring orientations: keep[0] lands downstream on one, upstream on the other
        mo = s.moat(ring, gap=24, river=river)
        (inlet, adj_in), (outlet, adj_out) = sorted([(mo[0], mo[1]), (mo[-1], mo[-2])], key=lambda e: e[0][1])
        in_shift = adj_in[1] - inlet[1]  # upstream (negative-y) shift of the inlet foot off square
        out_shift = outlet[1] - adj_out[1]  # downstream (positive-y) sweep of the outlet foot
        assert in_shift > 0  # inlet tilts upstream, never smoothly flow-aligned
        assert out_shift > in_shift  # the outlet sweeps harder - the researched asymmetry


def test_moat_river_junction_tilts_follow_a_reversed_river():
    # the OTHER branch of the tilt bookkeeping (keep[0]'s end downstream): same asymmetry when the
    # river runs bottom -> top (upstream-first pts reversed). Deterministic on purpose - this branch
    # was previously covered only by whichever orientation a pool map happened to roll, so an rng
    # shift elsewhere dropped it out of coverage (2026-07-24).
    import math as m

    s = _crop_settlement()
    s.meta(name="RT2", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 300 * m.cos(2 * m.pi * i / 16)), round(700 + 300 * m.sin(2 * m.pi * i / 16))) for i in range(16)]
    river = [(1360, 1300), (1360, 100)]  # flows bottom -> top (upstream-first)
    mo = s.moat(pts, gap=24, river=river)
    (outlet, adj_out), (inlet, adj_in) = sorted([(mo[0], mo[1]), (mo[-1], mo[-2])], key=lambda e: e[0][1])
    in_shift = inlet[1] - adj_in[1]  # upstream is +y now: the inlet foot shifts DOWN off square
    out_shift = adj_out[1] - outlet[1]  # the outlet foot sweeps UP, downstream with the current
    assert in_shift > 0  # inlet tilts upstream, never smoothly flow-aligned
    assert out_shift > in_shift  # the outlet sweeps harder - the researched asymmetry


def test_city_wall_gateposts_orient_to_the_wall_tangent():
    # GM 2026-07: gateposts were hard-coded N/S (vertical rects); on an E/W gate they must stand
    # N and S of the opening, oriented to the wall's local tangent - so a gate on a vertical wall
    # stretch gets ~vertical-tangent posts (rot near +-90), not the old rot=0.
    import math as m

    s = _crop_settlement()
    s.meta(name="C", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 400 * m.cos(2 * m.pi * i / 16)), round(700 + 400 * m.sin(2 * m.pi * i / 16))) for i in range(16)]
    egate = pts[0]  # the EAST gate (rightmost): the wall runs ~vertically there
    s.city_wall(pts, gates=[egate])
    posts = [g for g in s.M["gate_structs"] if g.get("kind") == "gatepost"]
    assert len(posts) == 2
    assert all(abs(abs(p["rot"]) - 90) < 25 for p in posts)  # tangent ~vertical, not the old rot 0
    # the two posts straddle the gate along the tangent (N and S of it), not E and W
    # > 10, not the old > 40: the throat is TO SCALE since 2026-07-27 (30 ft clear + a 15 ft pier a
    # side = 15 px between post centres at 1 px = 3 ft), where it used to open a 210 ft gap. The
    # assertion here is about ORIENTATION - N and S of the opening, not E and W - so it must not
    # re-encode the old spacing as its threshold.
    assert abs(posts[0]["y"] - posts[1]["y"]) > 10 and abs(posts[0]["x"] - posts[1]["x"]) < 30


def test_moat_closes_into_a_ring_without_a_river():
    # the moat(river=None) branch: with no river to join, the moat closes on itself into a ring (the
    # else arm), so the recorded polyline's first and last points coincide. The river-open-arc arm is
    # covered by test_river_canal_dock_jetty_water_gate_defaults.
    import math as m

    s = _crop_settlement()
    pts = [(round(1000 + 300 * m.cos(2 * m.pi * i / 12)), round(700 + 300 * m.sin(2 * m.pi * i / 12))) for i in range(12)]
    s.moat(pts)  # no river -> CLOSED ring
    assert s.M["moat"][0] == s.M["moat"][-1]


def test_city_gate_tower_flips_to_the_other_flank_when_one_is_blocked():
    # the gate tower belongs AT the gate: with its PRIMARY flank blocked by a kido span, it does NOT walk
    # far out along the wall - it flips to the OTHER flank at the same short arc, still at the opening.
    import math as m

    s = _crop_settlement()
    s.meta(name="G", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 400 * m.cos(2 * m.pi * i / 16)), round(700 + 400 * m.sin(2 * m.pi * i / 16))) for i in range(16)]
    blocks = [s._wall_walk(pts, 0, a, west=False)[:2] for a in (78, 98, 118)]  # block the PRIMARY (west=False) flank
    s.city_wall(pts, gates=[pts[0]], tower_skip=blocks)
    tower = [gs for gs in s.M["gate_structs"] if gs.get("kind") == "tower"]
    assert tower  # the gate tower is still placed...
    assert m.hypot(tower[0]["x"] - pts[0][0], tower[0]["y"] - pts[0][1]) < 110  # ...AT the gate, not marooned far out
    assert all(m.hypot(tower[0]["x"] - bx, tower[0]["y"] - by) > 45 for bx, by in blocks)  # on the clear OTHER flank


def test_city_gate_tower_steps_out_when_both_near_flanks_are_blocked():
    # only when BOTH near-gate flanks are blocked does the tower step OUTWARD along the wall (the arc walk):
    # kido spans on each side of the gate leave it nowhere at the opening, so it walks clear.
    import math as m

    s = _crop_settlement()
    s.meta(name="B", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 400 * m.cos(2 * m.pi * i / 16)), round(700 + 400 * m.sin(2 * m.pi * i / 16))) for i in range(16)]
    blocks = [s._wall_walk(pts, 0, a, west=wf)[:2] for a in (78, 98, 118) for wf in (False, True)]  # BOTH flanks near the gate
    s.city_wall(pts, gates=[pts[0]], tower_skip=blocks)
    tower = [gs for gs in s.M["gate_structs"] if gs.get("kind") == "tower"]
    assert tower and all(m.hypot(tower[0]["x"] - bx, tower[0]["y"] - by) > 45 for bx, by in blocks)  # placed, walked clear of every blocked span


def test_city_gate_tower_falls_back_when_every_spot_is_blocked():
    # both flanks blocked at EVERY arc out to the cap: the tower is still placed exactly once (the last
    # candidate is taken rather than the loop running past the cap with nothing placed).
    import math as m

    s = _crop_settlement()
    s.meta(name="F", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 400 * m.cos(2 * m.pi * i / 16)), round(700 + 400 * m.sin(2 * m.pi * i / 16))) for i in range(16)]
    blocks = [s._wall_walk(pts, 0, a, west=wf)[:2] for a in range(78, 241, 20) for wf in (False, True)]
    s.city_wall(pts, gates=[pts[0]], tower_skip=blocks)
    assert len([gs for gs in s.M["gate_structs"] if gs.get("kind") == "tower"]) == 1


def test_city_mural_tower_yields_a_vertex_shoulder_to_shoulder_with_a_gate_tower():
    # the mural-tower loop skips a wall vertex within 110px of a GATE tower (a mural tower there would read
    # as a double). This fires only when the gate tower has stepped OUT toward the next even vertex - which
    # now needs BOTH near-gate flanks blocked. A fine 24-gon plus kido spans on both flanks forces exactly
    # that: the tower walks out near an even, non-gate vertex, which the mural loop then yields.
    import math as m

    s = _crop_settlement()
    s.meta(name="M", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 420 * m.cos(2 * m.pi * i / 24)), round(700 + 420 * m.sin(2 * m.pi * i / 24))) for i in range(24)]
    blocks = [s._wall_walk(pts, 0, a, west=wf)[:2] for a in (78, 98, 118) for wf in (False, True)]
    s.city_wall(pts, gates=[pts[0]], tower_skip=blocks)
    gate_towers = [(gs["x"], gs["y"]) for gs in s.M["gate_structs"] if gs.get("kind") == "tower"]
    assert gate_towers and s.M.get("wall_towers")  # both kinds of tower were placed
    # the gate tower walked clear of the blocked kido spans (which is what carried it out near the even
    # vertex the mural loop then yields)
    assert all(m.hypot(gate_towers[0][0] - bx, gate_towers[0][1] - by) > 45 for bx, by in blocks)


def test_bridges_carries_the_ring_road_over_the_cargo_canal_but_not_over_a_buried_conduit():
    """The ring road is a carried way and the cargo canal a watercourse - the pair that used to be
    invisible here, so both cities hand-placed that deck and both went crooked (GM 2026-07-27). An
    UNDRAWN channel is a buried conduit, though: nothing on the ground to bridge."""
    s = _crop_settlement()
    s.M["ring_road"] = [[100, 300], [500, 300]]
    s.M["ring_road_width"] = 7
    s.M["canals"] = [{"poly": [[300, 150], [300, 450]], "w": 12}]
    s.M["channels"] = [{"poly": [[200, 150], [200, 450]], "frm": None, "to": None, "w": 2.5, "drawn": False}]
    assert s.bridges() == 1  # the canal only - the conduit is not a crossing
    deck = s.M["bridges"][0]
    assert abs(deck["x"] - 300) < 2 and abs(deck["y"] - 300) < 2  # ON the crossing, solved not eyeballed
    assert deck["rot"] == 0 and deck["w"] == 7  # ALONG the ring road, and as wide as the way it carries


def test_log_boom_defaults_to_a_full_holding_pen_and_records_its_box():
    s = _crop_settlement()
    z = s.log_boom(400, 300, rot=90)
    b = s.M["log_booms"][0]
    assert b["z"] == z and b["len"] == round(s.px(330), 1)  # the default pen, ~330 real ft of chained logs
    assert b["pen_w"] == round(s.px(40), 1)  # ~40 real ft of held water between chain and shore
    # the record carries TRUE unrotated dims + rot, like a building - the matrix extractor rotates
    # x/w/h by rot itself, so a rotation-folded box here would double-rotate into a phantom
    # footprint (which is exactly how the first pen landed "on" Minami's lumber yard 42px away)
    assert b["w"] == b["len"] and b["h"] == b["pen_w"] and b["rot"] == 90.0


def test_log_boom_labels_below_itself_unless_told_otherwise():
    s = _crop_settlement()
    s.log_boom(400, 300, rot=0, length=90, label="log boom")
    assert any(len(lb) > 5 and lb[5] == "log boom" for lb in s.M["labels"])
    s2 = _crop_settlement()
    s2.log_boom(400, 300, rot=0, length=90, label=None)
    assert not any(len(lb) > 5 and lb[5] == "log boom" for lb in s2.M["labels"])


def test_bridge_refuses_a_second_deck_on_a_crossing_that_already_has_one():
    """ONE DECK PER CROSSING - the guard lives in bridge() so every caller is covered.

    Minami shipped two decks over the Hayakawa 3px apart (a hand-placed one plus the automatic pass),
    and honda/hoshigaoka/kikuta each carried two footplanks at the SAME point. None was caught because
    bridges were invisible to the overlap matrix."""
    s = _crop_settlement()
    z1 = s.bridge(300, 300, 0, 60, 12)
    z2 = s.bridge(303, 301, 0, 60, 12)  # the same crossing, a few px off
    assert len(s.M["bridges"]) == 1 and z2 == z1  # returns the standing deck rather than drawing a second
    # ...but two genuinely distinct footplanks a few px apart still both draw (the tolerance scales
    # with the deck, so a narrow plank keeps a narrow exclusion)
    s2 = _crop_settlement()
    s2.bridge(300, 300, 0, 8, 2)
    s2.bridge(306, 300, 0, 8, 2)
    assert len(s2.M["bridges"]) == 2


def test_channel_footbridges_plank_each_long_ditch_perpendicular():
    s = _crop_settlement()
    s.M["fields"] = [{"outline": [[50, 120], [850, 120], [850, 280], [50, 280]]}]  # paddy straddling the y=200 ditch (both banks cultivated)
    s.M["field_ditches"] = [
        {"poly": [[100, 200], [400, 200], [800, 200]], "w": 5, "role": "main"},  # 700px, 2 segments -> two planks at spacing 320
        {"poly": [[100, 400], [160, 400]], "w": 4, "role": "branch"},  # 60px -> below min_len, no plank
    ]
    n = s.channel_footbridges(spacing=320)
    assert n == 2 and len(s.M["bridges"]) == 2  # the short stub is stepped over, not bridged
    assert all(abs(abs(b["rot"]) - 90) < 1 for b in s.M["bridges"])  # deck runs N-S, ACROSS the E-W ditch
    assert all(190 < b["y"] < 210 for b in s.M["bridges"])  # both sit ON the ditch line


def test_channel_footbridges_slides_a_plank_clear_of_a_farmhouse():
    s = _crop_settlement()
    s.M["fields"] = [{"outline": [[50, 220], [750, 220], [750, 380], [50, 380]]}]  # paddy straddling the y=300 ditch
    s.M["field_ditches"] = [{"poly": [[100, 300], [700, 300]], "w": 5, "role": "main"}]  # 600px E-W ditch
    s.M["houses"] = [{"x": 400, "y": 300, "w": 60, "h": 40, "kind": "plain", "rot": 0}]  # a house ON the ditch midpoint
    n = s.channel_footbridges(spacing=800)  # n=1, midway = (400,300) = on the house
    assert n == 1
    b = s.M["bridges"][0]
    assert not (365 <= b["x"] <= 435) and 190 < b["y"] < 410  # the plank slid ALONG the ditch, off the house footprint


def test_channel_footbridges_skips_a_crossing_to_uncultivated_ground():
    s = _crop_settlement()
    s.M["fields"] = [{"outline": [[50, 120], [750, 120], [750, 297], [50, 297]]}]  # paddy only NORTH of the ditch; the S bank is marsh/scrub
    s.M["field_ditches"] = [{"poly": [[100, 300], [700, 300]], "w": 5, "role": "main"}]  # a margin ditch: field one side, nothing the other
    n = s.channel_footbridges(spacing=800)
    assert n == 0 and not s.M["bridges"]  # no cultivated ground on the far bank -> no useful crossing -> no plank


def test_governor_mansion_caption_sits_inside_its_walls():
    # GM 2026-08-08. The court is drawn blank on purpose (its buildings are a separate Mode A
    # sheet), so it is guaranteed clear ground on a packed city map, and the band above the walls
    # is prime housing. The caption goes inside, small enough to clear both walls.
    s = Settlement(1400, 1400, seed=6)
    s.meta(name="C", scale="city", ftpx=3)
    s.governor_mansion(700, 700, s.px(436), s.px(366), "Governor's Mansion", gate_dir="west")
    gov = s.M["governor_mansion"]
    assert gov["label"] == "Governor's Mansion"  # the record keeps the name manor() was not given
    lab = next(lb for lb in s.M["labels"] if lb[5] == "Governor's Mansion")
    assert _caption_size(lab) == settlement.GOVERNOR_CAPTION_FS
    assert lab[0] > 700 - gov["w"] / 2 and lab[2] < 700 + gov["w"] / 2  # clear of BOTH walls
    assert lab[1] > 700 - gov["h"] / 2 and lab[3] < 700 + gov["h"] / 2  # and inside, not above
    assert len([lb for lb in s.M["labels"] if lb[5] == "Governor's Mansion"]) == 1  # manor drew none


def test_governor_mansion_can_be_left_unlabeled():
    s = Settlement(1400, 1400, seed=7)
    s.meta(name="C", scale="city", ftpx=3)
    s.governor_mansion(700, 700, s.px(436), s.px(366), "", gate_dir="west")
    assert s.M["governor_mansion"]["label"] == ""
    assert not s.M["labels"]


# ---- city_wall: a mural tower BOXED IN on both sides is dropped ----------------------------
def test_city_wall_drops_a_mural_tower_boxed_in_on_both_sides():
    # the NW vertex is ringed by keep-clear (kido) points carpeting BOTH wall flanks out past the
    # farthest slide arc, so every slide candidate stays blocked and the tower is dropped (spacing
    # tolerates one gap). The clear SE vertex still gets its tower.
    s = Settlement(1200, 1200, seed=1)
    s.meta(name="C", scale="city")
    pts = [[150, 150], [1050, 150], [1050, 1050], [150, 1050]]
    skip = [
        (150, 150),
        (190, 150),
        (230, 150),
        (270, 150),  # carpet the top flank
        (150, 190),
        (150, 230),
        (150, 270),
    ]  # carpet the left flank
    s.city_wall(pts, gates=(), tower_skip=skip)
    towers = s.M.get("wall_towers", [])
    # ftpx=1 garrison -> ~278px spacing; a CLEAR corner is straddled by flanking towers at ~147px, a
    # boxed-in corner's nearest tower is pushed out past the next seat (~212px). The contrast holds.
    nw = min(math.hypot(t["x"] - 150, t["y"] - 150) for t in towers)
    se = min(math.hypot(t["x"] - 1050, t["y"] - 1050) for t in towers)
    assert nw > 180  # NW tower dropped (boxed in) - nearest tower pushed out past the next seat
    assert se < 180  # SE corner kept - flanking towers straddle it at ~half-spacing


def test_inwall_drain_outfall_trims_gates_and_records_the_conduit():
    """The in-wall drain handoff (GM 2026-07-23): the drain polyline is trimmed back to half the
    ring-road width + 10px clear of the ring centerline, a sluice gate sits across the cut, and
    an UNDRAWN drain->moat conduit starts exactly at the cut (inwall_drains_gated_at_cutoff)."""
    s = _inwall_settlement()
    out = s.inwall_drain_outfall([(500, 300), (300, 150), (150, 110)])  # moat-side end LAST, ends 10px off the ring's top segment
    cut = out[-1]
    ringd = min(settlement.seg_dist(cut[0], cut[1], a, b) for a, b in [((100, 100), (900, 100)), ((100, 100), (100, 900))])
    assert ringd >= 13.9  # 8/2 + 10 clear of the centerline
    assert len(out) < 3 or out[:2] == [(500.0, 300.0), (300.0, 150.0)]  # only the tail was touched
    g = s.M["sluice_gates"][-1]
    assert math.hypot(g["x"] - cut[0], g["y"] - cut[1]) < 1.5  # the gate sits AT the cut
    c = s.M["channels"][-1]
    assert c["frm"] == {"kind": "drain"} and c["to"] == {"kind": "moat"} and c["drawn"] is False
    assert c["poly"][0] == [round(cut[0], 1), round(cut[1], 1)]  # the conduit starts at the cut


def test_inwall_drain_outfall_normalizes_orientation_and_degenerate_cases():
    # outfall-FIRST input comes back outfall-first (the caller's orientation is preserved)
    s = _inwall_settlement()
    out = s.inwall_drain_outfall([(150, 110), (300, 150), (500, 300)])
    assert out[-1] == (500.0, 300.0)  # far end untouched, so the cut landed at index 0
    # no ring road: nothing to trim - the gate still marks the outfall
    s2 = Settlement(1000, 1000, seed=1)
    s2.meta(name="C2", scale="town", ftpx=1)
    s2.M["moat"] = [[60, 60], [940, 60], [940, 940], [60, 940]]
    out2 = s2.inwall_drain_outfall([(500, 300), (150, 110)])
    assert out2 == [(500.0, 300.0), (150.0, 110.0)] and s2.M["sluice_gates"]
    # no moat: gate only - no conduit record, no orientation flip
    s3 = Settlement(1000, 1000, seed=1)
    s3.meta(name="C3", scale="town", ftpx=1)
    s3.M["ring_road"] = [[100, 100], [900, 100], [900, 900], [100, 900], [100, 100]]
    s3.M["ring_road_width"] = 8
    n3 = len(s3.M["channels"])
    s3.inwall_drain_outfall([(500, 300), (150, 110)])
    assert len(s3.M["channels"]) == n3 and s3.M["sluice_gates"]
    # the whole polyline hugs the road: left untrimmed (the check flags it), gate at the raw end
    s4 = _inwall_settlement()
    out4 = s4.inwall_drain_outfall([(300, 104), (200, 104)])
    assert out4[-1] == (200.0, 104.0)


def test_navigable_canal_is_level_and_carries_no_bearing():
    s = _town()
    s.canal([(100, 100), (400, 100)])
    rec = s.M["canals"][0]
    assert rec["flow"] == "level" and rec["flow_deg"] is None


def test_moat_flow_declares_a_closed_ring_circulation():
    s = _town()
    s.moat_flow((120.44, 200.51), (800.0, 640.0))
    assert s.M["moat_flow"] == {"inlet": [120.4, 200.5], "outlet": [800.0, 640.0]}


def test_towpath_records_a_list_and_draws_no_roadbed_or_centerline():
    """A towpath is NOT a road (research/cities/capitals.md, 'A river gets a TOWPATH, not a
    road'): no roadbed fill, no dashed centerline, one hairline at the linework floor."""
    s = _cap020()
    n0 = len(s.out)
    s.towpath([(100, 1300), (400, 1000), (700, 800)])
    frag = "".join(s.out[n0:])
    assert isinstance(s.M["towpaths"], list) and len(s.M["towpaths"]) == 1
    rec = s.M["towpaths"][0]
    assert rec["pts"][0] == [100, 1300] and rec["pts"][-1] == [700, 800]
    assert "stroke-dasharray" not in frag  # no dashed centerline - it is not a road
    assert frag.count("<path") == 1  # ONE hairline stroke, no roadbed under it
    assert rec["w"] <= 4.0  # a beaten path, not a carriageway
    # and it never touches the road records - a towpath must not read as road plumbing
    assert not s.M.get("roads") and not s.M.get("road")


def test_towpath_reserves_its_ground():
    s = _cap020()
    n_corr = len(s.corridors)
    s.towpath([(100, 1300), (700, 800)])
    assert len(s.corridors) == n_corr + 1  # later packs keep off the bank


def test_aqueduct_records_intake_channel_and_terminus():
    s = _cap020()
    s.aqueduct([(1300, 200), (900, 150), (500, 120)])
    assert isinstance(s.M["aqueducts"], list) and len(s.M["aqueducts"]) == 1
    rec = s.M["aqueducts"][0]
    assert rec["poly"][0] == [1300, 200] and rec["intake"] == [1300, 200]
    assert rec["to"] == [500, 120]
    assert rec["w"] > 0


def test_aqueduct_draws_no_arcade():
    """NO ARCADED AQUEDUCT EXISTS in either anchor tradition (research/cities/capitals.md): the
    vocabulary is a gravity canal at grade, a buried pipe, and a flume bridge only where water
    crosses water. Every path in the glyph is straight cuts - no arch curves anywhere."""
    s = _cap020()
    n0 = len(s.out)
    s.aqueduct([(1300, 200), (900, 150), (500, 120)])
    frag = "".join(s.out[n0:])
    for d in re.findall(r'd="([^"]+)"', frag):
        cmds = set(re.findall(r"[A-Za-z]", d))
        assert cmds <= {"M", "L"}, f"curve commands {cmds - {'M', 'L'}} in the aqueduct glyph - an arch has no business here"


def test_quay_faces_the_bank_with_stepped_landings():
    """The working face at a river wharf is the BANK, faced and notched with steps - not the piers
    (research/cities/river-cities.md: a river's level moves feet across the year, so a flight of
    steps is the right height at every one of them while a fixed deck is right for weeks). The
    glyph records its landings and mooring posts so the checks can read them."""
    s = settlement.Settlement(1200, 1200, seed=4)
    s.meta(scale="capital", ftpx=3)
    bank = [(300, 200), (420, 500), (500, 820)]
    s.quay(bank, steps=3)
    q = s.M["quays"][0]
    assert q["pts"] == [[300.0, 200.0], [420.0, 500.0], [500.0, 820.0]]
    assert len(q["landings"]) == 3, "each landing is a flight of steps notched into the face"
    assert len(q["posts"]) == 5, "mooring posts along the top of the face"
    for lx, ly in q["landings"]:
        assert min(seg_dist(lx, ly, bank[i], bank[i + 1]) for i in range(len(bank) - 1)) < 2.0, "a landing sits ON the face"
    assert any(cl > q["w"] / 2 for _p, cl in s.corridors), "the face reserves its own working strip"


def test_quay_takes_a_default_width_from_the_map_scale():
    s = settlement.Settlement(1200, 1200, seed=4)
    s.meta(scale="capital", ftpx=3)
    s.quay([(100, 100), (400, 100)], steps=1)
    assert s.M["quays"][0]["w"] >= 2.6


def test_a_footplank_is_never_laid_across_the_hem_crop():
    """THE RATCHET for the 2026-08-11 slide condition. A plank slides clear of houses and of banks
    that open onto marsh; it must also slide clear of the DRY hem, because a deck laid on a hatake
    strip is a board lying on the barley - the same rule `groves_clear_of_dry_plots` states for trees
    and `structures_clear_of_dry_plots` for buildings."""
    s = _plank_bed()
    hem = [(560.0, 660.0), (840.0, 660.0), (840.0, 740.0), (560.0, 740.0)]  # straddles the ditch mid-run
    s.M["dry_plots"].append({"poly": [list(p) for p in hem], "crop": "barley", "theta": 0.0})
    s.dry_polys.append(hem)
    s.channel_footbridges(spacing=300)
    assert s.M["bridges"], "the fixture must actually place planks, or it proves nothing"
    for b in s.M["bridges"]:
        assert not (560.0 <= b["x"] <= 840.0 and 660.0 <= b["y"] <= 740.0), f"a plank was laid on the hem at {(round(b['x']), round(b['y']))}"


def test_a_footplank_is_never_laid_on_a_bend_its_deck_cannot_clear():
    """THE RATCHET for the corner test. `bridges_span_their_water` requires every deck CORNER to
    stand clear of the crossed water; a deck perpendicular to a STRAIGHT ditch clears by
    construction, and one at a BEND does not, because the polyline curves back toward a corner."""
    s = _plank_bed(bend=True)
    s.channel_footbridges(spacing=300)
    assert s.M["bridges"], "the fixture must actually place planks, or it proves nothing"
    for b in s.M["bridges"]:
        th = math.radians(b["rot"])
        ux, uy = math.cos(th), math.sin(th)
        for su, sv in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            cx = b["x"] + su * ux * b["span"] / 2 - sv * uy * b["w"] / 2
            cy = b["y"] + su * uy * b["span"] / 2 + sv * ux * b["w"] / 2
            gap = min(seg_dist(cx, cy, tuple(d["poly"][i]), tuple(d["poly"][i + 1])) for d in s.M["field_ditches"] for i in range(len(d["poly"]) - 1))
            assert gap >= 4.0 / 2 + 2.0, f"deck corner {round(gap, 1)}px from its own ditch - the abutment stands in the water"


def test_farmland_ring_taps_water_gates_it_and_rings_the_households():
    """A city is ringed by its farmland, and the belt loop that draws it belongs in ONE place.
    Every provincial-city gen carried its own copy - which is why ringing a capital read as new
    work and cost a day (GM 2026-08-12). This is that loop: tap the water, gate the head-race,
    build the fan, declare source and sink, ring the households."""
    s = settlement.Settlement(1400, 1400, seed=5)
    s.meta(scale="city", ftpx=3)
    river = [(1200, 100), (1200, 1300)]
    s.M["rivers"] = [{"pts": river, "w": 30}]
    seen = {}

    def comb(name, sl, dd, sd, ff, ca, cb, oa):
        env = [(sl[0] - 200, sl[1] - 120), (sl[0] - 40, sl[1] - 120), (sl[0] - 40, sl[1] + 120), (sl[0] - 200, sl[1] + 120)]
        net = {"channels": [{"role": "drain", "pts": [(sl[0] - 200, sl[1] + 100), (sl[0] - 320, sl[1] + 160)]}], "plots": [{"poly": env}]}
        seen["sluice"] = sl
        return net, env, (sl[0] - 120, sl[1])

    def topo(pts, frm, to, draw_w=0.0):
        seen.setdefault("topo", []).append((frm.get("kind"), to.get("kind")))

    out = s.farmland_ring(
        [("f1", (1200, 700), 180, 3, 100, (120, 150), (80, 100), (0.3, 0.7), "river")],
        comb=comb,
        topo=topo,
        water=lambda k: river,
        city_center=(700, 700),
    )
    assert len(out) == 1, "the field should have been built"
    assert seen["sluice"] != (1200, 700), "the sluice is set off the tap, not on it"
    assert ("river", "field") in seen["topo"], "the source must be declared from the water it taps"
    assert any(a == "drain" and b == "offmap" for a, b in seen["topo"]), "the drain must reach a sink"
    assert s.M["sluice_gates"], "the head-race is gated where tap water becomes canal water"


def test_farmland_ring_withdraws_a_field_whose_ground_cannot_carry_it():
    """comb_field records the field BEFORE its water is declared, so a fan that fails to carve
    would leave a paddy with no source, no drain and no farmhouses - drawn, recorded, and invisible
    to every rule that reads the water."""
    s = settlement.Settlement(1400, 1400, seed=5)
    s.meta(scale="city", ftpx=3)
    river = [(1200, 100), (1200, 1300)]

    def comb(name, sl, dd, sd, ff, ca, cb, oa):
        s.M.setdefault("fields", []).append({"name": name, "outline": [(0, 0)]})
        raise ValueError("no room to carve")

    out = s.farmland_ring(
        [("doomed", (1200, 700), 180, 3, 100, (120, 150), (80, 100), (0.3, 0.7), "river")],
        comb=comb,
        topo=lambda *a, **k: None,
        water=lambda k: river,
        city_center=(700, 700),
    )
    assert out == [], "a field that cannot be built is not returned"
    assert not [f for f in s.M.get("fields") or [] if f.get("name") == "doomed"], "...and it is not left on the map"


def test_farmland_ring_sweeps_a_moat_offtake_downstream():
    """A moat offtake leaves at an ACUTE angle pointing downstream - a square tap sheds sediment
    into its own mouth and says nothing on the page about which way the water runs. The ring does
    that sweep itself, so no gen has to remember moat_swept_tap."""
    s = settlement.Settlement(1600, 1600, seed=8)
    s.meta(scale="city", ftpx=3)
    moat = [(400, 400), (1200, 400), (1200, 1200), (400, 1200), (400, 400)]
    s.M["moat_flow"] = {"inlet": [1200, 400], "outlet": [400, 1200]}
    taps = {}

    def comb(name, sl, dd, sd, ff, ca, cb, oa):
        taps["sl"] = sl
        env = [(sl[0] - 160, sl[1] - 90), (sl[0] - 30, sl[1] - 90), (sl[0] - 30, sl[1] + 90), (sl[0] - 160, sl[1] + 90)]
        # a drain that runs well off the sheet, so the reach loop finds its edge on the first steps
        return {"channels": [{"role": "drain", "pts": [(sl[0] - 160, sl[1] + 70), (-400, sl[1] + 200)]}], "plots": [{"poly": env}]}, env, sl

    out = s.farmland_ring(
        [("m1", (400, 800), 180, 4, 100, (120, 150), (80, 100), (0.3, 0.7), "moat")],
        comb=comb,
        topo=lambda *a, **k: None,
        water=lambda k: moat,
        city_center=(800, 800),
    )
    assert len(out) == 1
    assert s.M["sluice_gates"], "the head-race is gated"


def test_farmland_ring_taps_a_segment_and_opens_the_bound():
    """Two options a capital needs and the provincial cities do not. A river drawn with FIVE
    vertices has no vertex near where the gen meant to tap, so the tap must land on the nearest
    POINT of the polyline; and a map that sets a placement bound rings NOTHING until it is opened
    around the field, which is how a first farmland ring came out as fields with no households."""
    s = settlement.Settlement(1400, 1400, seed=6)
    s.meta(scale="capital", ftpx=3)
    river = [(1200, 100), (1200, 1300)]  # two vertices, both far from the hint
    s.bound = [[0, 0], [200, 0], [200, 200], [0, 200]]  # a bound nowhere near the field
    taps = {}

    def comb(name, sl, dd, sd, ff, ca, cb, oa):
        taps["sl"] = sl
        env = [(sl[0] - 150, sl[1] - 90), (sl[0] - 30, sl[1] - 90), (sl[0] - 30, sl[1] + 90), (sl[0] - 150, sl[1] + 90)]
        return {"channels": [{"role": "drain", "pts": [(sl[0] - 150, sl[1] + 70), (-500, sl[1] + 200)]}], "plots": [{"poly": env}]}, env, sl

    out = s.farmland_ring(
        [("f1", (1200, 700), 180, 3, 100, (120, 150), (80, 100), (0.3, 0.7), "river")],
        comb=comb,
        topo=lambda *a, **k: None,
        water=lambda k: river,
        city_center=(700, 700),
        tap_on_segment=True,
        open_bound=True,
        standoff=78.0,
    )
    assert len(out) == 1
    assert abs(taps["sl"][1] - 700) < 60, "tapped ON the segment beside the hint, not at a far vertex"
    assert s.bound == [[0, 0], [200, 0], [200, 200], [0, 200]], "the bound is restored afterwards"


def test_farmland_ring_upslope_keeps_households_out_of_the_wet_toe():
    """A plain ring walks the WHOLE envelope and projects each seat outward, so on the low edge it
    throws households into the ground below the drainage collector - the wettest in the valley, and
    the one place nobody builds. `upslope=True` walks the perimeter and skips the low side."""
    s = settlement.Settlement(1600, 1600, seed=11)
    s.meta(scale="capital", ftpx=3)
    river = [(1300, 100), (1300, 1500)]
    s.bound = [[0, 0], [100, 0], [100, 100], [0, 100]]
    seats = []

    def comb(name, sl, dd, sd, ff, ca, cb, oa):
        env = [(sl[0] - 200, sl[1] - 140), (sl[0] - 40, sl[1] - 140), (sl[0] - 40, sl[1] + 140), (sl[0] - 200, sl[1] + 140)]
        # RECORD the planted plots, so the cropland test has something to refuse seats against -
        # a farmstead stands beside the field it works, never on it
        s.M.setdefault("fields", []).append({"name": name, "outline": env, "plot_polys": [env]})
        # the drain lies along the field's SOUTH edge, so everything below it is toe
        return {"channels": [{"role": "drain", "pts": [(sl[0] - 200, sl[1] + 140), (sl[0] - 40, sl[1] + 140)]}], "plots": [{"poly": env}]}, env, sl

    s.farmland_ring(
        [("f1", (1300, 800), 90, 3, 100, (120, 150), (80, 100), (0.3, 0.7), "river")],
        comb=comb,
        topo=lambda *a, **k: None,
        water=lambda k: river,
        city_center=(800, 800),
        tap_on_segment=True,
        open_bound=True,
        upslope=True,
    )
    seats = [(h["x"], h["y"]) for h in s.M["houses"]]
    assert seats, "the upslope walk must seat households"
    # down_deg 90 is due south, and the drain sits at the envelope's south edge
    drain_y = max(q[1] for q in [(0, 0)] + seats) if seats else 0
    assert all(y <= drain_y for _x, y in seats), "no household below the drainage line"


def test_ring_upslope_refuses_a_seat_below_the_drain():
    """The drain test measures to the drain LINE, not the field's centre: a seat can be upslope of
    the middle and still below the collector where it bends, and that ground is the wet toe."""
    s = settlement.Settlement(1200, 1200, seed=2)
    s.meta(scale="capital", ftpx=3)
    env = [(400, 400), (800, 400), (800, 800), (400, 800)]
    # a drain running right across the middle of the field: everything south of it is toe
    drain = [(380, 600), (820, 600)]
    n = s._ring_upslope(env, 90.0, drain, (20, 44))
    ys = [h["y"] for h in s.M["houses"]]
    assert n == len(ys)
    assert all(y < 640 for y in ys), f"a household landed below the drain: {sorted(ys)[-3:]}"

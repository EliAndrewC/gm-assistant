"""Split from test_settlement.py by feature 025 - see tests/settlement/CLAUDE.md for the index."""

import pytest

from settlement import Settlement
from tests.settlement._builders import _city, _crop_settlement, _town


def test_trade_works_caption_hand_seat_moves_the_label_and_its_band():
    # label_xy on a trade glyph seats the caption (and its reserved band) at the given spot -
    # the punishment_spot/kosatsuba remedy for a collision the placement probe cannot see
    # (Minami's lumber-yard caption grazed the log-boom pen by under a pixel, 2026-08-02)
    s = _crop_settlement()
    s.lumber_yard(400, 300, label_xy=(470, 340))
    lab = next(lb for lb in s.M["labels"] if len(lb) > 5 and lb[5] == "lumber yard")
    assert abs((lab[0] + lab[2]) / 2 - 470) < 1.0 and lab[1] < 340 < lab[3]
    s2 = _crop_settlement()
    s2.lumber_yard(400, 300)  # default seat: below the footprint
    lab2 = next(lb for lb in s2.M["labels"] if len(lb) > 5 and lb[5] == "lumber yard")
    assert abs((lab2[0] + lab2[2]) / 2 - 400) < 1.0 and lab2[1] > 300


def test_bathhouses_roll_follows_the_population_formula():
    # GM formula 2026-07-24 (second refinement): 1 per full 2,000 population + a remainder-
    # fraction chance of one extra (2,500 -> 1 + 25%, 3,000 -> 1 + 50%, 4,000 -> exactly 2);
    # count= pins; too few seats is loud. Own Settlements with pinned seeds (the module has two
    # _city helpers and the later one shadows - a seed-3 assumption here failed on seed 1):
    # seed 2's dedicated roll is 0.670 (extra misses at 50%), seed 1's is 0.258 (extra lands).
    def city_(seed, pop):
        s_ = Settlement(1200, 1200, seed=seed)
        s_.meta(name="C", scale="city", ftpx=3)
        s_.M["meta"]["population"] = pop
        return s_

    s = city_(2, 2000)  # zero remainder: exactly 1, no roll can add
    assert s.bathhouses([(300, 300), (600, 600)]) == 1
    assert s.M["meta"]["bathhouse_roll"] == 1 and len(s.M["bathhouses"]) == 1
    s2 = city_(2, 4000)  # two full units, zero remainder: exactly 2
    assert s2.bathhouses([(300, 300), (600, 600)]) == 2
    assert len(s2.M["bathhouses"]) == 2
    assert city_(2, 3000).bathhouses([(300, 300), (600, 600)]) == 1  # roll 0.670 >= 0.50: no extra
    assert city_(1, 3000).bathhouses([(300, 300), (600, 600)]) == 2  # roll 0.258 < 0.50: extra lands
    assert city_(2, 3000).bathhouses([(300, 300), (600, 600)], count=2) == 2  # pin overrides the roll
    s4 = city_(2, 4000)
    with pytest.raises(ValueError, match="vetted seats"):
        s4.bathhouses([(300, 300)])  # a guaranteed 2 needs 2 seats


def test_farrier_draws_a_forge_shed_with_a_working_apron_and_records_it():
    # the shoeing forge (GM 2026-07-25, settlements.md "TRADE WORKS" -> FARRIERY): an open-sided
    # shed plus the apron the animal is actually stood on, recorded as a first-class trade work so
    # farrier_serves_a_stables / farrier_keeps_fire_gap can gate its siting. Sizes are TRUE feet -
    # a 20x18 ft shed on a 28x20 ft apron - so the record is the full 28x38 ft footprint.
    s = _city()
    before = len(s.out)
    s.farrier(600, 620)
    assert len(s.out) > before
    fr = s.M["farriers"][-1]
    assert (fr["x"], fr["y"]) == (600, 620)
    assert fr["w"] == round(s.px(28), 1) and fr["h"] == round(s.px(38), 1)
    assert fr["label"] == "farrier"
    assert "#8FA6B0" in s.out[-1]  # the quench tub - a forge always has water at hand


def test_tanning_yard_two_row_layout_and_ditch_intake():
    # The pool covers 4 pits on a ditch (Hoshizora) and 12 on live water (Tango/Nagahara); this
    # reaches the branches between - an ODD pit count over one row, where the last row is short
    # and the pit loop must stop at `pits` rather than filling the grid.
    s = _town()
    s.tanning_yard(400, 400, rot=0, pits=7, water="ditch")
    y = s.M["tanning_yards"][0]
    assert (y["w"], y["h"]) == (58.0, 50.0)  # 2 rows of 4 -> 14 + 11*4 wide, 2*9 + 32 tall
    svg = "".join(s.out)
    assert svg.count('fill="#8E8A6A"') == 7  # exactly 7 pits drawn, not the 8 the grid would hold
    assert '#9CB4C8' in svg  # the gated intake cut (ditch variant), not staking frames


def test_intake_cut_is_lengthened_to_REACH_the_drawn_bank():
    # settlement-review 2026-08-08: the cut was a flat px(11), so a yard seated a little off its
    # ditch (Hoshizora, re-rotated onto the drain) drew a stub that stopped 4 ft short of the water
    # and read as a tab pinned to the yard. Nothing in the gate sees this - tanning_yard_on_water
    # asks whether the YARD is near a bank, never whether the CUT arrives - so the rule lives here.
    s = _town()
    s.field_channel([(340, 340), (460, 340)], "#9CB4C8", 2.0, 2.0)  # a drawn ditch 40px out from the yard's water edge
    s.tanning_yard(400, 400, rot=0, pits=4, water="ditch")
    svg = "".join(s.out)
    # yard is 41 tall, so its water edge sits at y=-20.5 local; the ditch centerline is 39.5 further
    assert 'height="39.5"' in svg and 'y="-60.0"' in svg  # the cut spans edge -> centerline, not a fixed 11
    assert s._intake_reach(400, 400, 0.0, 20.5) == pytest.approx(39.5)


def test_intake_cut_falls_back_to_its_stock_length_with_no_water_ahead():
    # A yard with nothing drawn in front of it (a fixture, or a bank that curves away) draws exactly
    # what it always did rather than a zero-length or runaway cut.
    s = _town()
    assert s._intake_reach(400, 400, 0.0, 20.5) is None
    s.tanning_yard(400, 400, rot=0, pits=4, water="ditch")
    assert 'height="11.0"' in "".join(s.out)


def test_tanning_yard_stream_variant_draws_staking_frames():
    s = _town()
    s.tanning_yard(400, 400, pits=4, water="stream")
    svg = "".join(s.out)
    assert '#9CB4C8' not in svg  # no intake cut on live water
    assert svg.count('stroke="#6B4F2A"') >= 4  # three stakes + the frame rail out in the shallows


# ---- feature 016: the charcoal district's trade works -------------------------------------------
def test_charcoal_yard_records_its_sheds_and_its_cooling_apron():
    """The apron is part of the record's contract, not decoration: charcoal self-heats, so a yard
    must have open ground to stand a fresh load apart from the conditioned stock. `sheds` floors at
    one - a yard with no roof over the conditioned stock is not a charcoal yard."""
    s = _town()
    s.charcoal_yard(400, 400, rot=-17, sheds=2)
    s.charcoal_yard(700, 700, sheds=0)  # floored
    a, b = s.M["charcoal_yards"]
    assert a["sheds"] == 2 and b["sheds"] == 1
    assert len(a["apron"]) == 4 and a["w"] == 88 and a["h"] == 58
    assert a["label"] == "charcoal yard" and a["rot"] == -17.0


def test_kiln_draws_a_works_and_records_its_body_and_its_quarters():
    """A kiln is a WORKS, not a lone glyph (GM 2026-07-27): the kiln itself, the throwing shed, the
    clay pit, the fuel stack, its own private well, and the cottages of the households that work
    it. `body` and `quarters` are part of the record's contract - kiln_keeps_fire_gap measures from
    the body, and a record with neither is a rule nobody can apply."""
    s = _town()
    s.kiln(400, 400)
    k = s.M["kilns"][0]
    # The caption says "kiln works", not "tile kiln" and not a bare "kiln" (GM 2026-07-27): the
    # feature is the kiln PLUS its drying shed, clay pit, fuel stack, well and its workers' cottages,
    # so naming it after one building inside it under-describes what the reader is looking at.
    assert (k["w"], k["h"]) == (140.0, 120.0) and k["label"] == "kiln works"
    assert len(k["body"]) == 5 and (k["body"][2], k["body"][3]) == (46.0, 16.0)
    assert len(k["quarters"]) == 2  # the default works houses two households
    # the cottages stand a clear fire gap BELOW the kiln body, which is the whole point of the
    # works' otherwise empty middle
    assert min(q[1] for q in k["quarters"]) - (k["body"][1] + 8) >= 60


def test_kiln_cottage_count_is_clamped_to_the_one_to_three_band():
    """Two or three households is the works we draw; a real kiln district could be a dozen, and
    that liberty is recorded in research/urban-features.md rather than taken silently here."""
    s = _town()
    s.kiln(300, 300, cottages=0)
    s.kiln(700, 300, cottages=9)
    assert len(s.M["kilns"][0]["quarters"]) == 1
    assert len(s.M["kilns"][1]["quarters"]) == 3


def test_kiln_keeps_its_own_private_well():
    """Clay cannot be weathered, wedged or thrown without water, so the well is a premises fixture
    like the brewery's - and private for the same reason, so it never counts toward the
    settlement's public idobata."""
    s = _town()
    before = len(s.M.get("wells", []))
    s.kiln(400, 400)
    added = s.M["wells"][before:]
    assert len(added) == 1 and added[0].get("private") is True


def test_refining_forge_records_its_two_hearths():
    """Two hearths because the refining is a TWO-STAGE process on both sides of the research - the
    Japanese okaji and the Chinese chao fining both work the iron through more than one heat."""
    s = _town()
    s.refining_forge(400, 400, label="refining forge")
    r = s.M["refining_forges"][0]
    assert r["hearths"] == 2 and (r["w"], r["h"]) == (74, 48)


def test_border_line_records_a_poly_with_no_footprint():
    """A jurisdictional line has no w/h on purpose: it reserves nothing and blocks nothing, which
    is why it is overlap-exempt. It also must NOT register a placement footprint."""
    s = _town()
    before = len(s.placed)
    s.border_line([(900, -20), (900, 1020)])
    b = s.M["borders"][0]
    assert b["poly"] == [[900, -20.0], [900, 1020.0]] and b["label"] == ""
    assert "w" not in b and "h" not in b
    assert len(s.placed) == before  # nothing reserved


def test_border_line_caption_defaults_to_the_lines_midpoint_and_is_registered():
    """The caption goes through self.label(), so the label-collision checks can see it. An earlier
    draft emitted raw <text>, which is invisible to every label check - and duly shipped a border
    caption sitting on a wellhead with a green gate."""
    s = _town()
    n = len(s.M["labels"])
    s.border_line([(900, 0), (900, 400), (900, 800)], label="the Fox border")
    assert len(s.M["labels"]) == n + 1
    assert s.M["labels"][-1][-1] == "the Fox border"
    s2 = _town()
    m = len(s2.M["labels"])
    s2.border_line([(900, 0), (900, 800)], label="pinned", label_xy=(700, 300))
    assert len(s2.M["labels"]) == m + 1


def test_trade_caption_tilts_and_rotates_its_reserved_band():
    s = _town()
    s.brewery(500, 500, rot=150)
    L = s.M["labels"][-1]
    assert L[5] == "brewery" and len(L) == 8 and L[7] == -30.0
    # the caption hangs off the ROTATED lower edge - the seat swings off plumb with the tilt
    assert (L[0] + L[2]) / 2 > 500 and (L[1] + L[3]) / 2 > 500
    band = s.block_polys[-1]
    assert band[0][1] != band[1][1]  # the reserved caption band rotated with it
    s2 = _town()
    s2.brewery(500, 500, rot=90)
    assert len(s2.M["labels"][-1]) == 6  # square rotation: the level path, byte-identical record

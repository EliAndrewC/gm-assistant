"""Guards on the researched constants - the couplings that are stated in prose and would otherwise
drift silently."""

from l7r.diagram.check_village.segments_07c_moats_drains_and_edges import _WEB_REACH
from l7r.diagram.hamletgen.consts import BUNDLE_PITCH, MIN_WEB_GAP, WEB_CLEARANCE, WEB_REACH_FT


def test_the_web_reach_is_one_bundle_pitch_in_the_generator_and_in_the_gate() -> None:
    """THREE copies of one number, and this is what stops them drifting.

    `WEB_REACH_FT` is what the generator lays the web to satisfy, `_WEB_REACH` is what
    `farmhouses_reach_a_way` measures against, and both ARE `BUNDLE_PITCH` - the ground one
    homestead occupies, which is the distance at which a lane passes your own plot or your
    neighbor's. The gate deliberately does not import the generator's constant (a check that reads
    the value it is checking cannot catch that value being wrong), so the coupling has to live
    somewhere, and it lives here.

    If you are changing the reach, change all three and say why in `consts.py` - the number is
    derived from research, not tuned to make maps pass."""
    assert WEB_REACH_FT == BUNDLE_PITCH
    assert _WEB_REACH == BUNDLE_PITCH


def test_a_web_lane_reserves_far_less_ground_than_a_lane_the_houses_front() -> None:
    """The two clearances exist to be different. `LANE_CLEARANCE` (40) holds a steading off a lane it
    FRONTS; `WEB_CLEARANCE` is for a way that runs behind and between the plots, which the sources
    describe as colonised by the adjoining house. Collapsing them is what made an early version of
    the web grow the pool's clusters by up to 97%."""
    from l7r.diagram.hamletgen.consts import LANE_CLEARANCE

    assert WEB_CLEARANCE < LANE_CLEARANCE


def test_the_web_only_threads_a_gap_a_person_can_walk() -> None:
    """`MIN_WEB_GAP` is the least room between two steadings a web lane will be cut through - a
    3 ft tread plus a hand's breadth each side, doubled for the two neighbors. It must stay well
    under the pitch, or there would be no gap in an ordinary row that qualifies."""
    assert 0 < MIN_WEB_GAP < BUNDLE_PITCH / 2

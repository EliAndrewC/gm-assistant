"""Unit tests for the crossings, the notice board, and the map frame (`hamletgen/frame.py`).

Split from test_hamletgen.py by feature 111; test bodies verbatim. See hamletgen/CLAUDE.md.
"""

from l7r.diagram import hamletgen as hg


def test_stage_notice_reseats_a_board_the_frame_would_lose():
    """The board re-seat branch: place_kosatsuba maximises traffic along the WHOLE way network, so
    a lane arm running past the cluster can seat the board outside the house cloud - where
    crop_to_content (which frames hard features only) would drop it off the sheet. stage_notice
    must then pop the board AND its caption and re-seat it on a lane verge inside the cloud.
    Exercised directly with a stub settlement: no rolled seed reaches this branch any more (the
    2026-08-16 well/lane re-rolls un-covered it), and hunting seeds is fragile where a direct
    call is exact."""

    class _StubS:
        def __init__(self):
            self.M = {
                "houses": [{"x": x, "y": y} for x in (440.0, 520.0, 600.0) for y in (440.0, 520.0, 600.0)],
                "kosatsuba": [{"x": 900.0, "y": 100.0}],
                "labels": [[0, 0, 0, 0], [880.0, 90.0, 60.0, 12.0, 0.0, "notice board"]],
                "lanes": [
                    {"pts": [(-200.0, 0.0), (200.0, 0.0)], "connector": True},  # skipped: connector
                    {"pts": [(300.0, 520.0), (700.0, 524.0)]},  # verge seats inside AND outside the cloud
                ],
            }
            self.reseated: list[tuple[float, float, float]] = []

        def place_kosatsuba(self):
            return (900.0, 100.0)  # outside the cloud - the frame would lose it

        def _fits(self, x, y, w, h, corridors=False):
            return x >= 500.0  # some verge candidates refused, so the refusal path runs too

        def fixture_clear_of_water(self, x, y, half):
            # a "stream" across the west half of the verge, so the re-seat's water REFUSAL runs too
            # (the same reason `_fits` above refuses part of the range). The predicate's own behavior
            # is covered where it lives, in settlement/structures/fixtures.py; what this pins is that
            # the re-seat consults it at all - without the call a board lands in the water, which is
            # exactly what cohort seed 13 shipped.
            return x >= 540.0

        def kosatsuba(self, x, y, rot=0.0):
            self.reseated.append((x, y, rot))
            self.M["kosatsuba"].append({"x": x, "y": y})

    s = _StubS()
    hg.stage_notice(s, None)  # type: ignore[arg-type]
    assert s.reseated, "the board was not re-seated"
    bx, by, _rot = s.reseated[0]
    assert 440.0 <= bx <= 600.0 and 440.0 <= by <= 600.0, f"re-seated outside the cloud: {(bx, by)}"
    assert bx >= 540.0, f"re-seated into the stub's water at {(bx, by)} - the re-seat must consult fixture_clear_of_water"
    assert not any(len(lb) > 5 and lb[5] == "notice board" for lb in s.M["labels"]), "orphan caption left behind"
    assert len(s.M["kosatsuba"]) == 1, "old board not popped"

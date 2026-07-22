#!/usr/bin/env python3
"""Automated tests for Mode B settlement maps (diagram skill).

Regenerates every village in pool/ from its generator and runs the full
check_village gate over the resulting manifest. This pins the whole Mode B
process: any change to settlement.py or a village spec that breaks an invariant
(no overlaps, every field ringed, households-consistent house counts, channels
anchored, no label overlaps, ...) fails here.

Works under pytest OR standalone:
    python3 -m pytest test_villages.py -q     # from the diagram skill directory
    python3 test_villages.py                  # no pytest required
"""

import glob
import json
import os
import runpy
import sys

import pytest

import check_village

HERE = os.path.dirname(os.path.abspath(__file__))
POOL = os.path.join(HERE, "pool")


def _is_village_gen(gen):
    """A Mode B VILLAGE gen builds on the settlement engine (`settlement.py`) and emits a JSON manifest the
    check_village gate reads. Mode A COMPOUND gens (built on `compound.py`, e.g. ochiba-recomposed) also live
    in pool/ but are hand-plan SVGs with NO village manifest - running one produces nothing to gate (and may
    raise SystemExit from its own `__main__` guard). They are not villages, so this test skips them; they carry
    their own tests. Discriminate by which engine the gen imports (every village gen imports settlement; no
    compound gen does - verified across the pool)."""
    with open(gen) as fh:
        src = fh.read()
    return "settlement import" in src or "import settlement" in src


GENERATORS = sorted(g for g in glob.glob(os.path.join(POOL, "*", "*.gen.py")) if _is_village_gen(g))


def _regen_and_gate(gen):
    """Run a village generator, then its gate; return True if every check passes.
    Runs the generator IN-PROCESS (not as a subprocess) so coverage measures settlement.py.
    The gate reads the JSON manifest, never the PNG, so DIAGRAM_SKIP_RENDER skips the resvg
    raster - cheap since the resvg switch, but still pure waste in the test loop."""
    os.environ["DIAGRAM_SKIP_RENDER"] = "1"
    try:
        runpy.run_path(gen, run_name="__main__")
    finally:
        del os.environ["DIAGRAM_SKIP_RENDER"]
    manifest = gen[: -len(".gen.py")] + ".json"
    assert os.path.exists(manifest), f"{os.path.basename(gen)} produced no manifest"
    return check_village.main(manifest) == 0


def test_at_least_one_village_exists():
    assert GENERATORS, "no *.gen.py village generators found in pool/"


def _channels_under_plots(svgpath):
    """SVG-level z-order audit: every field channel (the #6C9CBE supply / #7C9EB0 drain strokes)
    must draw OVER the paddy plots it crosses. A channel whose midpoint lies inside a plot polygon
    that appears LATER in the document is painted over - the invisible-ditch-net defect (GM
    2026-07-21: Hoshizora's canals "rendering below the rice paddies"; also Hikari-no-sato's
    first comb under its second comb's plots, and the cities' residual 2nd-fan hole). This is
    deliberately an SVG test, not a manifest check: scatter/paint order is not manifest-recorded,
    same as the per-tuft skips. Returns the covered channels as (x, y) midpoints."""
    import re

    with open(svgpath) as fh:
        svg = fh.read()
    plots = []
    for m in re.finditer(r'<polygon points="([^"]+)" fill="#[0-9A-Fa-f]{6}" stroke="#[0-9A-Fa-f]{6}" stroke-width="2"', svg):
        plots.append((m.start(), [tuple(map(float, p.split(","))) for p in m.group(1).split()]))
    covered = []
    for m in re.finditer(r'<path d="M([^"]+)" fill="none" stroke="#(?:6C9CBE|7C9EB0)"', svg):
        coords = [tuple(map(float, p.split(","))) for p in m.group(1).replace(" L", ";").split(";")]
        mid = coords[len(coords) // 2]
        if any(pos > m.start() and check_village.point_in_poly(mid[0], mid[1], pts) for pos, pts in plots):
            covered.append((round(mid[0]), round(mid[1])))
    return covered


def _typical_cell_acres(svgpath, ftpx):
    """Real-feet area of the TYPICAL leveled paddy cell (a bund-stroked plot polygon), taking the mean
    of the 45th-75th percentile band (the regular interior cells, above the edge wedges). Pins the
    ~0.05-acre paddy calibration (GM 2026-07-22, see settlements.md 'Paddy cell size'). SVG-measured,
    not a manifest gate, because villages do not record plot_polys - same tier as the ditch z-order audit."""
    import re
    import statistics

    with open(svgpath) as fh:
        svg = fh.read()

    def _sl(poly):
        return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))) / 2

    areas = sorted(
        _sl([tuple(map(float, p.split(","))) for p in m.group(1).split()]) * ftpx * ftpx
        for m in re.finditer(r'<polygon points="([^"]+)" fill="#[0-9A-Fa-f]{6}" stroke="#[0-9A-Fa-f]{6}" stroke-width="2"', svg)
    )
    if len(areas) < 8:
        return None
    band = areas[int(len(areas) * 0.45) : int(len(areas) * 0.75)]
    return statistics.mean(band) / 43560


# one test per village (not one loop over all): a failure names its map directly, and a
# parallel runner (pytest-xdist) can spread the regens instead of serializing them in one test
@pytest.mark.parametrize("gen", GENERATORS, ids=[os.path.basename(g) for g in GENERATORS])
def test_village_passes_gate(gen):
    assert _regen_and_gate(gen), f"{os.path.basename(gen)} failed the gate"
    svg = gen[: -len(".gen.py")] + ".svg"
    covered = _channels_under_plots(svg)
    assert not covered, (
        f"{os.path.basename(gen)}: {len(covered)} field channel(s) painted UNDER a later plot at {covered[:5]} - route the comb net through the LATE water block (field_channel late=True; see settlement._water)"
    )
    # PADDY CELL SIZE stays in the calibrated real-feet band (GM 2026-07-22). Every valley-paddy comb map
    # (all villages + cities) and the two HILL-RICE archetype demos - contour_terraces (Tanada) and
    # ribbon_valley (Yatsuda), whose steps/bands are now split into leveled cells - hold to it; the band
    # spans plot_texture's small_irregular->large_block knobs (~0.036-0.0675) plus slop and, above all,
    # catches a regression back to the old hand-set ~0.13 ac (or the old field-wide terrace/ribbon bands).
    # The polder / dike-pond archetypes are DELIBERATELY larger (Buck's ~1 mu parcels, 0.4-0.6 ha ponds -
    # true-scale per settlements.md line ~102), so they are excluded, not held to the leveled-cell target.
    with open(gen[: -len(".gen.py")] + ".json") as _fh:
        manifest = json.load(_fh)
    meta = manifest.get("meta", {})
    _valley = meta.get("scale") in ("village", "city")
    _hill_rice = meta.get("field_archetype") in ("contour_terraces", "ribbon_valley")
    if _valley or _hill_rice:
        cell = _typical_cell_acres(svg, meta.get("ftpx") or 2)
        assert cell is not None and 0.030 <= cell <= 0.072, (
            f"{os.path.basename(gen)}: typical paddy cell {cell:.3f} ac is outside the calibrated 0.030-0.072 band (see settlements.md 'Paddy cell size')"
        )


if __name__ == "__main__":
    rc = 0
    for g in GENERATORS:
        ok = _regen_and_gate(g)
        print(("PASS " if ok else "FAIL ") + os.path.basename(g))
        rc |= 0 if ok else 1
    sys.exit(rc)

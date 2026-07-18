#!/usr/bin/env python3
"""ochiba-recomposed.gen.py - round-trip TEST of the perimeter-first placer (feature 008).

Encode the EXISTING hand-authored Ochiba magistracy (pool/ochiba-magistracy.svg) as a
feet-first CompoundProgram - its real envelope, its real court-spine, and its real building
masses measured off the finished SVG at 3 px = 1 ft - then run it through compound.place()
and compound.emit_svg(). The point is not to replace Ochiba but to see whether the placer,
given Ochiba's ACTUAL program, composes it the way the GM hand-composed it, and to surface
exactly where the two diverge (that divergence is the finding of the test).

Garden pavilions and point features (bath, wells, latrines, porch, privy, fire-tubs) are NOT
massed perimeter buildings - they are hand-placed in the final map regardless - so they are
omitted here; the placer only arranges the wall-ranging masses.

Run:  python3 pool/ochiba-recomposed.gen.py   (from the skill dir)
"""

from __future__ import annotations

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import compound as C  # noqa: E402

OUT_SVG = "pool/ochiba-recomposed-draft.svg"


def ochiba_program() -> C.CompoundProgram:
    env = C.Envelope(w_ft=267.0, h_ft=200.0, divider_ft=100.0, gate_w_ft=13.3)
    # real open courts measured off the finished map
    spine = (
        C.CourtZone("garden", 107.0, 53.0, 97.0, 45.0),  # inner garden (center of inner court)
        C.CourtZone("oshirasu", 73.0, 139.0, 120.0, 35.0),  # the sanded hearing court
        C.CourtZone("forecourt", 95.0, 180.0, 76.0, 17.0),  # just inside the main gate
    )
    b = C.BuildingSpec
    buildings = (
        # inner (residence) court
        b("residence (W)", "lord", 90.0, 25.0, "inner", "N", order=10),
        b("residence (E)", "lord", 93.0, 25.0, "inner", "N", order=9),
        b("servants", "service", 73.0, 13.0, "inner", "N", order=2, rank=2),  # rear service strip
        b("kitchen", "service", 40.0, 33.0, "inner", "W", order=5),
        b("Inari shrine", "shrine", 37.0, 31.0, "inner", "E", order=5),
        b("cinnabar workshop", "shrine", 37.0, 24.0, "inner", "E", order=4),
        b("karo's house", "lord", 37.0, 23.0, "inner", "divider", order=3),
        # outer (administrative) court
        b("office hall", "lord", 120.0, 28.0, "outer", "divider", order=10),
        b("tax archive", "kura", 32.0, 28.0, "outer", "W", order=6),
        b("senior retainers", "service", 51.0, 17.0, "outer", "W", order=4),
        b("granary", "kura", 50.0, 26.0, "outer", "E", order=6),
        b("barracks", "service", 31.0, 33.0, "outer", "E", order=4),
        b("cell", "cell", 18.0, 15.0, "outer", "E", order=1),
        b("gatehouse", "dark", 40.0, 14.0, "outer", "S", order=8),
        b("stables", "service", 29.0, 22.0, "outer", "S", order=5),
    )
    return C.CompoundProgram("Ochiba County Magistracy (placer round-trip)", env, spine, buildings)


def main() -> int:
    program = ochiba_program()
    result = C.place(program)
    with open(OUT_SVG, "w", encoding="utf-8") as fh:
        fh.write(C.emit_svg(program, result))
    print(f"wrote {OUT_SVG}: {len(result.placed)} placed, {len(result.overflow)} overflow")
    for p in sorted(result.placed, key=lambda p: (p.spec.court, p.spec.wall, p.x_ft, p.y_ft)):
        print(f"  placed  {p.spec.name:22s} {p.spec.court:5s} {p.spec.wall:7s} @ ({p.x_ft:.0f},{p.y_ft:.0f})")
    for s in result.overflow:
        print(f"  OVERFLOW {s.name:21s} {s.court:5s} {s.wall:7s} ({s.w_ft:.0f}x{s.h_ft:.0f} ft)")
    if os.environ.get("DIAGRAM_SKIP_RENDER") != "1":
        subprocess.run(
            ["resvg", "--width", "2400", "--serif-family", "DejaVu Serif", OUT_SVG, OUT_SVG[:-4] + ".png"],
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

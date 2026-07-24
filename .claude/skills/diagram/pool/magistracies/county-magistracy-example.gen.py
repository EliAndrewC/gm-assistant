#!/usr/bin/env python3
"""county-magistracy-example.gen.py - render the placer's built-in generic worked example.

The program itself lives in compound.py (`county_magistracy_program()`) - a generic county
magistracy declared entirely in feet, kept as the placer's worked example alongside the
ochiba-roundtrip-test. This gen is just the pool wiring for it: render-sync regenerates
every `pool/*/*.gen.py` from its own directory, so wrapping the program in a gen keeps the
gitignored png fresh in main. Before this gen existed the png was a one-off hand render and
silently went stale (caught 2026-07-24).

Run:  python3 pool/magistracies/county-magistracy-example.gen.py   (from the skill dir)
"""

from __future__ import annotations

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import compound as C  # noqa: E402

OUT_SVG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "county-magistracy-example.svg")


def main() -> int:
    program = C.county_magistracy_program()
    result = C.place(program)
    with open(OUT_SVG, "w", encoding="utf-8") as fh:
        fh.write(C.emit_svg(program, result))
    print(f"wrote {OUT_SVG}: {len(result.placed)} placed, {len(result.overflow)} overflow")
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

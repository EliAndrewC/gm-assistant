#!/usr/bin/env python3
"""Crop regions of a rendered map by WORLD (manifest) coordinates, several at once.

WHY (2026-07-25): reviewing a map means cropping the spot you care about and looking at it, and the
coordinates you have are always manifest coordinates while the PNG is in pixels. That conversion -
read the `.svg` viewBox, scale by png_width/viewBox_width, offset by the viewBox origin - got
hand-written from scratch five times in one session, once with the arithmetic wrong, which cost a
round trip to notice and another to fix. It is the same six lines every time, so it lives here now.

Taking MANY regions in one invocation is the point: the review loop is "crop everything you want to
see, then look at it all", not one crop per turn (see "Batch the rendered-map inspection" in this
directory's CLAUDE.md).

    python3 -m l7r.diagram.tools.crop_map pool/towns/hoshizora 1600,900,220 1200,400,150
    python3 -m l7r.diagram.tools.crop_map pool/hamlets/moritono --box 2100,150,2418,760 --zoom 1.7
    python3 -m l7r.diagram.tools.crop_map pool/villages/ueda --whole --zoom 0.5      # the whole map, downscaled

Regions are `x,y,radius` (a square centered on a manifest point) or `--box x0,y0,x1,y1`. Everything
is clamped to the image, so a region near the edge crops to what exists instead of erroring. Prints
one output path per line - feed those straight to Read.
"""

from __future__ import annotations

import os
import re
import sys

Box = tuple[int, int, int, int]


def view_box(svg_path: str) -> tuple[float, float, float, float]:
    """The map's viewBox (ox, oy, w, h) - the window of world coordinates the PNG actually shows."""
    with open(svg_path) as fh:
        head = fh.read(4000)
    m = re.search(r'viewBox="([-\d.]+) +([-\d.]+) +([-\d.]+) +([-\d.]+)"', head)
    if not m:
        raise SystemExit(f"no viewBox in {svg_path} - is it a rendered map?")
    return (float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)))


def crop(base: str, regions: list[Box], zoom: float, outdir: str) -> list[str]:
    """Write one PNG per region; returns the paths. `base` is the map path without extension."""
    from PIL import Image

    ox, oy, vw, _vh = view_box(base + ".svg")
    im = Image.open(base + ".png")
    k = im.size[0] / vw  # png px per world unit; the y scale is the same (the render is uniform)
    name = os.path.basename(base)
    os.makedirs(outdir, exist_ok=True)
    out: list[str] = []
    for i, (x0, y0, x1, y1) in enumerate(regions):
        px = [round((x0 - ox) * k), round((y0 - oy) * k), round((x1 - ox) * k), round((y1 - oy) * k)]
        px = [max(0, min(px[0], im.size[0])), max(0, min(px[1], im.size[1])), max(0, min(px[2], im.size[0])), max(0, min(px[3], im.size[1]))]
        if px[2] - px[0] < 2 or px[3] - px[1] < 2:
            print(f"  (region {i} is outside the rendered view {ox:.0f},{oy:.0f} {vw:.0f}x{_vh:.0f} - skipped)", file=sys.stderr)
            continue
        piece = im.crop((px[0], px[1], px[2], px[3]))
        if zoom != 1.0:
            piece = piece.resize((max(1, round(piece.size[0] * zoom)), max(1, round(piece.size[1] * zoom))))
        path = os.path.join(outdir, f"{name}-{i}.png")
        piece.save(path)
        out.append(path)
    return out


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:]]
    if not args:
        print(__doc__)
        return 1
    zoom, outdir, regions, base, whole = 1.0, os.environ.get("CROP_OUT", "/tmp/crop-map"), [], "", False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--zoom":
            zoom = float(args[i + 1])
            i += 2
        elif a == "--out":
            outdir = args[i + 1]
            i += 2
        elif a == "--whole":
            whole = True
            i += 1
        elif a == "--box":
            x0, y0, x1, y1 = (float(v) for v in args[i + 1].split(","))
            regions.append((int(x0), int(y0), int(x1), int(y1)))
            i += 2
        elif not base:
            base = a.removesuffix(".png").removesuffix(".svg").removesuffix(".json")
            i += 1
        else:
            x, y, r = (float(v) for v in a.split(","))
            regions.append((int(x - r), int(y - r), int(x + r), int(y + r)))
            i += 1
    if not base:
        raise SystemExit("give a map path (without extension), e.g. pool/towns/hoshizora")
    if whole or not regions:
        ox, oy, vw, vh = view_box(base + ".svg")
        regions = [(int(ox), int(oy), int(ox + vw), int(oy + vh))]
    for p in crop(base, regions, zoom, outdir):
        print(p)
    return 0


if __name__ == "__main__":
    from l7r.diagram._invocation import guard

    # REFUSE unless invoked through this project's make (feature 127). At the TOP of the
    # entry point, never in a loop - the determination reads /proc and is cached per process.
    guard("l7r.diagram.tools.crop_map")
    sys.exit(main(sys.argv))

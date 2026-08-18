"""Scatter audit (feature 108) - adjudicate drawn ground-cover BASES against the engine's keep-outs.

The manifest does not record scatter (each tuft is draw-time ink), so the rendered SVG is the only
source of truth for where ground cover actually stands - which is why the 2026-08-16 cut-bank
review had to hand-build this parse across ~21 tool uses. This script is that parse made permanent:
it extracts every scatter base point from a pool map's SVG and tests each against the SAME keep-out
geometry the engine's scatter skips at draw time.

OBSERVE-DON'T-RESTATE (diagram CLAUDE.md "A DIAGNOSTIC that restates what it observes will lie to
you, or die"): the keep-outs are obtained by executing the ENGINE'S OWN code on the recorded
manifest - `Settlement._watercourse_segs(..., channel_margin=px(_BANK_MARGIN_FT))` for water + the
irrigation cut-bank margin, and the manifest's `fields[].outline` + `dry_plots[].poly` padded by
`Settlement._CROP_MARGIN_FT` through the same `boxed_*` helpers the scatter uses. No margin rule is
re-implemented here, so a future rule change moves this audit's verdicts automatically.

Families: blade / dot / pine / crown are adjudicated; reed is REPORT-ONLY (reeds are the water
fringe by doctrine - research/vegetation.md). Bases only - blade TIPS may lean a few real feet by
the disclosed departure. Zero bases parsed is a LOUD failure (exit 2), never a clean pass: a
styling drift in the engine's emission must read as "the audit is broken", not "the map is clean".

CLI contract (exit 0 clean / 1 violations / 2 unusable):
specs/108-review-loop-efficiency/contracts/scatter-audit-cli.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, cast

from l7r.diagram.settlement import Settlement
from l7r.diagram.settlement._geom import CROWN_FILLS, boxed_grid, boxed_hit, boxed_polys, boxed_seg_hit, boxed_segs

Base = tuple[float, float]

_NUM = r"(-?[\d.]+)"
# Anchors are the engine's exact emission styling (the grass bucket in settlement/land/cover.py, the
# reed bucket in settlement/land/wet.py; research.md R2). Attribute
# order is stable because one code path emits each family.
_BLADE_GROUP = re.compile(r'<g stroke="#A7A860"[^>]*>(.*?)</g>', re.S)  # commons grass bucket
_REED_GROUP = re.compile(r'<g stroke="#6E9377"[^>]*>(.*?)</g>', re.S)  # marsh reed bucket
_LINE_BASE = re.compile(rf'<line x1="{_NUM}" y1="{_NUM}"')  # a blade/reed line's root
_TRANSLATE_G = re.compile(rf'<g transform="translate\({_NUM},{_NUM}\)[^"]*"[^>]*>')  # grove clumps draw their canopy in a translated group
_DOT = re.compile(rf'<circle cx="{_NUM}" cy="{_NUM}" r="[\d.]+" fill="#94A063"')  # brush dot
_PINE = re.compile(rf'<line x1="{_NUM}" y1="{_NUM}" x2="{_NUM}" y2="{_NUM}" stroke="#7A6A48"')  # trunk (branches are #6E8452 - canopy ink, not a base)
# THE CROWN FILLS COME FROM THE ENGINE, not from a copy here (2026-08-17). This pattern used to
# hardcode #6E8B4A / #7C9856 / #87A45C - none of which the engine has painted for some time - so the
# audit parsed ZERO crowns on maps recording thousands and still reported "crown checked". A family
# that sees nothing looks exactly like a family with nothing wrong, which is the same shape as a
# check that never runs, one level down inside the tool reviewers quote as evidence.
_CROWN = re.compile(rf'<circle cx="{_NUM}" cy="{_NUM}" r="{_NUM}" fill="(?:{"|".join(c.lstrip("#") and re.escape(c) for c in CROWN_FILLS)})"')

ADJUDICATED = ("blade", "dot", "pine", "crown")
DENSITY_BANDS = ((0.0, 15.0), (15.0, 30.0), (30.0, 45.0))
# Coordinate-quantization slack: the engine adjudicates scatter at full float precision and then
# WRITES the SVG at %.1f, so a base the engine legally seated a hair outside a keep-out can parse
# back a few hundredths INSIDE it. 0.15 px is the same slack the engine's own margin unit tests
# use (tests/settlement/test_homestead_parts.py); a real defect stands whole pixels deep.
_QUANT_EPS = 0.15


def _translated_spans(svg: str) -> list[tuple[int, int, float, float]]:
    """Every `<g transform="translate(tx,ty)">...</g>` span, as (start, end, tx, ty).

    Nested groups are not produced by this engine's emitters, so a flat scan of matched pairs is
    enough; a span is closed at the first `</g>` after its opening tag."""
    spans: list[tuple[int, int, float, float]] = []
    for m in _TRANSLATE_G.finditer(svg):
        end = svg.find("</g>", m.end())
        spans.append((m.end(), len(svg) if end < 0 else end, float(m.group(1)), float(m.group(2))))
    return spans


def parse_bases(svg: str) -> dict[str, list[Base]]:
    """Every scatter BASE point per family, in document order, in WORLD coordinates.

    Most element coords already are world coords - `crop_to_content` crops via the viewBox and never
    rewrites coordinates, which `crop_map.py` relies on too. But GROVE CLUMPS are not: `_draw_grove`
    emits its canopy inside `<g transform="translate(cx,cy)">`, so a crown's `cx`/`cy` are LOCAL to
    the clump. Reading them raw put a crown at world (710.9, 1815.8) on the map at (4.9, -14.2).

    THE COUNT GUARD COULD NOT SEE THAT, which is the transferable half (settlement-review, Mizuguchi
    2026-08-18). `tests/tools/test_scatter_audit.py` asserted `parsed >= recorded`, and 1,446 >= 1,446
    passed while ~78% of the crown family was being adjudicated in the wrong place - the audit
    reported 0 violations on a map that really had 5 crown bases inside the crop margin. A coverage
    guard that counts is blind to a family that sees the right NUMBER of things somewhere else; the
    guard is positional now, and this parser resolves the transform."""
    fams: dict[str, list[Base]] = {"blade": [], "dot": [], "pine": [], "crown": [], "reed": []}
    for group, fam in ((_BLADE_GROUP, "blade"), (_REED_GROUP, "reed")):
        for body in group.findall(svg):
            fams[fam] += [(float(x), float(y)) for x, y in _LINE_BASE.findall(body)]
    fams["dot"] = [(float(x), float(y)) for x, y in _DOT.findall(svg)]
    fams["pine"] = [(float(x), float(y)) for x, y, _, _ in _PINE.findall(svg)]
    spans = _translated_spans(svg)

    def _offset(at: int) -> tuple[float, float]:
        for lo, hi, tx, ty in spans:
            if lo <= at < hi:
                return tx, ty
        return 0.0, 0.0

    for m in _CROWN.finditer(svg):
        ox, oy = _offset(m.start())
        fams["crown"].append((float(m.group(1)) + ox, float(m.group(2)) + oy))
    return fams


class _EngineView:
    """The minimal `self` the engine's geometry methods need, bound to a RECORDED manifest: `M`
    plus the declared scale. The methods executed on it are Settlement's own (see module
    docstring) - this class holds state, never logic."""

    def __init__(self, manifest: dict[str, Any]) -> None:
        self.M = manifest
        self.ftpx = float(manifest["meta"]["ftpx"])


def _water_segs(view: _EngineView, extra: float = 0.0) -> list[tuple[Any, float]]:
    """The engine's watercourse keep-out at its cut-bank margin, widened by `extra` px (the density
    bands re-ask the same geometry at growing offsets)."""
    s = cast(Settlement, view)
    margin = Settlement.px(s, Settlement._BANK_MARGIN_FT)
    segs = Settlement._watercourse_segs(s, channel_margin=margin)
    return [(pts, half + extra) for pts, half in segs]


def adjudicate(fams: dict[str, list[Base]], manifest: dict[str, Any], map_name: str) -> dict[str, Any]:
    """Test every adjudicated-family base against the water+cutbank and crop keep-outs; count the
    near-water density bands. Reed bases are counted only."""
    view = _EngineView(manifest)
    crop_pad = Settlement.px(cast(Settlement, view), Settlement._CROP_MARGIN_FT)
    wat = boxed_grid(boxed_segs(_water_segs(view, extra=-_QUANT_EPS)))  # violation test carries the quantization slack
    crop_polys = [f["outline"] for f in manifest.get("fields", []) if f.get("outline")]
    crop_polys += [d["poly"] for d in manifest.get("dry_plots", []) if d.get("poly")]
    crop = boxed_grid(boxed_polys(crop_polys, pad=crop_pad))
    bands = [boxed_grid(boxed_segs(_water_segs(view, extra=hi))) for _, hi in DENSITY_BANDS]

    violations: list[dict[str, Any]] = []
    density = dict.fromkeys((f"{int(lo)}-{int(hi)}" for lo, hi in DENSITY_BANDS), 0)
    for fam in ADJUDICATED:
        for x, y in fams[fam]:
            if boxed_seg_hit(x, y, wat.near(x, y)):
                violations.append({"x": x, "y": y, "family": fam, "keepout": "water+cutbank"})
            elif boxed_hit(x, y, crop.near(x, y), edge_pad=crop_pad - _QUANT_EPS):
                violations.append({"x": x, "y": y, "family": fam, "keepout": "crop"})
            else:
                for (lo, hi), grid in zip(DENSITY_BANDS, bands, strict=True):
                    if boxed_seg_hit(x, y, grid.near(x, y)):
                        density[f"{int(lo)}-{int(hi)}"] += 1
                        break
    return {
        "map": map_name,
        "families_checked": {"adjudicated": list(ADJUDICATED), "keepouts": ["water+cutbank", "crop"], "report_only": ["reed"]},
        "counts": {fam: len(pts) for fam, pts in fams.items()},
        "violations": violations,
        "density_bands": density,
    }


def format_report(report: dict[str, Any]) -> str:
    counts = report["counts"]
    lines = [
        f"scatter_audit: {report['map']}",
        "parsed: " + " ".join(f"{f}={counts[f]}" for f in ("blade", "dot", "pine", "crown", "reed")) + f" (total {sum(counts.values())})",
        "checked: families " + "/".join(report["families_checked"]["adjudicated"]) + " vs keep-outs " + ", ".join(report["families_checked"]["keepouts"]) + "  (reed: report-only)",
    ]
    lines += [f"VIOLATION family={v['family']} at ({v['x']}, {v['y']}) inside {v['keepout']}" for v in report["violations"]]
    lines.append(f"violations: {len(report['violations'])}")
    lines.append("density beyond water keep-out: " + " ".join(f"{band}px={n}" for band, n in report["density_bands"].items()))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Audit a pool map's drawn ground-cover scatter against the engine's keep-outs.")
    ap.add_argument("map", nargs="?", help="pool map stem or path (with or without .json/.svg)")
    ap.add_argument("--json", action="store_true", dest="as_json", help="emit the Report as JSON")
    ns = ap.parse_args(argv)
    if not ns.map:
        print("usage: python3 -m l7r.diagram.tools.scatter_audit <pool-map-path> [--json]", file=sys.stderr)
        return 2
    stem = re.sub(r"\.(json|svg)$", "", ns.map)
    svg_path, json_path = Path(stem + ".svg"), Path(stem + ".json")
    if not svg_path.is_file() or not json_path.is_file():
        print(f"scatter_audit: need BOTH {json_path} and {svg_path}", file=sys.stderr)
        return 2
    manifest = json.loads(json_path.read_text())
    if "ftpx" not in (manifest.get("meta") or {}):
        print("scatter_audit: manifest has no meta.ftpx - cannot convert real-feet margins", file=sys.stderr)
        return 2
    fams = parse_bases(svg_path.read_text())
    if sum(len(p) for p in fams.values()) == 0:
        # A parser that finds nothing is BROKEN until proven otherwise ("a check that never runs
        # looks exactly like a check that passes") - most likely the engine's scatter styling
        # drifted from the anchors at the top of this file.
        print("scatter_audit: ERROR - zero scatter bases parsed; suspect emission-styling drift, treat the AUDIT as broken (not the map as clean)", file=sys.stderr)
        return 2
    # ...AND A SINGLE BLIND FAMILY IS THE SAME FAILURE, one level down (2026-08-17). The zero-TOTAL
    # guard above cannot see a parser that lost ONE family: `crown` matched three fills the engine
    # had stopped painting, so this tool reported `crown=0 ... checked: blade/dot/pine/crown,
    # violations: 0` on maps recording thousands of crowns, and every review that quoted it was
    # quoting a family nobody had looked at. Where the MANIFEST records a feature the family draws,
    # parsing none of it is drift, not cleanliness.
    # COVERAGE, NOT MERELY NON-ZERO. The first version of this guard fired only at exactly zero, and
    # that is how the crown family went from 0% to 63% coverage and still reported "crown checked":
    # `CROWN_FILLS` had been made "exhaustive" while missing every woodland-commons canopy. A partial
    # family is the same failure as a blind one, just quieter - so compare what was PARSED against
    # what the manifest RECORDS. Crowns are recorded as a flat [x, y, r] run, hence the // 3.
    _rec_crowns = len(manifest.get("tree_crowns") or []) // 3
    if _rec_crowns and len(fams["crown"]) < _rec_crowns:
        print(
            f"scatter_audit: ERROR - parsed {len(fams['crown'])} crown bases but the manifest records {_rec_crowns} "
            f"({100 * len(fams['crown']) / _rec_crowns:.0f}% coverage); the emission styling has drifted from "
            f"`CROWN_FILLS` - treat the AUDIT as broken, not the map as clean",
            file=sys.stderr,
        )
        return 2
    report = adjudicate(fams, manifest, Path(stem).name)
    print(json.dumps(report) if ns.as_json else format_report(report))
    return 1 if report["violations"] else 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Feature 114's one-shot transformer: settlement/structures.py -> settlement/structures/ package.

Adapted from feature 113's split_city.py, which was adapted from 112's split_fields.py, which came
from feature 025's split_settlement.py. The lineage matters because the slicing rule is the part
worth preserving, and it is the part a fresh implementation gets wrong.

Run once from .claude/skills/diagram/:

    python3 ../../../specs/114-structures-package/split_structures.py

then prune the copied import headers with ruff (see PRUNE below) and delete the old file.

WHY the blocks are sliced as (previous node's end + 1 .. this node's end) rather than by the node's
own lineno: that span carries the decorator lines (@staticmethod sits ABOVE the `def`, and ast
reports FunctionDef.lineno at the `def`), the blank lines, and any comment block written above the
member. Slicing by node.lineno silently drops all three - and in this project the third is the real
loss, because a comment above a method is usually researched grounding. A "pure move" that drops a
why-comment is not pure. structures.py has this in force: URBAN carries an explanatory comment line
above it, and both class constants carry their measurement citations inline.
"""

import ast
import pathlib
import sys

SRC = pathlib.Path("settlement/structures.py")
PKG = pathlib.Path("settlement/structures")

# The partition, per specs/114-structures-package/data-model.md. Keys are class-body member names in
# SOURCE order. Unlike 113's CityMixin, this class DOES carry class-level constants (URBAN,
# SERVANT_RANGE_DEPTH_FT, _OFFICE_STANDOFF), so the Assign branch in member_name() fires here - as
# it did in 112 for the _PADDY_*_KINDS matrices. Each constant travels with the members that read it.
MODULES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "compounds": (
        "CompoundsMixin",
        "Walled compounds shown as a glyph on a settlement map: the samurai manor and the merchant estate.",
        # _estate_wall_clear is merchant_estate's own siting predicate, mirroring the
        # merchant_estate_wall_clear_of_* gate geometry - not a general placement helper, so it goes
        # with its caller (data-model.md; research R1b's rule).
        ("manor", "_estate_wall_clear", "merchant_estate", "merchant_estates"),
    ),
    "ground": (
        "GroundMixin",
        "Unbuilt GROUND SURFACES that reserve placement rather than structures that occupy it.",
        # Neither belongs to the structures subsystem: road belongs with water_ways.py's ways,
        # pasture with land.py's land surfaces. Isolated here so each eventual move is a one-file
        # change - feature 113's city/civic.py precedent. Full reasoning: research R1a.
        ("road", "pasture"),
    ),
    "urban": (
        "UrbanBuildingMixin",
        "The urban building glyph, its palette, and the per-building helpers that seat ONE of them.",
        ("URBAN", "building", "_dims", "try_building", "_face_street_rot", "open_face_rot"),
    ),
    "servants": (
        "ServantRangesMixin",
        "The nagaya pass that attaches a servant range to each ward samurai household, and the four probes that exist to serve it.",
        # The four door/solid probes sit textually beside building() and read like general placement
        # utilities, but a census gives each of them exactly one consumer: servant_ranges. Placement
        # follows the caller (research R1b). The two class constants move with the method that reads
        # them - a class attribute is as easy to lose in a split as a method and easier to overlook.
        (
            "SERVANT_RANGE_DEPTH_FT",
            "_OFFICE_STANDOFF",
            "_solid_records",
            "_blocks_any_door",
            "_door_is_clear",
            "_office_records",
            "servant_ranges",
        ),
    ),
    "packing": (
        "PackingMixin",
        "The two multi-building placement engines and the shortfall bookkeeping they share.",
        # rowpack walks an INDEX where pack POPs, and that asymmetry is a documented bug source
        # (skill CLAUDE.md, "Two placer bugs of the same shape") - an argument for keeping the two
        # where the difference is visible, not for separating them.
        ("rowpack", "pack", "_shortfall"),
    ),
    "captions": (
        "CaptionProbesMixin",
        "The primitives a siter uses to ask whether a caption fits, and whether a footprint would land under one.",
        # Distinct from castle_civic.py's place_caption, which is the draw-time seat LADDER; these
        # are the probes underneath it. Whether they should eventually join it is an OPEN question -
        # research R1c - deliberately recorded rather than silently decided.
        ("label_blockers", "label_caption_hw", "label_seat_clear", "clear_label_seat", "_under_a_caption"),
    ),
    "fixtures": (
        "PublicFixturesMixin",
        "The settlement's public street furniture and civic fixtures, and the two auto-siters that place them on the traffic.",
        # The largest module, and the one to watch. If it grows past ~500 lines or any member past
        # ~150, the seam is glyph-drawers (theater_stage, fire_tower, kosatsuba, drum_tower) vs
        # auto-siters (place_kosatsuba, place_punishment_spot). Recorded in data-model.md and the
        # package index so the next session inherits the seam rather than choosing one under pressure.
        ("theater_stage", "fire_tower", "kosatsuba", "place_kosatsuba", "place_punishment_spot", "drum_tower"),
    ),
}

# Section-divider comments that describe the OLD file's layout and would be actively misleading once
# the sections live in different files. structures.py has none today (checked): its only class-body
# comment above a member is URBAN's, which describes URBAN itself and travels correctly with it. The
# hook is kept because every predecessor needed it and the next split probably will.
DROP_BANNERS: tuple[str, ...] = ()


def member_name(node: ast.stmt) -> str | None:
    """The class-body member's name, for a def or a simple class-level assignment."""
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        return node.name
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    return None


def main() -> int:
    src = SRC.read_text()
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "StructuresMixin")

    # The parent header: everything above `class StructuresMixin:`. Copied wholesale into each module
    # and pruned by ruff afterwards (PRUNE below) - which reaches the same end state as computing each
    # module's used names by hand, without this script having to model name resolution.
    header = "".join(lines[: cls.lineno - 1])
    header = header.replace("from ._geom import", "from .._geom import")
    header = header.replace("from ._knobs import", "from .._knobs import")
    header = header.replace("from .core import Settlement", "from ..core import Settlement")
    header = header.replace(
        '"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""\n',
        "",
    )

    # Slice every class-body member into a block that carries its decorators, its blank lines and any
    # comment written above it.
    blocks: dict[str, str] = {}
    cursor = cls.lineno  # 1-based line of `class StructuresMixin:`; body text starts on the next line
    for node in cls.body:
        name = member_name(node)
        text = "".join(lines[cursor : node.end_lineno])
        # The same one-dot -> two-dot rewrite the header gets, applied to the BODY as well. 112 only
        # rewrote the header, because none of its methods had an in-body import; 113 found one
        # (city.py's _wall_point_at_arc does a LAZY `from .core import Settlement` inside its body)
        # which left alone silently resolves to a module that does not exist. structures.py has no
        # in-body import today, but the rewrite costs nothing and the next split inherits it.
        text = text.replace("from .core import", "from ..core import")
        text = text.replace("from ._geom import", "from .._geom import")
        text = text.replace("from ._knobs import", "from .._knobs import")
        if name is None:
            print(f"REFUSING: unnamed class-body member at line {node.lineno} ({type(node).__name__})", file=sys.stderr)
            return 1
        blocks[name] = text
        cursor = node.end_lineno

    assigned = [n for _, _, names in MODULES.values() for n in names]
    if len(assigned) != len(set(assigned)):
        dupes = sorted({n for n in assigned if assigned.count(n) > 1})
        print(f"REFUSING: a member is assigned to more than one module: {dupes}", file=sys.stderr)
        return 1
    if sorted(assigned) != sorted(blocks):
        missing = sorted(set(blocks) - set(assigned))
        extra = sorted(set(assigned) - set(blocks))
        print(f"REFUSING: partition does not cover the class. missing={missing} extra={extra}", file=sys.stderr)
        return 1

    PKG.mkdir(exist_ok=True)
    for mod, (mixin, doc, names) in MODULES.items():
        body = []
        for n in names:
            text = blocks[n]
            for banner in DROP_BANNERS:
                text = "".join(ln for ln in text.splitlines(keepends=True) if ln.strip() != banner)
            body.append(text)
        out = f'"""{doc}\n\nSplit from settlement/structures.py by feature 114 - see settlement/structures/CLAUDE.md for the index.\n"""\n\n{header}\nclass {mixin}:\n{"".join(body)}'
        (PKG / f"{mod}.py").write_text(out)
        print(f"wrote {PKG / mod}.py  ({len(out.splitlines())} lines, {len(names)} members)")

    init = '''"""The structures subsystem of the Mode B settlement engine.

Split from the 1,459-line settlement/structures.py by feature 114 (constitution Principle X clause
13). See CLAUDE.md in this directory for which submodule holds what.

Unlike settlement/fields/ and settlement/city/, this package was never ONE subsystem: structures.py
was feature 025's residue bucket, holding everything that was neither field, nor way, nor homestead,
nor funerary ground. So the seven submodules are grouped by what a session comes here to CHANGE, and
they are deliberately uneven in size - a partition tuned for equal files would have to cut a cluster
that no task cuts.

`StructuresMixin` exists ONLY to preserve settlement/core.py's single import and its position in the
`class Settlement(...)` base list - the split is meant to be invisible above this line. Sub-mixin
methods reach each other through `self.` on the composed Settlement, so a cross-submodule call needs
no import and the partition can be re-cut later without touching core.py. urban.py is the hub: three
of the other six call into it and it calls out to none of them.

The base order below is source order and is behaviorally irrelevant - no name is defined twice, which
is what the composed-surface guard's second assertion exists to keep true.
"""

from .captions import CaptionProbesMixin
from .compounds import CompoundsMixin
from .fixtures import PublicFixturesMixin
from .ground import GroundMixin
from .packing import PackingMixin
from .servants import ServantRangesMixin
from .urban import UrbanBuildingMixin


class StructuresMixin(
    CompoundsMixin,
    GroundMixin,
    UrbanBuildingMixin,
    ServantRangesMixin,
    PackingMixin,
    CaptionProbesMixin,
    PublicFixturesMixin,
):
    """The composed structures surface. No members of its own by design - see the module docstring."""
'''
    (PKG / "__init__.py").write_text(init)
    print(f"wrote {PKG / '__init__.py'}")
    print("\nPRUNE the copied headers next:")
    print("  python3 -m ruff check --select F401 --fix settlement/structures/")
    print("  python3 -m ruff format settlement/structures/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

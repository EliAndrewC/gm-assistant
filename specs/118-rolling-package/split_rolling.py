#!/usr/bin/env python3
"""Feature 118's one-shot transformer: settlement/rolling.py -> settlement/rolling/.

Adapted from feature 116's split_shrines_wells.py, which came from 114's split_structures.py, 113's
split_city.py, 112's split_fields.py and 025's split_settlement.py. The lineage matters because the
SLICING RULE is the part worth preserving, and it is the part a fresh implementation gets wrong.

Run once from .claude/skills/diagram/:

    python3 ../../../specs/118-rolling-package/split_rolling.py

then prune the copied import headers with ruff (see PRUNE below) and delete the old file.

WHY the blocks are sliced as (previous node's end + 1 .. this node's end) rather than by the node's
own lineno: that span carries the DECORATOR lines (ast reports FunctionDef.lineno at the `def`, not
at the decorator above it), the blank lines, and any comment block written above the member. Slicing
by node.lineno silently drops all three.

Both hazards are live in THIS file:

  - `@staticmethod` sits on `_bbox_of` and `_closest_on_seg`. Lose it and the name still exists, the
    package still imports, mypy --strict still passes - and every call site passes `self` as the
    first positional argument, so `_bbox_of(rects)` silently measures the Settlement instead.
  - This class is comment-heavy, and in this project a comment above (or inside) a method is usually
    researched grounding: roll_village's bundle-pitch post-mortem, the windbreak "measured off the
    houses" correction, _kura_side's draw-time-decision block, _sun_corridor_ok's 38N shadow-length
    research. A "pure move" that drops a why-comment is not pure, which is why the quickstart counts
    comment lines rather than trusting this docstring.

This file also carries the ONE class-level Assign in the lineage so far - `_NUC_SIDES` - so the
Assign branch of member_name() fires here for the first time since 112.
"""

import ast
import pathlib
import sys

SRC = pathlib.Path("settlement/rolling.py")
PKG = pathlib.Path("settlement/rolling")

# The partition, per specs/118-rolling-package/data-model.md. Keys are class-body member names in
# SOURCE order within each module. The axis is the CHAIN's links - roll, seed, shape, test, place,
# draw - because unlike structures.py and civic_grounds.py this file was never a residue bucket
# (research R1).
MODULES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "roll": (
        "RollVillageMixin",
        "Roll a whole gate-passing settlement from the seed: the knobs, the field, the cluster band, the civic features.",
        ("roll_village",),
    ),
    "seeds": (
        "SeedFormsMixin",
        "Where the candidate house seats COME FROM - the settlement-form seed generators and the perimeter ring.",
        # _perim_bbox/_perim_poly answer the same question the three *_seeds members answer, and
        # `ring` is their consumer the way roll_village is cluster_seeds' (research R1).
        ("line_seeds", "scatter_seeds", "waterfront_seeds", "_perim_bbox", "_perim_poly", "ring"),
    ),
    "bundle": (
        "BundleGeomMixin",
        "What a homestead BUNDLE is: house, threshing yard, dooryard garden beds, kura, grove arms. Pure geometry - it places nothing and draws nothing.",
        ("_bbox_of", "_garden_beds", "_bundle_geom"),
    ),
    "fit": (
        "BundleFitMixin",
        "May a bundle STAND here? Every keep-out and clearance predicate, plus the two spatial caches that make asking cheap.",
        (
            "_field_adjacent",
            "_rect_corners",
            "_poly_bboxes",
            "_rect_hits",
            "_water_obstacles",
            "_rect_on_water",
            "_rect_blocked",
            "_bundle_fits",
            "_sun_corridor_ok",
            "sun_corridor",
            "_bundle_common_fits",
            "_bundle_side_fits",
            "_yard_sun_conflict",
            "_garden_shaded",
            "_fits_any_side",
        ),
    ),
    "place": (
        "PlacerMixin",
        "FIND a spot and commit to it: the spiral searches, the two compaction slides, the nucleated garden-side choice, the legacy per-house solver.",
        # _NUC_SIDES stays with _place_bundle_nucleated, the member it exists for; _fits_any_side
        # over in fit.py reads it through self. (research R4). `headman` is here rather than in
        # bundle.py because its body is a try_place call - a placement entry point, not a geometry
        # definition.
        (
            "headman",
            "_closest_on_seg",
            "_nearest_field_point",
            "_nearest_placed_point",
            "_slide",
            "_place_bundle",
            "_NUC_SIDES",
            "_field_dist",
            "_slide_nuc",
            "_place_bundle_nucleated",
            "_solve_homestead",
        ),
    ),
    "farmsteads": (
        "FarmsteadFlushMixin",
        "The deferred farmstead flush: what actually gets DRAWN, and in what order. This is the module the DRAW ORDER contract is about.",
        ("farmsteads", "_farmsteads_bundle", "_east_trees", "_garden_beds_clear", "_relax_gardens_south", "_kura_side", "_farmsteads_legacy"),
    ),
}

# Section-divider comments describing the OLD file's layout, which would be actively misleading once
# the sections live in different files. rolling.py has NONE - its `# ---` banners all sit INSIDE
# roll_village's body, where they mark that function's phases and are the very structure feature
# 118's decomposition follows (data-model.md Part 2), so they must survive the move untouched. The
# hook is kept because every predecessor needed it.
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
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "RollingMixin")

    # The parent header: everything above `class RollingMixin:`. Copied wholesale into each module
    # and pruned by ruff afterwards (PRUNE below) - which reaches the same end state as computing
    # each module's used names by hand, without this script having to model name resolution.
    header = "".join(lines[: cls.lineno - 1])
    header = header.replace("from ._geom import", "from .._geom import")
    header = header.replace("from ._knobs import", "from .._knobs import")
    header = header.replace("from .core import Settlement", "from ..core import Settlement")
    header = header.replace('"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""\n', "")

    # Slice every class-body member into a block that carries its decorators, its blank lines and any
    # comment written above it.
    blocks: dict[str, str] = {}
    cursor = cls.lineno  # 1-based line of `class RollingMixin:`; body text starts on the next line
    for node in cls.body:
        name = member_name(node)
        text = "".join(lines[cursor : node.end_lineno])
        # The same one-dot -> two-dot rewrite the header gets, applied to the BODY as well. 113 found
        # a LAZY in-body `from .core import Settlement` which, left alone, silently resolves to a
        # module that does not exist. rolling.py's one in-body import is `from waterfields import
        # build_comb`, which is absolute and unaffected; the rewrite is free insurance.
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
        out = f'"""{doc}\n\nSplit from settlement/rolling.py by feature 118 - see settlement/rolling/CLAUDE.md for the index.\n"""\n\n{header}\nclass {mixin}:\n{"".join(body)}'
        (PKG / f"{mod}.py").write_text(out)
        print(f"wrote {PKG / mod}.py  ({len(out.splitlines())} lines, {len(names)} members)")

    init = '''"""The rolling / homestead-solver subsystem of the Mode B settlement engine.

Split from the 1,197-line settlement/rolling.py by feature 118 (constitution Principle X clause 13).
See CLAUDE.md in this directory for which submodule holds what.

Unlike structures/ and civic_grounds/, this package was NEVER a residue bucket. It is one cohesive
CHAIN - roll a village from a seed, generate candidate seats, shape a homestead bundle, test whether
it fits, find it a spot, draw it - and the six submodules are its links, in that order. The test of
the partition is that real tasks stay inside one link: adding a settlement form reads seeds.py alone,
the standing rotated-footprint debt lands in fit.py alone, changing what the flush draws is
farmsteads.py alone.

`RollingMixin` exists ONLY to preserve settlement/core.py's single import and its position in the
`class Settlement(...)` base list - the split is meant to be invisible above this line. Sub-mixin
methods reach each other through `self.` on the composed Settlement, so a cross-submodule call needs
no import and the partition can be re-cut later without touching core.py. fit.py is the hub: place.py
and roll.py call into it, and it calls out only to bundle.py.

The base order below is source order and is behaviorally irrelevant - no name is defined twice, which
is what the composed-surface guard's second assertion exists to keep true.
"""

from .bundle import BundleGeomMixin
from .farmsteads import FarmsteadFlushMixin
from .fit import BundleFitMixin
from .place import PlacerMixin
from .roll import RollVillageMixin
from .seeds import SeedFormsMixin


class RollingMixin(
    RollVillageMixin,
    SeedFormsMixin,
    BundleGeomMixin,
    BundleFitMixin,
    PlacerMixin,
    FarmsteadFlushMixin,
):
    """The composed rolling surface. No members of its own by design - see the module docstring."""
'''
    (PKG / "__init__.py").write_text(init)
    print(f"wrote {PKG / '__init__.py'}")
    print("\nPRUNE the copied headers next:")
    print("  python3 -m ruff check --select F401 --fix settlement/rolling/")
    print("  python3 -m ruff format settlement/rolling/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Feature 112's one-shot transformer: settlement/fields.py -> settlement/fields/ package.

Adapted from feature 025's split_settlement.py. The difference that matters: 025 carved a MODULE
into modules, slicing between top-level statements; this carves a CLASS into sub-mixin classes,
slicing between CLASS-BODY statements. Everything else - the mixin pattern, the TYPE_CHECKING
`self: Settlement` annotation, the "compose in __init__" shape - is the same.

Run once from .claude/skills/diagram/:

    python3 ../../../specs/112-fields-package/split_fields.py

then prune the copied import headers with ruff (see PRUNE below) and delete the old file.

WHY the blocks are sliced as (previous node's end + 1 .. this node's end) rather than by the
node's own lineno: that span carries the decorator lines (@staticmethod sits ABOVE the `def`, and
ast reports FunctionDef.lineno at the `def`), the blank lines, and any comment block written above
the member. Slicing by node.lineno silently drops all three, which is how a "pure move" loses a
researched why-comment.
"""

import ast
import pathlib
import sys

SRC = pathlib.Path("settlement/fields.py")
PKG = pathlib.Path("settlement/fields")

# The partition, per specs/112-fields-package/data-model.md. Keys are class-body member names in
# SOURCE order; the three _PADDY_*_KINDS class constants are named here too - they are the
# feature-012 archetype matrix and belong with the plot features they gate, which the plan's
# method-only table did not list (recorded in research.md R9).
MODULES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "paddy": (
        "PaddyMixin",
        "Wet and dry field bodies, and the plot geometry they quilt themselves from.",
        (
            "paddy_field",
            "_split_convex",
            "_paddy_plots",
            "_taxfree_plots",
            "_paddy_surface",
            "_rows",
            "_fallow_patch",
            "water_field",
            "fallow_field",
        ),
    ),
    "comb": (
        "CombMixin",
        "The comb-field builder, its base fill, its bund junctions, and its furrows.",
        ("comb_base_fill", "bund_junctions", "draw_comb_field", "_draw_furrows"),
    ),
    "landuse": (
        "LandUseMixin",
        "The land-use overlay pass (mulberry-and-fishpond, lotus, hill tea) and its row helpers.",
        ("apply_land_use", "_mulberry_rows", "_pick_overlay_plots"),
    ),
    "features": (
        "FieldFeaturesMixin",
        "Non-rice features the paddy tiles around (feature 012), and every standing-water glyph.",
        (
            "pond",
            "_PADDY_POND_KINDS",
            "_PADDY_ROCK_KINDS",
            "_PADDY_GRAVE_KINDS",
            "_paddy_features",
            "_plot_center_span",
            "_plot_pond",
            "_plot_rock",
            "_plot_grave_island",
            "_rounded_pond",
            "crescent_pond",
        ),
    ),
}

# Section-divider comments that describe the OLD file's layout and would be actively misleading
# once the sections live in different files. Dropped deliberately; each module's docstring says
# the same thing for its own contents. The feature-012 banner is NOT in this list - it is six
# lines of real grounding documentation (the archetype matrix, the disclosed calibrated liberty),
# so it travels with the code it documents, into features.py.
DROP_BANNERS = ("# ---- fields", "# ---- water")


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
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "FieldsMixin")

    # The parent header: everything above `class FieldsMixin:`. Copied wholesale into each module
    # and pruned by ruff afterwards (PRUNE below) - which reaches the same end state as computing
    # each module's used names by hand, without this script having to model name resolution.
    header = "".join(lines[: cls.lineno - 1])
    header = header.replace("from ._geom import", "from .._geom import")
    header = header.replace("from ._knobs import", "from .._knobs import")
    header = header.replace("from .core import Settlement", "from ..core import Settlement")
    header = header.replace(
        '"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""\n',
        "",
    )

    # Slice every class-body member into a block that carries its decorators, its blank lines and
    # any comment written above it.
    blocks: dict[str, str] = {}
    cursor = cls.lineno  # 1-based line of `class FieldsMixin:`; body text starts on the next line
    for node in cls.body:
        name = member_name(node)
        text = "".join(lines[cursor : node.end_lineno])
        if name is None:
            print(f"REFUSING: unnamed class-body member at line {node.lineno} ({type(node).__name__})", file=sys.stderr)
            return 1
        blocks[name] = text
        cursor = node.end_lineno

    assigned = [n for _, _, names in MODULES.values() for n in names]
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
        out = f'"""{doc}\n\nSplit from settlement/fields.py by feature 112 - see settlement/fields/CLAUDE.md for the index.\n"""\n\n{header}\nclass {mixin}:\n{"".join(body)}'
        (PKG / f"{mod}.py").write_text(out)
        print(f"wrote {PKG / mod}.py  ({len(out.splitlines())} lines, {len(names)} members)")

    init = '''"""The field subsystem of the Mode B settlement engine.

Split from the 1,511-line settlement/fields.py by feature 112 (constitution Principle X clause 13).
See CLAUDE.md in this directory for which submodule holds what.

`FieldsMixin` exists ONLY to preserve settlement/core.py's single import and its position in the
`class Settlement(...)` base list - the split is meant to be invisible above this line. Sub-mixin
methods reach each other through `self.` on the composed Settlement, so a cross-submodule call
needs no import and the partition can be re-cut later without touching core.py.
"""

from .comb import CombMixin
from .features import FieldFeaturesMixin
from .landuse import LandUseMixin
from .paddy import PaddyMixin


class FieldsMixin(PaddyMixin, CombMixin, LandUseMixin, FieldFeaturesMixin):
    """The composed field surface. No members of its own by design - see the module docstring."""
'''
    (PKG / "__init__.py").write_text(init)
    print(f"wrote {PKG / '__init__.py'}")
    print("\nPRUNE the copied headers next:")
    print("  python3 -m ruff check --select F401 --fix settlement/fields/")
    print("  python3 -m ruff format settlement/fields/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

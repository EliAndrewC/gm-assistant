#!/usr/bin/env python3
"""Feature 113's one-shot transformer: settlement/city.py -> settlement/city/ package.

Adapted from feature 112's split_fields.py, which was itself adapted from feature 025's
split_settlement.py. The lineage matters because the slicing rule is the part worth preserving,
and it is the part a fresh implementation gets wrong.

Run once from .claude/skills/diagram/:

    python3 ../../../specs/113-city-package/split_city.py

then prune the copied import headers with ruff (see PRUNE below) and delete the old file.

WHY the blocks are sliced as (previous node's end + 1 .. this node's end) rather than by the node's
own lineno: that span carries the decorator lines (@staticmethod sits ABOVE the `def`, and ast
reports FunctionDef.lineno at the `def`), the blank lines, and any comment block written above the
member. Slicing by node.lineno silently drops all three - and in this project the third is the real
loss, because a comment above a method is usually researched grounding. A "pure move" that drops a
why-comment is not pure.
"""

import ast
import pathlib
import sys

SRC = pathlib.Path("settlement/city.py")
PKG = pathlib.Path("settlement/city")

# The partition, per specs/113-city-package/data-model.md. Keys are class-body member names in
# SOURCE order. Every member of CityMixin is a FunctionDef - the class carries no class-level
# constants, unlike 112's FieldsMixin with its _PADDY_*_KINDS matrices - so the Assign branch in
# member_name() below is retained for lineage but will not fire here.
MODULES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "walls": (
        "WallsMixin",
        "The city's defensive shell: the wall, its towers and walk, and the patrol road inside it.",
        (
            "_gapped_ring",
            "ring_road",
            "_tower",
            "_wall_walk",
            "_wall_perimeter",
            "_wall_point_at_arc",
            "_wall_arc_of",
            "city_wall",
        ),
    ),
    "moat": (
        "MoatMixin",
        "The wet defense and every opening through it - water gates, sluices, the inwall drain.",
        ("moat", "water_gate", "sluice_gate", "inwall_drain_outfall", "moat_flow"),
    ),
    "canals": (
        "CanalsMixin",
        "Water carried for transport and irrigation rather than defense, and the farmland ring it feeds.",
        # _ring_upslope reads like a ring_road helper and is NOT one: its only caller is
        # farmland_ring, so placement follows the caller (data-model.md, research R1).
        ("canal", "towpath", "_ring_upslope", "farmland_ring"),
    ),
    "waterfront": (
        "WaterfrontMixin",
        "Where the city meets navigable water: quay, aqueduct, docks, jetties, the log boom.",
        ("quay", "aqueduct", "dock", "jetty", "log_boom"),
    ),
    "bridges": (
        "BridgesMixin",
        "Crossings, from a single span to the footbridge net over a channel system.",
        ("bridge", "bridges", "channel_footbridges", "_plank_reaches_useful_ground"),
    ),
    "civic": (
        "CityCivicMixin",
        "The one civic BUILDING the city tier draws.",
        # A one-method module on purpose. governor_mansion calls self.manor() and re-keys the
        # record out of M["manors"] - it is a structure reusing the manor glyph, not city
        # infrastructure, so it belongs to none of the five subsystems above. Isolating it keeps
        # every other module's index row honest and makes the intended follow-up (folding it into
        # settlement/castle_civic.py) a one-file change. Full reasoning: research.md R1.
        ("governor_mansion",),
    ),
}

# Section-divider comments that describe the OLD file's layout and would be actively misleading
# once the sections live in different files. This one sits at the top of the class body, above
# _gapped_ring, and describes the whole class - at the top of walls.py it would claim the file
# holds every provincial-city feature. Dropped deliberately; each module's docstring says the same
# thing for its own contents.
DROP_BANNERS = ('# ---- provincial-city features (scale="city")',)


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
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "CityMixin")

    # The parent header: everything above `class CityMixin:`. Copied wholesale into each module and
    # pruned by ruff afterwards (PRUNE below) - which reaches the same end state as computing each
    # module's used names by hand, without this script having to model name resolution.
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
    cursor = cls.lineno  # 1-based line of `class CityMixin:`; body text starts on the next line
    for node in cls.body:
        name = member_name(node)
        text = "".join(lines[cursor : node.end_lineno])
        # The same one-dot -> two-dot rewrite the header gets, applied to the BODY as well.
        # Feature 112 only rewrote the header, because none of its methods had an in-body import.
        # city.py has one: _wall_point_at_arc does a LAZY `from .core import Settlement` inside its
        # body (a runtime class-attribute read that would cycle at module level). Left alone it
        # keeps the one-dot path and silently resolves to `settlement.city.core`, which does not
        # exist - caught here by mypy, but it would have been an ImportError at draw time in a
        # module mypy did not check. Any future split inherits this line, so keep it.
        text = text.replace("from .core import", "from ..core import")
        text = text.replace("from ._geom import", "from .._geom import")
        text = text.replace("from ._knobs import", "from .._knobs import")
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
        out = f'"""{doc}\n\nSplit from settlement/city.py by feature 113 - see settlement/city/CLAUDE.md for the index.\n"""\n\n{header}\nclass {mixin}:\n{"".join(body)}'
        (PKG / f"{mod}.py").write_text(out)
        print(f"wrote {PKG / mod}.py  ({len(out.splitlines())} lines, {len(names)} members)")

    init = '''"""The provincial-city subsystem of the Mode B settlement engine.

Split from the 1,582-line settlement/city.py by feature 113 (constitution Principle X clause 13).
See CLAUDE.md in this directory for which submodule holds what.

`CityMixin` exists ONLY to preserve settlement/core.py's single import and its position in the
`class Settlement(...)` base list - the split is meant to be invisible above this line. Sub-mixin
methods reach each other through `self.` on the composed Settlement, so a cross-submodule call
needs no import and the partition can be re-cut later without touching core.py. There is exactly
one such call today: farmland_ring (canals) -> sluice_gate (moat).

The base order below is source order and is behaviorally irrelevant - no name is defined twice,
which is what the composed-surface guard's second assertion exists to keep true.
"""

from .bridges import BridgesMixin
from .canals import CanalsMixin
from .civic import CityCivicMixin
from .moat import MoatMixin
from .walls import WallsMixin
from .waterfront import WaterfrontMixin


class CityMixin(WallsMixin, MoatMixin, CanalsMixin, WaterfrontMixin, BridgesMixin, CityCivicMixin):
    """The composed city surface. No members of its own by design - see the module docstring."""
'''
    (PKG / "__init__.py").write_text(init)
    print(f"wrote {PKG / '__init__.py'}")
    print("\nPRUNE the copied headers next:")
    print("  python3 -m ruff check --select F401 --fix settlement/city/")
    print("  python3 -m ruff format settlement/city/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

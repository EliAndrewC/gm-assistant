"""Feature 110: guard + surface-pin tests for the waterfields package namespace.

The package __init__ re-exports its submodules' public names via star imports
(specs/110-waterfields-package/, the 027 mechanism). Three properties keep that
safe, and this file holds all of them:

1. No two submodules may bind the same public name to different objects -
   star-import shadowing is silent (last import wins). test_no_public_name_clashes
   holds the line; test_guard_fires_on_synthetic_clash proves the guard has teeth.
2. The consumed surface - every name reached through waterfields anywhere in the
   skill tree (contracts/package-surface.md census) - must keep resolving,
   including the underscore names the aliased explicit block carries.
3. The census itself is re-run mechanically (AST over the tree), so a consumer
   added by a later session fails here loudly instead of breaking at import time.

The submodule-shaped tests skip while waterfields is still the monolith (they
activate the moment it becomes a package), so this file is green before, during,
and after the split.
"""

import ast
import importlib
import os
import pkgutil
import types

import pytest

from l7r.diagram import waterfields

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # the skill root


def _is_package() -> bool:
    return hasattr(waterfields, "__path__")


def _submodules() -> list[types.ModuleType]:
    return [importlib.import_module(f"l7r.diagram.waterfields.{info.name}") for info in pkgutil.iter_modules(waterfields.__path__)]


def _public_clashes(modules: list[types.ModuleType]) -> list[tuple[str, str, str]]:
    """Every (name, first_module, offending_module) where a public name is bound to two different objects."""
    seen: dict[str, tuple[str, object]] = {}
    clashes: list[tuple[str, str, str]] = []
    for mod in modules:
        for name, obj in vars(mod).items():
            if name.startswith("_"):
                continue
            if name in seen:
                if seen[name][1] is not obj:
                    clashes.append((name, seen[name][0], mod.__name__))
            else:
                seen[name] = (mod.__name__, obj)
    return clashes


# The public names consumed as waterfields.<name> across the skill tree
# (contracts/package-surface.md census, re-taken 2026-08-16 at implement time).
CONSUMED_PUBLIC = [
    "jog_vertices",
    "AZE",
    "BANK_MARGIN",
    "BEAN_GREEN",
    "BUND",
    "DRAIN_FT",
    "DRY_CROPS",
    "FLOODED",
    "PADDY_CELL_ACRES",
    "aze_w",
    "build_comb",
    "build_polder",
    "build_ribbon",
    "build_terraces",
    "chan_px",
    "dedup_ring",
    "drain_bank_clearance",
    "floor_overhang",
    "hem_on_paddy",
    "paddy_grain",
    "pointed_ring",
    "polyline_cum",
    "round_channel_joints",
    "supply_bank_clearance",
    "taper_pieces",
    "taper_w",
    "worth_planking",
]

# The underscore names with external consumers, and the submodule that owns each
# (settlement/fields/: _RICE_GREEN; tests/hamletgen/: _Frame, _miter_normals;
# tests/settlement/test_core.py: _bund_beans, _seg_d).
ALIASED_UNDERSCORE = {
    "_Frame": "l7r.diagram.waterfields.frame",
    "_RICE_GREEN": "l7r.diagram.waterfields.palette",
    "_bund_beans": "l7r.diagram.waterfields.carve",
    "_miter_normals": "l7r.diagram.waterfields.frame",
    "_seg_d": "l7r.diagram.waterfields.frame",
}


def _census() -> set[str]:
    """Every name the skill tree actually reaches through waterfields, by AST.

    Covers both `from waterfields import a, b` and attribute access through any
    `import waterfields [as alias]` binding. Skips the package's own files.
    """
    names: set[str] = set()
    skip_dirs = {"__pycache__", ".git", "waterfields"}
    for root, dirs, files in os.walk(HERE):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
        for fn in files:
            if not fn.endswith(".py") or fn == "waterfields.py":
                continue
            path = os.path.join(root, fn)
            with open(path) as fh:
                src = fh.read()
            try:
                tree = ast.parse(src)
            except SyntaxError:  # a scratch or wip file that does not parse is not a consumer
                continue
            aliases: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "l7r.diagram.waterfields":
                    names.update(a.name for a in node.names)
                elif isinstance(node, ast.Import):
                    aliases.update(a.asname or a.name for a in node.names if a.name == "l7r.diagram.waterfields")
            if aliases:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases and not node.attr.startswith("__"):
                        names.add(node.attr)
    return names


def test_no_public_name_clashes() -> None:
    if not _is_package():
        pytest.skip("waterfields is still the monolith - activates after the 110 split")
    clashes = _public_clashes(_submodules())
    assert not clashes, f"star-import shadowing - same public name, different objects: {clashes}"


def test_guard_fires_on_synthetic_clash() -> None:
    first = types.ModuleType("waterfields.fake_first")
    second = types.ModuleType("waterfields.fake_second")
    first.same_name = object()  # type: ignore[attr-defined]
    second.same_name = object()  # type: ignore[attr-defined]
    assert _public_clashes([first, second]) == [("same_name", "waterfields.fake_first", "waterfields.fake_second")]


@pytest.mark.parametrize("name", CONSUMED_PUBLIC)
def test_consumed_surface_resolves(name: str) -> None:
    getattr(waterfields, name)


@pytest.mark.parametrize(("name", "owner"), sorted(ALIASED_UNDERSCORE.items()))
def test_aliased_underscore_reexport_is_identical(name: str, owner: str) -> None:
    if not _is_package():
        assert getattr(waterfields, name) is not None  # monolith: the name at least exists
        return
    assert getattr(waterfields, name) is getattr(importlib.import_module(owner), name)


def test_census_covers_every_real_consumer() -> None:
    """The mechanical census: every name any file reaches through waterfields resolves,
    and every censused name is pinned above (so the pinned lists cannot go stale)."""
    found = _census()
    missing = sorted(n for n in found if not hasattr(waterfields, n))
    assert not missing, f"consumed through waterfields but not resolvable: {missing}"
    pinned = set(CONSUMED_PUBLIC) | set(ALIASED_UNDERSCORE)
    unpinned = sorted(found - pinned)
    assert not unpinned, f"consumed in the tree but not pinned in this file's census lists: {unpinned}"

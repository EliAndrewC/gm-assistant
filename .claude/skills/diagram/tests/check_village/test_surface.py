"""Feature 027: guard + surface-pin tests for the check_village package namespace.

The package __init__ re-exports its submodules' public names via star imports
(specs/027-init-star-imports/). Two properties keep that safe, and this file
holds both lines:

1. No two submodules may bind the same public name to different objects -
   star-import shadowing is silent (last import wins), so a clash would swallow
   a check or helper without any error. test_no_public_name_clashes holds the
   line; test_guard_fires_on_synthetic_clash proves the guard has teeth
   (check-before-fix: a checker never seen failing is not a check).
2. The consumed surface - every name reached through check_village anywhere in
   the repo at feature time (specs/027-init-star-imports/census.md) - must keep
   resolving, including the six underscore names the aliased explicit block
   carries.
"""

import importlib
import pkgutil
import types

import pytest

import check_village


def _submodules() -> list[types.ModuleType]:
    return [importlib.import_module(f"check_village.{info.name}") for info in pkgutil.iter_modules(check_village.__path__) if info.name != "__main__"]


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


# The 38 public names consumed as check_village.<name> (census.md, 2026-08-16).
CONSUMED_PUBLIC = [
    "BUDGET_TOL_OVER",
    "BUDGET_TOL_UNDER",
    "GATE_SEGMENTS",
    "HOUSEHOLD",
    "META_CHECKS",
    "OVERLAP_CLASS",
    "QUARTER_DENSITY_CEIL",
    "QUARTER_DENSITY_FLOOR",
    "RESERVE_CAP_FRAC",
    "TWIN_AXES",
    "city_capacity",
    "clip_poly_rect",
    "crop_relocatable_singletons",
    "edge_gap",
    "forest_reveal_x",
    "gate",
    "kiln_quarters",
    "lane_near_misses",
    "lane_ward_shortfalls",
    "largest_empty_gap",
    "main",
    "matrix_extents",
    "matrix_policy",
    "matrix_violations",
    "onmap_field_edge",
    "point_in_poly",
    "poly_area",
    "poly_dist",
    "poly_gap",
    "rect_corners",
    "seg_dist",
    "seg_intersect",
    "seg_to_rect_dist",
    "sweep_hi",
    "twin_axes",
    "twin_diff_count",
    "twin_report",
    "water_setback",
]

# The six underscore names with external consumers, and the submodule that owns each.
ALIASED_UNDERSCORE = {
    "_LABEL_EXEMPT": "check_village.common_01_geometry",
    "_LABEL_GROUP": "check_village.common_01_geometry",
    "_MATRIX_OUTSTANDING": "check_village.common_01_geometry",
    "_OVERLAP_EXEMPT": "check_village.common_01_geometry",
    "_OVERLAP_STRUCTS": "check_village.common_01_geometry",
    "_ward_interior": "check_village.common_02_overlap_policy",
}


def test_no_public_name_clashes() -> None:
    clashes = _public_clashes(_submodules())
    assert not clashes, f"star-import shadowing - same public name, different objects: {clashes}"


def test_guard_fires_on_synthetic_clash() -> None:
    first = types.ModuleType("check_village.fake_first")
    second = types.ModuleType("check_village.fake_second")
    first.same_name = object()  # type: ignore[attr-defined]
    second.same_name = object()  # type: ignore[attr-defined]
    assert _public_clashes([first, second]) == [("same_name", "check_village.fake_first", "check_village.fake_second")]


@pytest.mark.parametrize("name", CONSUMED_PUBLIC)
def test_consumed_surface_resolves(name: str) -> None:
    getattr(check_village, name)


@pytest.mark.parametrize(("name", "owner"), sorted(ALIASED_UNDERSCORE.items()))
def test_aliased_underscore_reexport_is_identical(name: str, owner: str) -> None:
    assert getattr(check_village, name) is getattr(importlib.import_module(owner), name)

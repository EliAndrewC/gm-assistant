"""CLI entry: python3 -m l7r.diagram.check_village <manifest.json> [--capacity [--capacity-map]]."""

if __name__ == "__main__":
    import os
    import sys

    from l7r.diagram.check_village import QUARTER_DENSITY_CEIL, QUARTER_DENSITY_FLOOR, RESERVE_CAP_FRAC, city_capacity, main

    here = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
    )  # the skill root: __file__ moved one level down into the package (024) and two more under l7r/diagram/ (119)
    default = os.path.join(here, "pool", "villages", "kikuta.json")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else default
    if "--capacity" in sys.argv[1:]:
        import json as _json

        want_map = "--capacity-map" in sys.argv[1:]
        with open(path) as _cf:
            rep = city_capacity(_json.load(_cf), grid_step=40 if want_map else None)
        if rep is None:
            print("no capacity report (not a walled city with a declared population)")
        else:
            _action = {"sized_and_packed": "sized and packed - done", "densify": "add dwellings (wall is right)", "enlarge": "ENLARGE the wall", "shrink": "SHRINK the wall"}
            print(f"WALL CAPACITY: {rep['verdict'].upper()} -> {_action.get(rep['verdict'], '')}")
            print(f"  target {rep['target_dwellings']} dwellings, placed IN-WALL {rep['placed']}, INHERENT capacity (well-packed) {rep['inherent_capacity']}")
            print(
                f"  ring {rep['ring_area']}px^2: residential-capable {rep['res_capable_area']}, civic {rep['civic_area']}, reserve {rep['reserve_area']} (reserve frac {rep['reserve_frac']}, cap {RESERVE_CAP_FRAC})"
            )
            print(f"  suggested wall scale x{rep['suggested_wall_scale']} (>1 enlarge, <1 shrink)")
            for pq in rep.get("per_quarter", []):
                _band = "" if QUARTER_DENSITY_FLOOR <= pq["density"] <= QUARTER_DENSITY_CEIL else "  <-- OUT OF BAND"
                print(f"  quarter {str(pq['name']):>22} [{pq['zone']:11}] {pq['dwellings']:3d} dwellings, density {pq['density'] * 1000:.2f}/1000px^2{_band}")
            if rep.get("grid"):
                ox, oy = rep["grid_origin"]
                print(f"  interior map (D dwell / C civic / ~ water / # trunk / + res-street / F field / . OPEN); each cell {rep['grid_step']}px, origin ({ox},{oy}):")
                for j, row in enumerate(rep["grid"]):
                    print(f"    {oy + j * rep['grid_step']:>5} {row}")
        sys.exit(0)
    sys.exit(main(path))

"""Feature 122: drive `split_segments.split_apply` over all 13 segment files.

The cut POINTS come from `split_segments.propose` (balanced at segment boundaries, ~850 lines
a part) rather than being hand-typed, so no segment name is transcribed by hand and a cut can
never land mid-function. This file supplies only the theme SLUGS, read off the check names in
each proposed part.

The three `segments_10_city_battery_*` files are one contiguous key range (0563_000-0563_376)
that an earlier split cut into three for size alone, so their eight parts take one lettered run
`10a..10h` - restoring in the file names what the key range always said.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from split_segments import PKG, propose, split_apply  # noqa: E402

SLUGS: dict[str, list[str]] = {
    "segments_01_city_frame_and_yards": [
        "01a_city_ring_and_frame",
        "01b_quarters_and_civic_reserve",
        "01c_work_yards_and_matrix",
    ],
    "segments_02_capital_and_walls": [
        "02a_capital_budget_and_ministries",
        "02b_capital_ways_and_burial",
        "02c_walls_gates_and_housing",
    ],
    "segments_03_structures_and_wards": [
        "03a_overlaps_and_ward_fences",
        "03b_structures_vs_water_and_streets",
        "03c_clusters_and_labels",
    ],
    "segments_04_homesteads": [
        "04a_margins_lanes_and_wells",
        "04b_yards_gardens_and_sheds",
        "04c_groves_and_shading",
    ],
    "segments_05_fields_and_funerary": [
        "05a_field_cover_and_cremation",
        "05b_graveyards_and_channel_sources",
        "05c_streams_and_field_ditches",
        "05d_supply_roadways_and_commons",
    ],
    "segments_06_ways_and_bridges": [
        "06a_bridges_and_gate_roads",
        "06b_bridge_labels_and_reach",
        "06c_decks_yards_and_moat_clearances",
    ],
    "segments_07_water": [
        "07a_channels_and_bridge_spans",
        "07b_ponds_hems_and_land_fall",
        "07c_moats_drains_and_edges",
    ],
    "segments_08_town_and_fire": [
        "08a_ponds_marshes_and_drainage",
        "08b_flow_bands_and_the_burakumin_seam",
        "08c_town_trades_and_theater",
        "08d_kosatsuba_and_paddy_basins",
    ],
    "segments_09_justice_and_tanning": [
        "09a_justice_grounds_and_land_fall",
        "09b_tanning_yards",
    ],
    "segments_10_city_battery_a": [
        "10a_city_castes_and_dojos",
        "10b_city_civic_and_commerce",
        "10c_city_gates_and_wall_towers",
    ],
    "segments_10_city_battery_b": [
        "10d_city_temples_and_estates",
        "10e_city_governor_and_quarters",
    ],
    "segments_10_city_battery_c": [
        "10f_city_labels_and_works",
        "10g_city_streets_and_docks",
        "10h_city_torii_and_estate_grounds",
    ],
    "segments_11_polders_and_edges": [
        "11a_taxfree_terraces_and_dikeponds",
        "11b_polder_dikes_and_waivers",
    ],
}

# The GM's stated order: 05 first, then 08, then the rest by descending size.
ORDER = [
    "segments_05_fields_and_funerary",
    "segments_08_town_and_fire",
    "segments_01_city_frame_and_yards",
    "segments_03_structures_and_wards",
    "segments_04_homesteads",
    "segments_02_capital_and_walls",
    "segments_07_water",
    "segments_06_ways_and_bridges",
    "segments_10_city_battery_c",
    "segments_10_city_battery_a",
    "segments_10_city_battery_b",
    "segments_09_justice_and_tanning",
    "segments_11_polders_and_edges",
]


def main() -> int:
    assert sorted(ORDER) == sorted(SLUGS), "ORDER and SLUGS disagree"
    written: list[pathlib.Path] = []
    for stem in ORDER:
        path = PKG / f"{stem}.py"
        if not path.exists():
            print(f"SKIP {stem} (already split)")
            continue
        cuts = propose(path)
        slugs = SLUGS[stem]
        if len(cuts) != len(slugs):
            raise SystemExit(f"{stem}: propose() wants {len(cuts)} parts, {len(slugs)} slugs given")
        print(f"\n{stem}.py ({len(path.read_text().splitlines())} lines)")
        written += split_apply(path, [(f"segments_{s}", c[0]) for s, c in zip(slugs, cuts, strict=True)])
    print(f"\n{len(written)} sub-files written")
    over = [p for p in written if len(p.read_text().splitlines()) > 1000]
    print("over the 1,000-line bar:", [p.name for p in over] or "NONE")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())

# Quickstart: Village Visual Variation Knobs

How a spec author will use the knobs once Phase 1 lands. Illustrative - exact call names are settled during implementation; the behavior is fixed by `contracts/knob-interface.md`.

## Roll a distinct village from a minimal spec

Supply only the geography + seed; let every layout knob roll independently:

```python
s = Settlement(W=2400, H=1560, seed=53)
s.meta(name="Some Village", scale="village", ftpx=2, down_deg=45,
       water_source="pond", region="rice_valley")   # no cluster/lane/water/focal coordinates
# ... the water-first field is built, then the cluster/lanes/headman/shrine/focal features
#     are all resolved by independent seeded rolls under their historical-typing rules
```

Change only the seed and you get a different but historically-coherent village (different cluster position + shape, lane skeleton, water-source corner, plot grain, focal-feature set). Two such villages with the same `down_deg` differ on >= 4 structural axes (SC-001) and pass the twin-detector.

## Pin the knobs you care about, roll the rest

```python
s.meta(name="Designed Village", scale="village", ftpx=2, down_deg=90,
       water_source="stream",
       cluster_shape="crescent",          # pinned: a crescent hugging the field
       lane_skeleton="waterside",         # pinned: lanes follow the stream
       focal_features=["ancestral_hall"], # pinned: a single-lineage village with its hall
       )                                  # cluster_position, water entry edge, plot_texture, grain roll from the seed
```

Pinned values are honored exactly and are deterministic across regenerations. An incompatible pin (e.g. `focal_features=["mulberry_fishpond"]` in a dry upland) is rejected/warned, not drawn.

## Verify

```sh
python3 pool/<name>.gen.py                 # writes .svg / .json / .png
python3 check_village.py pool/<name>.json  # per-map gate -> ALL CHECKS PASSED
python3 -m pytest                          # full suite incl. test_villages + the twin-detector, 100% coverage
```

Then read the rendered PNG (author self-review) and confirm the twin-detector reports no twinned same-`down_deg` pair.

## Re-varying Kikuta / Hoshigaoka (this feature's MVP demonstration)

Both are regenerated through the knobs to sit on different cluster positions, with different lane skeletons, headman placement, water-source corners, plot grain, and focal-feature sets - so they stop reading as copies while both keep passing the gate. This is the SC-001 / SC-002 acceptance demonstration.

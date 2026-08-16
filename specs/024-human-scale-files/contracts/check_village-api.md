# Contract: check_village public surface (must survive the package split)

## Import surface (consumers: test_checks, test_villages, test_regressions, test_citybudget,
## test_settlement, cohort_audit, site_justice, make_regressions, hamletgen, oracle_sweep)

- `import check_village` exposes EVERY name the monolith exposed at module level - public and
  underscore - via `check_village/__init__.py` re-exports. Attribute access like
  `check_village.city_capacity`, `check_village.OVERLAP_CLASS`, `check_village._MATRIX_ALLOWED_KEYS`
  keeps working unchanged.
- `from check_village import gate, load` keeps working (hamletgen, cohort_audit).

## Behavioral contract

- `gate(M, verbose=True)` - byte-identical stdout and identical returned verdict list per
  manifest vs the pre-feature monolith (oracle-hash proof, all 797 fixtures + pool manifests).
- `gate(M, only={names})` - same closure semantics: segments emitting the names + dependency
  closure; unknown names and META names raise ValueError; restricted verdicts identical to the
  full run's for those names (oracle `targeted` proof).
- `GATE_SEGMENTS` order unchanged where segments were not split; split segments replaced in
  place by their per-check rows in statement order.
- Import-time guard `_assert_not_main_tree` still fires on package import from main's tree.

## CLI

- OLD: `python3 check_village.py <manifest.json> [...]`
- NEW: `python3 -m check_village <manifest.json> [...]` (same flags, same output; every doc
  quoting the old form is updated in this feature).

## Check-name surface

- The SET of emitted check names is unchanged (fixture `_regression.fires` keys, `only=` names,
  and `gate_check_names.json` all key on check names; only SEGMENT names change).

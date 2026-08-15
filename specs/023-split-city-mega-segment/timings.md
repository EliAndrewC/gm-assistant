# Timings and measurements ledger: feature 023

All measured on this container (22 cpus, python 3.14), clone at main tip (`89ebda5` + this
feature's work). "Baseline" = pre-split `check_village.py`.

## Baseline (T001-T003)

| Measurement | Value |
|---|---|
| `import check_village` | 0.13 s |
| Largest functions (AST stmt count) | `_seg_0563__city_has_six_ministries` 1,040; `_seg_0285__wells_clear_of_shrine_and_torii` 427; `_seg_0543__town_farmers_plurality` 161 |
| `gate_check_names.json` sha256 | `1c56c8073870764c51e9b3ce351a3725f72d2e2f5b4a6db2b74a1728a076924d` |
| Oracle baseline capture | `<scratchpad>/oracle-baseline-023.json` (fresh at this tip - NOT the stale 022 capture) |
| Replay wall (`pytest test_regressions.py -n auto`) | (recorded below when the background run lands) |

## Census (T004/T006)

- 377 spans: 82 outer-guard + 295 walled-guard, textual order preserved.
- Statement sizes: median 1, p90 6, max 51. Check-emitting spans: 119; name union == the frozen
  148 exactly. Always-run (opaque names): none. Meta reads: none.
- Stale-cell hazard merges required: **zero** - every nested helper def's free names are stable
  from its definition onward at per-statement granularity.
- Lambda-freeze WARNs: 5, all manually verified consumed in-span (uses confirmed by AST span
  lookup: lines 21649/21664/21704/21762 all in span 21647-21776; 21790-21805 all in span
  21787-21813; two `key=` lambdas and one parameter-shadow false positive at 23130).

## Post-split (T007/T011/T013)

(filled in as tasks complete)

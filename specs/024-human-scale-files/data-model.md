# Data Model: Human-Scale Files (024)

## Package layout (target state)

| module | contents | source lines (monolith) | size bound |
|---|---|---|---|
| `check_village/__init__.py` | generated explicit re-exports, original definition order | n/a | small |
| `check_village/__main__.py` | CLI entry (old `__main__` block via `main()`) | 35566-35602 | small |
| `check_village/common_01_spatial.py` | geometry/spatial helpers, GridIndex, hull/gap math | ~1-1360 (contiguous cut at a def boundary) | ≤ ~1,500 |
| `check_village/common_02_policy.py` | overlap matrix + label taxonomy tables, theater/fire/ward/lane helpers | ~1361-2138 | ≤ ~1,500 |
| `check_village/common_03_capacity.py` | crop/capacity helpers, city_capacity, waiver consts, `_UnboundType`/`_UNBOUND`/`_kept` | ~2139-2630 | ≤ ~1,500 |
| `check_village/segments_NN_<theme>.py` (~10-14 files) | segment functions, contiguous ranges | 2632-28021 | ≤ ~3,000 each |
| `check_village/registry.py` | `_GateSeg`, `GATE_SEGMENTS`, `META_CHECKS`, `_SEG_DEPS` build loop | 28024-35352 | EXCEEDS - inline clause-13 justification (ordered data) |
| `check_village/driver.py` | `gate()`, `_dir8`, twin helpers, `main()` | 35355-35565 | small |
| `check_village/CLAUDE.md` | index: one line per module, "look here when" | new | small |

Exact `common_*` cut lines and segment-file ranges are computed by `split_package.py`'s census
and recorded in the package CLAUDE.md; the invariant is CONTIGUITY (concatenation in file order
reproduces monolith definition order) and every cut lands on a top-level statement boundary.

## Split tooling data shapes

### Segment census row (`split_oversized.py` output, recorded in tasks/commit)

```json
{"seg": "_seg_0285__wells_clear_of_shrine_and_torii", "lines": 1351, "units": 427,
 "checks": 42, "action": "split", "new_segs": ["_seg_0285_000__gardens_present", "..."]}
```

### Oracle baseline (`oracle_sweep.py capture` - unchanged 022 format)

Per fixture/manifest: ordered verdict list + sha256 of verbose stdout. Identity = zero diffs on
`compare`, and `targeted` verdict sets equal to full-run sets.

### `_GateSeg` (UNCHANGED - the contract)

```python
class _GateSeg(NamedTuple):
    fn: Any; free: tuple[str, ...]; writes: tuple[str, ...]
    checks: tuple[str, ...]; needs: tuple[str, ...]; meta: bool; always: bool
```

New per-check segments get rows with: `checks` = the one check name (plus any names the group
still emits together when statements are inseparable), `free`/`writes`/`needs` recomputed by the
same dataflow rules as 022 (`transform_gate.py`), row order = statement order within the old
segment, spliced at the old row's registry position.

### Registry-pin fixture

`test_fixtures/gate_check_names.json` maps the registry's segment names/checks; regenerated after
stage 1 (segment names change; CHECK names do not - fixture `_regression.fires` keys stay valid).

## Import generation rule (`split_package.py`)

For each moved top-level def/assign: free names = AST loads not bound locally, minus params,
builtins, and its own module's definitions; each remaining name imports explicitly from the
module that defines it (always an earlier file by contiguity; `settlement`/`waterfields` imports
stay absolute). Cycles are impossible by construction: imports only point backwards in file
order, except `registry.py` importing segment functions and `driver.py` importing registry -
both strictly forward of their dependencies.

# Data Model: 109-registry-derive

## Entities

### Gate segment (existing, unchanged)
A keyword-only function `_seg_<key>__<slug>` in a `segments_*` module. Carries in its own code
the facts the registry used to restate:
- **signature** (kwonly params) = the row's `free`
- **terminal `return _kept(locals(), (<literal str tuple>))`** = the row's `writes`
- **body AST** = source for `checks` / `needs` / `meta` / `always`
- **name numeric key** = default execution position (`NNNN` or `NNNN_NNN`; sub-number sorts
  after the plain number's -1)

### Registry row `_GateSeg` (existing shape, now derived)
`(fn, free, writes, checks, needs, meta, always)` - NamedTuple unchanged so `driver.py` and any
row-shape assumptions hold. Values produced by derivation, not literals.

### PLACEMENTS (new, decided data)
`dict[str, str]`: segment name -> name-prefix of the segment it runs immediately after. Exactly
2 entries at introduction (`_seg_0595`, `_seg_0596`). Each entry carries an inline why. Validity
rules: key and anchor must name live segments; anchor must not itself be a placed segment;
entries for names the key-sort already orders correctly are dead and fail the liveness guard.

### NEEDS_OVERRIDES (new, decided data)
`dict[str, tuple[str, ...]]`: segment name -> hand-decided `needs` value replacing the derived
one. Exactly 1 entry at introduction (`_seg_0324_500`). Inline why per entry; liveness-guarded;
value must be a subset of the segment's `free`.

### Derivation cache (new, gitignored)
JSON artifact: `{key: <hash of segment sources + derivation version>, rows: [{name, free,
writes, checks, needs, meta, always}, ...], meta_checks: [...]}`. Functions are NOT serialized -
rows re-bind `fn` by name at load. Atomic publish (write-tempfile-rename, per gencache
precedent). A key mismatch or any load error discards it and re-derives.

### Frozen fixture (new, committed, never regenerated)
Same JSON shape as the cache rows, generated from the pre-collapse registry. The transition
oracle: derived rows must equal fixture rows by name; fixture name order must be a subsequence
of derived order. Documents the legacy state permanently.

## Relationships / dataflow

```text
segments_*.py --(module scan)--> roster of fns
  fn signature -----------------> free
  fn return tuple ---------------> writes
  fn body AST + helper fixpoint -> needs (unless NEEDS_OVERRIDES) , checks, meta, always
  fn name key + PLACEMENTS ------> order
rows --> META_CHECKS (union of checks where meta) --> _SEG_DEPS (needs x writes, as today)
cache: (segment sources hash) -> rows           [fast path, skips AST]
fixture: legacy rows                            [test-time oracle only]
```

## Validation rules (enforced at derive time and/or by guard tests)

1. Every `_seg_*` function ends with `return _kept(locals(), <tuple literal of str>)`.
2. No duplicate segment names; no duplicate numeric keys among non-placed segments.
3. PLACEMENTS / NEEDS_OVERRIDES entries reference live segments (stale entry = hard failure).
4. Final order strictly increasing by key once placed segments are removed.
5. `needs` subset-of `free` for every row (including overridden rows).
6. Derived `META_CHECKS` equals union over meta rows.
7. Cache round-trip: loaded rows identical to freshly derived rows (property test).

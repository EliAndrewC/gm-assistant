# Data Model: Split the City Mega-Segment (023)

No persistent data changes. The entities are the transformer's in-memory model and the (already
existing, unchanged in shape) registry row.

## SubSeg (transformer-internal)

One top-level statement lifted out of the mega-segment. Mirrors 022's `Seg`.

| Field | Type | Meaning |
|---|---|---|
| `idx` | int | 0-based position across the concatenated (outer, walled) statement sequence - becomes `NNN` in `_seg_0563_NNN__slug` and the row's registry position offset |
| `node` | ast.stmt | the statement, body emitted VERBATIM from source lines (never unparsed) |
| `guard` | str | `"scale in ('city', 'capital')"` or `"scale in ('city', 'capital') and meta.get('walled')"` |
| `free` | list[str] | loads ∩ gate-local vocabulary (mega free ∪ mega writes), plus mutation targets and helper-mutation closure - wrapper params, `_UNBOUND`-defaulted |
| `writes` | list[str] | stores outside nested defs + mutation targets + helper-transitive mutations - the `_kept` return set |
| `checks` | list[str] | check base names emitted (literal, same-segment-assigned, or via emitting module helpers) |
| `needs` | list[str] | upward-exposed reads of the GUARDED body ∩ free - the dependency edges |
| `meta` | bool | always False here (censused: no `_ran`/`_waived`/`fails` reads in the region) |
| `always` | bool | True only if a check name is opaque to the census (none expected; conservative fallback) |
| `name` | str | `_seg_0563_NNN__<slug>` - slug from first check name, else first write, else `stmt`; de-duplicated with a numeric suffix like 022 |

## Registry row (`_GateSeg`) - shape UNCHANGED

`(fn, free, writes, checks, needs, meta, always)`. The single row at registry index 563 is
replaced by ~378 rows in the same position, in SubSeg order. `_SEG_DEPS` continues to be derived
at import time from `needs` x `writes`; `META_CHECKS` is unchanged.

## Invariants (validated by the transformer + oracle)

1. Union of new rows' `checks` == the old row's 148 names, exactly (spec FR-001, SC-005).
2. Concatenated new-row order == original textual statement order (spec FR-007).
3. Every new `free` name ∈ (mega free ∪ mega writes ∪ gate params); no module global is a param.
4. No new segment > 400 logical statements; no function in check_village.py > 1,000 (FR-002).
5. `gate_check_names.json` byte-identical (FR-006).
6. Hard-fail census clean: no early return / global / nonlocal / del-of-local / `scale`-or-
   `meta` mutation / stale helper cell in the region (research R3/R4).

# Data Model: Gate Check Registry (022)

## Segment

One top-level statement of the legacy `gate()` body, extracted verbatim into a module-level
function. The unit of registration, dependency analysis, and targeted execution.

| Field | Meaning | Constraints |
|---|---|---|
| `fn` | the extracted function; takes its free names as keyword parameters, returns `dict` of the names it bound | body is byte-for-byte the legacy statement, dedented |
| `free` | names read from gate scope (loads minus same-segment stores) | computed by the analyzer; includes mutation targets (see below) |
| `writes` | names the segment may bind for later segments | includes any free name it MUTATES (append/extend/add/update/insert/setdefault/pop/remove/sort/clear, subscript or attribute assignment) |
| `checks` | base check names this segment can emit (literal, or the static prefix of an f-string name) | empty for pure-derivation segments |
| `meta` | True if the segment reads run state (`_ran`, `_waived`, `fails`) | meta segments never run in targeted mode |

**Invariants**:
- Registry order = legacy textual order; full mode runs every segment in order (stdout and
  failure-list order preserved by construction).
- Every one of the 549 legacy check names maps to >=1 segment; no name maps to a segment that
  cannot emit it; the full name set is pinned by a test.
- A segment bound only under a branch merges only what it bound - unbound-name errors reproduce
  legacy behavior exactly.

## Context / namespace

Per-invocation dict threaded through segments, seeded by the prelude (manifest merge with
`DEFAULT_MANIFEST`, `meta`, `scale`, `URBAN`, `houses`/`fields`/`field_by`, canvas/view bounds,
waiver state, and the `check` closure). Never module-level; never shared across invocations
(pytest -n safety).

## Targeted request

`gate(M, verbose=..., only={base names})`.
- Selection: segments whose `checks` intersect `only`, plus the transitive dependency closure over
  `free`/`writes`, executed in original order.
- `only` naming an unknown base -> `ValueError` naming it.
- `only` naming a meta check -> `ValueError` (the replay falls back to a full run instead).
- Guarantee: for each requested name, verdict (fail / pass / waived) identical to the full run.

## Meta-check set

The segments reading `_ran`/`_waived`/`fails` - measured: the waiver meta-checks
(`waivers_are_documented`, `waivers_are_live`) and the closing waiver summary. Exposed as a module
constant the replay imports (single source of truth; no second list to drift).

## Regression fixture (unchanged)

`pool/regressions/*.json`: manifest + `_regression.fires` (+ `source`/`note`/`why`). The replay
derives base names (`name.split('[')[0]`) from `fires` and uses the targeted request; fixtures
whose `fires` intersect the meta set use the full run.

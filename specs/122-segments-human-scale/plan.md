# 122 - plan

## Constitution Check

| principle | how this feature satisfies it |
|---|---|
| **I** (author is not a reviewer) | No map, page or prose changes, so no review agent applies. The independent check here is mechanical and stronger: a byte-identity oracle plus a registry-row diff, both run by the tool on every invocation. |
| **III** (pool data convention) | Untouched. |
| **VI** (verify before reporting done) | `make done` green, plus the registry-row diff captured before/after, plus a `git show`-based proof that every moved line is byte-identical. |
| **X** (code quality; clauses 13/14) | This IS clause 13. Clause 14 is respected: nothing derived is being hand-maintained - the registry keeps deriving itself, and no roster is created (the `__init__.py` star imports are one line per module, which clause 14's exemplar - feature 027 - established as the correct surface). |
| **XI** (Japanese authenticity) | No generated content. |
| **XIII** (no known regressions) | Baseline taken in a detached worktree before the first cut; `make done` compared against it. Any failure that exists in both is pre-existing and stays ledgered. |

No principle requires a deviation.

## The safety argument, and the oracle that holds it

The move is safe by construction (see spec.md "Why this is cheap NOW"), but "by construction" has
been wrong here before, so the tool proves it on every run rather than asserting it:

1. **Body byte-identity.** The concatenated sub-file bodies must equal the original file's body,
   line for line. A single changed character fails the split.
2. **Segment order.** The AST-parsed function names, read back out of the written sub-files in
   sorted-glob order, must equal the original file's function names in definition order.
3. **Registry identity** (the whole-feature oracle, run once before and once after all 13):
   `GATE_SEGMENTS` serialized to JSON - names, order, and every derived field - must be identical.
   This is the property every consumer actually depends on, and it is checked against the REAL
   registry rather than a re-implementation of it.
4. **The pin.** `tests/fixtures/gate_check_names.json` must not need editing. It is derived from a
   different path than (3), so agreeing with it is independent evidence.

## The one thing the tool authors, and why it can be wrong safely

Each sub-file needs an import block. The tool copies the original header and PRUNES it to the names
the sub-file's body actually references. A prune that is too aggressive fails loudly at import
(`NameError` on the first gate run, and `make done` runs the whole battery); a prune that is too
conservative fails loudly at lint (ruff F401). Neither can pass silently, which is why the prune is
allowed to be a heuristic rather than a proof.

## Naming

`segments_<key><letter>_<theme>.py`. The letter preserves sorted-glob contiguity with the key
ranges, so the directory listing still reads in execution order. The three city-battery files
(currently `segments_10_city_battery_a/b/c`, one contiguous range 0563_000-0563_376) collapse into
one lettered run `segments_10a..10h`, which is what they always were.

## Stages

1. **Baseline** - detached worktree at HEAD, capture `GATE_SEGMENTS` JSON and a `make done` result.
2. **Split**, one file at a time in the GM's stated order (05, 08, then the rest), each verified by
   oracles (1) and (2) as it lands.
3. **Surface** - `__init__.py` star imports, the two `CLAUDE.md` indexes.
4. **Tests** - split `test_segments_05_*` and `test_segments_08_*`; relax the mapping rule.
5. **Prove** - oracles (3) and (4), then `make done`, then compare to baseline.
6. **Record** - `future-work.md` gets the 15 over-150-line segment functions as a scoped follow-up;
   retire the one-shot tool per the 022/023 convention.

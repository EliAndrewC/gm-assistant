# Quickstart: running feature 115's verification harness

All paths relative to `.claude/skills/diagram/` inside the session clone unless stated otherwise.
Run the packaged tools AS MODULES - `python3 -m pipeline.regen`, never `python3 pipeline/regen.py`,
which would put `pipeline/` on `sys.path` instead of the skill root and import the same file twice
under two names.

**Scratch root** for this session:

    SCRATCH=/tmp/claude-1000/-gm-assistant/51f99e4b-813a-471d-a5a0-c95c154a36bf/scratchpad

This feature sweeps **three** times, not two (research R4): baseline, post-move, post-decomposition.
Steps 1, 5 and 8.

## 0. Confirm the oracle can actually see the new package (do this ONCE, before trusting a sweep)

The cache walks decide what a regen considers stale. If a nested `settlement/civic_grounds/` fell
OUT of `gencache.engine_files()`, a stale cache would reproduce the baseline for the wrong reason - a
green sweep proving nothing.

    python3 - <<'EOF'
    from pipeline import gencache
    fs = [str(p) for p in gencache.engine_files()]
    print("civic_grounds files seen:", sorted(f for f in fs if "settlement/civic_grounds" in f))
    print("tests contributing:", sum(1 for f in fs if "/tests/" in f))
    EOF

Before the split the only entry is `settlement/civic_grounds.py`. Run it again AFTER, and expect
every `settlement/civic_grounds/*.py` listed and `tests contributing: 0`.

## 1. Capture the baseline (BEFORE any code change)

The committed manifests are NOT a valid baseline (research R3, feature 110 R3). Capture from a
scratch copy of the pre-split tree:

    BASE="$SCRATCH/115-baseline"
    rm -rf "$BASE" && mkdir -p "$BASE"
    cp -a .claude/skills/diagram "$BASE/diagram"     # from the CLONE ROOT

Sweep every pool generator in the copy, live and frozen alike:

    cd "$BASE/diagram"
    python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py 2>&1 | tee /tmp/115-baseline.log

`--frozen-ok` is required or the legacy maps print `FROZEN` and skip - and for THIS feature they
carry most of the diagnostic power, because the members being moved skew urban (`execution_ground`,
`merchant_storehouses`, `granary`, `flophouse`, `inn`, `stables`, `_stable_yard`) while the live
scripted cohort is hamlets.

**Then the one `wip/` run** (research R11 - `precinct_interior`'s sole consumer, and it is not
covered by the cities the way every other member is):

    python3 -m pipeline.regen --no-cache --frozen-ok wip/shiro-daika.gen.py 2>&1 | tee /tmp/115-baseline-wip.log

Budget over 6 minutes for it. Record the hashes:

    find pool wip -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) | sort \
      | xargs sha256sum > /tmp/115-baseline.sha
    grep -c '^REGENERATED' /tmp/115-baseline.log     # note this number - part of the pass condition

## 2. Prove the guard test fires (two breakages, per contracts/mixin-surface.md C1-C3)

    # 1. delete a METHOD from a sub-mixin        -> C1 must fail, naming it
    # 2. copy a method into a second sub-mixin   -> C2 must fail, naming the collision

Breakage 1 can be run PRE-split (against `CivicGroundsMixin` as a single class). Breakage 2 needs the
package to exist, so it runs after the transformer and BEFORE the stage is committed. Record both
failure texts in tasks.md. A guard never seen red is an assumption wearing a test's clothes.

Unlike feature 114 there is no third breakage for class-level attributes - `CivicGroundsMixin` has
none (all 22 members are functions; research R2).

## 3. Run the transformer

From `.claude/skills/diagram/`:

    python3 ../../../specs/115-civic-grounds-package/split_civic_grounds.py

It REFUSES (non-zero, naming names) if the partition does not exactly cover the class or if it meets
an unnamed class-body member. Then prune the copied import headers and delete the old file:

    python3 -m ruff check --select F401 --fix settlement/civic_grounds/
    python3 -m ruff format settlement/civic_grounds/
    git rm settlement/civic_grounds.py

## 4. Confirm `core.py` is untouched

    git diff --stat -- settlement/core.py     # must print NOTHING (contract C6)

## 5. Sweep and compare - checkpoint 1, after the pure move

    WORK="$SCRATCH/115-move"
    rm -rf "$WORK" && mkdir -p "$WORK"
    cp -a .claude/skills/diagram "$WORK/diagram"     # from the CLONE ROOT
    cd "$WORK/diagram"
    python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py 2>&1 | tee /tmp/115-move.log
    python3 -m pipeline.regen --no-cache --frozen-ok wip/shiro-daika.gen.py 2>&1 | tee /tmp/115-move-wip.log
    find pool wip -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) | sort \
      | xargs sha256sum > /tmp/115-move.sha
    diff /tmp/115-baseline.sha /tmp/115-move.sha && echo "BYTE-IDENTICAL"

**An empty diff is NOT sufficient on its own.** Check all three:

    grep -c '^REGENERATED' /tmp/115-move.log     # must equal the baseline's count
    # regen's own exit code must be 0
    diff /tmp/115-baseline.sha /tmp/115-move.sha  # must be empty

The reason is a false green feature 113 actually hit (its research R9). `cp -a` copies the COMMITTED
pool artifacts into the scratch tree. If the sweep dies early - `regen` fans out across processes and
a `resvg` render can be OOM-killed when something heavy runs beside it - the artifacts sitting there
are the committed ones, untouched. They hash equal to a baseline that faithfully reproduced those
same bytes, `diff` prints nothing, and the oracle reports success having tested nothing at all.

So: **do not run the sweep beside an `-n auto` pytest or a `make done`**, and treat the exit code and
the REGENERATED count as part of the pass condition rather than as diagnostics. If memory is tight,
`--jobs 1` trades wall clock for headroom. **Sweep in the scratch copy, never in the clone.**

A NON-empty diff is a stop condition, not a diff to inspect and accept. After a pure move it means
the composition or an import binding is wrong.

## 6. Confirm the clone stayed clean, and check the move was pure

    git status --porcelain -- .claude/skills/diagram/pool     # must print nothing

Then verify the pure move really was pure - not by eye, but by comparing moved text to the original:

    git show HEAD:.claude/skills/diagram/settlement/civic_grounds.py > /tmp/115-pre.py
    python3 - <<'EOF'
    import pathlib
    pre = pathlib.Path('/tmp/115-pre.py').read_text()
    post = "\n".join(p.read_text() for p in sorted(pathlib.Path('settlement/civic_grounds').glob('*.py')))
    body = pre[pre.index('class CivicGroundsMixin:'):]
    missing = [ln.strip() for ln in body.splitlines()
               if ln.strip().startswith('#') and ln.strip() not in post]
    print("comment lines lost:", len(missing))
    for m in missing[:20]: print("  ", m)
    EOF

Expect `comment lines lost: 0`. Research R5's slicing rule, checked rather than assumed.

## 7. Decompose `_stable_yard`, then re-run the comment check

Stage 2 relocates comments that no slicing rule protects, so step 6's check is re-run against
`/tmp/115-pre.py` AFTER the decomposition. This is the step that enforces FR-009, and it is the
reason the decomposition is a separate commit: if a comment goes missing, the diff is small.

Expect `comment lines lost: 0` again.

## 8. Sweep and compare - checkpoint 2, after the decomposition

Same as step 5 into `$SCRATCH/115-decomp`, but `pool/` only - the decomposition touches nothing
`wip/shiro-daika` exercises beyond what the cities do (research R11):

    diff /tmp/115-baseline.sha /tmp/115-decomp.sha   # restricted to pool/ paths

**This is the RNG-order proof** (research R12). Because `_stable_yard` seeds and draws from the
GLOBAL `random` stream, any draw that moved across a stage boundary changes the scatter, the
furniture order, or the heap positions on every map that draws a yard. An empty diff here is strong
evidence the extraction was faithful; a dirty one means revert the last stage extracted rather than
debugging forward.

## 9. Gate

    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy   # cheap prefix first
    python3 -m pytest tests/settlement/ -q -n auto --no-cov                  # WHOLE file, no -k
    make done > /tmp/115-gate.log 2>&1                                       # backgrounded, once

Background `make done` and act on the completion notification; do not poll it. Read the log's tail
before believing green - do NOT append `; echo EXIT=$?`, which makes a failed gate report exit 0.

Only `tests/settlement/` is in the pre-gate run: unlike feature 114, no consumer outside the package
changes (research R6), so there is no `tests/tools/` assertion to carry.

Known pre-existing failure in a FRESHLY created clone:
`tests/pipeline/test_gencache.py::test_the_real_pool_round_trips_through_the_cache` reads
`pool/hamlets/inashiro.svg`, which is gitignored. It goes green after the first
`python3 -m pipeline.regen`. If exactly that one test fails on a new clone, that is what it is - not
this feature.

## 10. Check the size results

    wc -l settlement/civic_grounds/*.py | sort -rn      # every file under 400 (SC-001)

    python3 - <<'EOF'
    import ast, pathlib
    worst = max(
        ((n.end_lineno - n.lineno + 1, str(p), n.name)
         for p in pathlib.Path('settlement/civic_grounds').glob('*.py')
         for n in ast.walk(ast.parse(p.read_text()))
         if isinstance(n, ast.FunctionDef)),
    )
    print("longest function in the package:", worst)   # must be under 150 (SC-004)
    EOF

## 11. Coverage

    python3 -m coverage report --include='*/settlement/*'

At or above `SETTLEMENT_COV_FLOOR` (94, in `.claude/skills/diagram/Makefile:62`). The move cannot
change coverage; the decomposition adds seven `def` statements which execute at class creation, so
the number should be unchanged or a hair higher. A FALL is a defect to investigate - most likely a
stage function that is never called (contract C4) - not a number to re-baseline. Never lower the
floor; research R7.

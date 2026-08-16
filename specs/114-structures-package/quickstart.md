# Quickstart: running feature 114's verification harness

All paths relative to `.claude/skills/diagram/` inside the session clone unless stated otherwise.
Run the packaged tools AS MODULES - `python3 -m pipeline.regen`, never `python3 pipeline/regen.py`,
which would put `pipeline/` on `sys.path` instead of the skill root and import the same file twice
under two names.

**Scratch root** for this session:

    SCRATCH=/tmp/claude-1000/-gm-assistant/0081234f-d258-4c07-ba00-719616cd2729/scratchpad

## 0. Confirm the oracle can actually see the new package (do this ONCE, before trusting a sweep)

The cache walks decide what a regen considers stale. If a nested `settlement/structures/` fell OUT
of `gencache.engine_files()`, a stale cache would reproduce the baseline for the wrong reason - a
green sweep proving nothing. Features 112 and 113 verified this for their own packages; verify it
for `structures/` directly rather than borrowing the analogy:

    python3 - <<'EOF'
    from pipeline import gencache
    fs = [str(p) for p in gencache.engine_files()]
    print("structures files seen:", sorted(f for f in fs if "settlement/structures" in f))
    print("tests contributing:", sum(1 for f in fs if "/tests/" in f))
    EOF

Before the split the only entry is `settlement/structures.py`. Run it again AFTER, and expect every
`settlement/structures/*.py` listed and `tests contributing: 0`.

## 1. Capture the baseline (BEFORE any code change)

The committed manifests are NOT a valid baseline (research R3, feature 110 R3). Capture from a
scratch copy of the pre-split tree:

    BASE="$SCRATCH/114-baseline"
    rm -rf "$BASE" && mkdir -p "$BASE"
    cp -a .claude/skills/diagram "$BASE/diagram"     # from the CLONE ROOT

Sweep every pool generator in the copy, live and frozen alike:

    cd "$BASE/diagram"
    python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py 2>&1 | tee /tmp/114-baseline.log

`--frozen-ok` is required or the legacy maps print `FROZEN` and skip - and for THIS feature they
carry most of the diagnostic power, because the members being moved skew urban (`servant_ranges`,
`rowpack`, `merchant_estates`, `drum_tower`, `theater_stage`, `place_punishment_spot`) while the
live scripted cohort is hamlets. `wip/shiro-daika.gen.py` is deliberately excluded (research R3).

Record the hashes:

    find pool -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) | sort \
      | xargs sha256sum > /tmp/114-baseline.sha
    grep -c '^REGENERATED' /tmp/114-baseline.log     # note this number - it is part of the pass condition

## 2. Sweep and compare (after Stage 1 - twice in total, not seven times)

    WORK="$SCRATCH/114-work"
    rm -rf "$WORK" && mkdir -p "$WORK"
    cp -a .claude/skills/diagram "$WORK/diagram"     # from the CLONE ROOT
    cd "$WORK/diagram"
    python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py 2>&1 | tee /tmp/114-work.log
    find pool -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) | sort \
      | xargs sha256sum > /tmp/114-work.sha
    diff /tmp/114-baseline.sha /tmp/114-work.sha && echo "BYTE-IDENTICAL"

**An empty diff is NOT sufficient on its own.** Check all three:

    grep -c '^REGENERATED' /tmp/114-work.log     # must equal the baseline's count
    # regen's own exit code must be 0
    diff /tmp/114-baseline.sha /tmp/114-work.sha  # must be empty

The reason is a false green feature 113 actually hit (its research R9). `cp -a` copies the COMMITTED
pool artifacts into the scratch tree. If the sweep dies early - `regen` fans out across processes and
a `resvg` render can be OOM-killed when something heavy runs beside it - the artifacts sitting there
are the committed ones, untouched. They hash equal to a baseline that faithfully reproduced those
same bytes, `diff` prints nothing, and the oracle reports success having tested nothing at all.

So: **do not run the sweep beside an `-n auto` pytest or a `make done`**, and treat the exit code and
the REGENERATED count as part of the pass condition rather than as diagnostics. If memory is tight,
`--jobs 1` trades wall clock for headroom. **Sweep in the scratch copy, never in the clone** - that
is what keeps the clone's committed frozen artifacts untouched.

A NON-empty diff is a stop condition, not a diff to inspect and accept. After a pure move it means
the composition or an import binding is wrong.

## 3. Confirm the clone stayed clean

    git status --porcelain -- .claude/skills/diagram/pool

Must print nothing. A frozen map's committed bytes changing is a stop-work condition.

## 4. Prove the guard test fires (three breakages, per contracts/mixin-surface.md)

    # 1. delete a METHOD from a sub-mixin        -> assertion 1 must fail, naming it
    # 2. delete a class-level ATTRIBUTE          -> assertion 1 must fail, naming it
    # 3. copy a method into a second sub-mixin   -> assertion 2 must fail, naming the collision

Breakage 1 can be run PRE-split (against `StructuresMixin` as a single class). Breakages 2 and 3 need
the package to exist, so they run after the transformer and BEFORE the stage is committed. Record all
three failure texts in tasks.md. A guard never seen red is an assumption wearing a test's clothes.

## 5. Gate

    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy   # cheap prefix first
    python3 -m pytest tests/settlement/ tests/tools/ -q -n auto --no-cov    # WHOLE files, no -k
    make done > /tmp/114-gate.log 2>&1                                      # backgrounded, once

Background `make done` and act on the completion notification; do not poll it. Read the log's tail
before believing green - do NOT append `; echo EXIT=$?`, which makes a failed gate report exit 0.

`tests/tools/` is in the pre-gate run because `test_why_placed.py` is this feature's one consumer
change (research R6) and is exactly the kind of test a `tests/settlement/`-only run would miss.

Known pre-existing failure in a FRESHLY created clone:
`tests/pipeline/test_gencache.py::test_the_real_pool_round_trips_through_the_cache` reads
`pool/hamlets/inashiro.svg`, which is gitignored. It goes green after the first
`python3 -m pipeline.regen`. If exactly that one test fails on a new clone, that is what it is - not
this feature.

## 6. Check the file-size result, and that the grounding comments arrived

    wc -l settlement/structures/*.py | sort -rn

Every file under ~450 lines (SC-001). Then verify the pure move really was pure - not by eye, but by
comparing the moved text against the original:

    git show HEAD:.claude/skills/diagram/settlement/structures.py > /tmp/114-pre.py
    python3 - <<'EOF'
    import ast, pathlib, re
    pre = pathlib.Path('/tmp/114-pre.py').read_text()
    post = "\n".join(p.read_text() for p in sorted(pathlib.Path('settlement/structures').glob('*.py')))
    # every comment line in the pre-split class body must survive somewhere in the package
    body = pre[pre.index('class StructuresMixin:'):]
    missing = [ln.strip() for ln in body.splitlines()
               if ln.strip().startswith('#') and ln.strip() not in post]
    print("comment lines lost:", len(missing))
    for m in missing[:20]: print("  ", m)
    EOF

Expect `comment lines lost: 0`. This is research R5's slicing rule, checked rather than assumed - in
this project a comment above a method is usually researched grounding, and a "pure move" that drops
a why-comment is not pure.

## 7. Coverage

    python3 -m coverage report --include='*/settlement/*'

At or above `SETTLEMENT_COV_FLOOR` (94). A pure move CANNOT change coverage - it relocates executable
lines without adding, removing or altering one, and the floor is measured over the package combined.
So a movement here is a signal to investigate (a member lost, a module not composed), not a number to
re-baseline. Never lower the floor; research R7.

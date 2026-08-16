# Quickstart: running feature 116's verification harness

All paths relative to `.claude/skills/diagram/` inside the session clone unless stated otherwise.
Run the packaged tools AS MODULES - `python3 -m pipeline.regen`, never `python3 pipeline/regen.py`,
which would put `pipeline/` on `sys.path` instead of the skill root and import the same file twice
under two names.

**Scratch root** for this session:

    SCRATCH=/tmp/claude-1000/-gm-assistant/4eb77348-7747-44cf-b815-3d76370aeb37/scratchpad

## 0. Confirm the oracle can actually see the new package (ONCE, before trusting a sweep)

The cache walk decides what a regen considers stale. If a nested `settlement/shrines_wells/` fell OUT
of `gencache.engine_files()`, a stale cache would reproduce the baseline for the wrong reason - a
green sweep proving nothing. The walk is depth-agnostic by construction (feature 025 made
`settlement/` a package for exactly this reason and the docstring says so), but a borrowed analogy is
not a check:

    python3 - <<'EOF'
    from pipeline import gencache
    fs = [str(p) for p in gencache.engine_files()]
    print("shrines_wells files seen:", sorted(f for f in fs if "settlement/shrines_wells" in f))
    print("tests contributing:", sum(1 for f in fs if "/tests/" in f))
    EOF

Before the split the only entry is `settlement/shrines_wells.py`. Run it again AFTER, and expect
every `settlement/shrines_wells/*.py` listed and `tests contributing: 0`.

## 1. Capture the baseline (BEFORE any code change)

The committed manifests are NOT a valid baseline (research R3). Capture from a scratch copy of the
pre-split tree:

    BASE="$SCRATCH/116-baseline"
    rm -rf "$BASE" && mkdir -p "$BASE"
    cp -a .claude/skills/diagram "$BASE/diagram"     # from the CLONE ROOT

Sweep every pool generator in the copy, live and frozen alike:

    cd "$BASE/diagram"
    python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py 2>&1 | tee /tmp/116-baseline.log

`--frozen-ok` is required or the legacy maps print `FROZEN` and skip - and for THIS feature they
carry most of the diagnostic power, because the members being moved skew rural-and-legacy
(`farm_wells`, `small_shrine`, `torii_even`, `forest`, `draft_byres`, the town/city `shrine_hall`
paths) while the live scripted cohort is hamlets. `wip/shiro-daika.gen.py` is deliberately excluded
(research R3 / feature 112 R11).

Record the hashes:

    find pool -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) | sort \
      | xargs sha256sum > /tmp/116-baseline.sha
    grep -c '^REGENERATED' /tmp/116-baseline.log     # note this number - part of the pass condition

## 2. Sweep and compare (after Stage 1 - twice in total, not seven times)

    WORK="$SCRATCH/116-work"
    rm -rf "$WORK" && mkdir -p "$WORK"
    cp -a .claude/skills/diagram "$WORK/diagram"     # from the CLONE ROOT
    cd "$WORK/diagram"
    python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py 2>&1 | tee /tmp/116-work.log
    find pool -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) | sort \
      | xargs sha256sum > /tmp/116-work.sha
    diff /tmp/116-baseline.sha /tmp/116-work.sha && echo "BYTE-IDENTICAL"

**An empty diff is NOT sufficient on its own.** Check all three:

    grep -c '^REGENERATED' /tmp/116-work.log     # must equal the baseline's count
    # regen's own exit code must be 0
    diff /tmp/116-baseline.sha /tmp/116-work.sha  # must be empty

The reason is a false green feature 113 actually hit (its research R9). `cp -a` copies the COMMITTED
pool artifacts into the scratch tree. If the sweep dies early - `regen` fans out across processes and
a `resvg` render can be OOM-killed when something heavy runs beside it - the artifacts sitting there
are the committed ones, untouched. They hash equal to a baseline that faithfully reproduced those
same bytes, `diff` prints nothing, and the oracle reports success having tested nothing at all.

So: **do not run the sweep beside an `-n auto` pytest or a `make done`**, and treat the exit code and
the REGENERATED count as part of the pass condition rather than as diagnostics. If memory is tight,
`--jobs 1` trades wall clock for headroom. **Sweep in the scratch copy, never in the clone** - that is
what keeps the clone's committed frozen artifacts untouched.

A NON-empty diff is a stop condition, not a diff to inspect and accept. After a pure move it means the
composition or an import binding is wrong.

## 3. Confirm the clone stayed clean

    git status --porcelain -- .claude/skills/diagram/pool

Must print nothing. A frozen map's committed bytes changing is a stop-work condition.

## 4. Prove the guard test fires (two breakages, per contracts/mixin-surface.md)

    # 1. delete a METHOD from a sub-mixin (e.g. _well_vr)  -> C1 must fail, naming it
    # 2. copy a method into a second sub-mixin             -> C2 must fail, naming the collision

Breakage 1 can be run PRE-split (against `ShrinesWellsMixin` as a single class). Breakage 2 needs the
package to exist, so it runs after the transformer and BEFORE the stage is committed. Record both
failure texts in tasks.md. A guard never seen red is an assumption wearing a test's clothes.

Feature 114's third breakage (delete a class-level ATTRIBUTE) has no subject here - this class defines
none - but C1 keeps the `vars()` form that would catch it.

## 5. Gate

    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy   # cheap prefix first
    python3 -m pytest tests/settlement/ -q -n auto --no-cov                  # WHOLE files, no -k
    make done > /tmp/116-gate.log 2>&1                                       # backgrounded, once

Background `make done` and act on the completion notification; do not poll it. Read the log's tail
before believing green - do NOT append `; echo EXIT=$?`, which makes a failed gate report exit 0.

Only `tests/settlement/` is in the pre-gate run because this feature has NO consumer change outside
the package (research R6) - unlike 114, which had to include `tests/tools/`. If the consumer census
ever turns up a hit, add that file's whole test directory here.

Known pre-existing failure in a FRESHLY created clone:
`tests/pipeline/test_gencache.py::test_the_real_pool_round_trips_through_the_cache` reads
`pool/hamlets/inashiro.svg`, which is gitignored. It goes green after the first
`python3 -m pipeline.regen`. If exactly that one test fails on a new clone, that is what it is - not
this feature.

## 6. Check the file-size result, and that the move really was pure

    wc -l settlement/shrines_wells/*.py | sort -rn

Every file under 320 raw lines (SC-001).

### 6a. The decorator survived

The one hazard this file introduces that its predecessors did not have (research R5) - a lost
`@contextlib.contextmanager` leaves the NAME in place and turns a context manager into a plain
generator:

    python3 - <<'EOF'
    import inspect, settlement
    src = inspect.getsource(settlement.Settlement.frozen_terrain)
    print("decorator present:", "@contextlib.contextmanager" in src)
    s = settlement.Settlement(400, 400, seed=1)
    with s.frozen_terrain():
        pass
    print("context manager works")
    EOF

### 6b. No grounding comment was dropped

Not by eye - by comparing the moved text against the original:

    git show HEAD:.claude/skills/diagram/settlement/shrines_wells.py > /tmp/116-pre.py
    python3 - <<'EOF'
    import pathlib
    # The two section-divider banners are dropped ON PURPOSE (DROP_BANNERS in the transformer): each
    # names a position in a file that no longer exists, and the half of "hill + shrine + torii" that
    # is torii now lives in another module. Every OTHER comment line must survive.
    DROPPED = {"# ---- hill + shrine + torii", "# ---- landscape / estate features"}
    pre = pathlib.Path('/tmp/116-pre.py').read_text()
    post = "\n".join(p.read_text() for p in sorted(pathlib.Path('settlement/shrines_wells').glob('*.py')))
    body = pre[pre.index('class ShrinesWellsMixin:'):]
    missing = [ln.strip() for ln in body.splitlines()
               if ln.strip().startswith('#') and ln.strip() not in post and ln.strip() not in DROPPED]
    print("comment lines lost:", len(missing))
    for m in missing[:20]: print("  ", m)
    # ...and prove the two banners really are gone rather than assumed gone
    print("banners still present:", sorted(b for b in DROPPED if b in post))
    EOF

Expect `comment lines lost: 0` and `banners still present: []` (SC-007). This is research R5's slicing rule, checked rather than
assumed - in this project a comment above a method is usually researched grounding, and a "pure move"
that drops a why-comment is not pure. This file carries more such grounding than any other module in
the package, which is why the check is a pass condition and not a nicety.

## 7. Coverage

    python3 -m coverage report --include='*/settlement/*'

At or above `SETTLEMENT_COV_FLOOR` (94). A pure move CANNOT change coverage - it relocates executable
lines without adding, removing or altering one, and the floor is measured over the package combined.
So a movement here is a signal to investigate (a member lost, a module not composed), not a number to
re-baseline. Never lower the floor; research R7.

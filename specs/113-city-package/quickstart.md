# Quickstart: running feature 113's verification harness

All paths relative to `.claude/skills/diagram/` inside the session clone, and all commands are
POST-reorg (the "Diagram reorganize" session's tip, `78be5bb`). The three that changed shape:
`tests/settlement/` replaces `test_settlement/`, helper imports are package-qualified
(`from tests.settlement._builders import ...`), and the loose top-level tools are packages run AS
MODULES - `python3 -m pipeline.regen`, never `python3 pipeline/regen.py`, which would put
`pipeline/` on `sys.path` instead of the skill root and import the same file twice under two names.

## 0. Confirm the oracle can actually see the new package (do this ONCE, before trusting a sweep)

The cache walks decide what a regen considers stale. If a nested `settlement/city/` fell OUT of
`gencache.engine_files()`, a stale cache would reproduce the baseline for the wrong reason - a
green sweep proving nothing. The peer session verified this for `settlement/fields/`; verify it for
`city/` directly rather than borrowing the analogy:

    python3 - <<'EOF'
    from pipeline import gencache
    fs = [str(p) for p in gencache.engine_files()]
    print("city files seen:", sorted(f for f in fs if "settlement/city" in f))
    print("tests contributing:", sum(1 for f in fs if "/tests/" in f))
    EOF

Expect every `settlement/city/*.py` listed and `tests contributing: 0`. Run it again AFTER the
split lands - before it, the only city file is `settlement/city.py`.

## 1. Capture the baseline (BEFORE any code change)

The committed manifests are NOT a valid baseline (research R3, feature 110 R3). Capture from a
scratch copy of the pre-split tree:

    BASE=/tmp/claude-1000/-gm-assistant/<session>/scratchpad/113-baseline
    rm -rf "$BASE" && mkdir -p "$BASE"
    cp -a .claude/skills/diagram "$BASE/diagram"     # from the clone root

Sweep every pool generator in the copy, live and frozen alike:

    cd "$BASE/diagram"
    python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py

`--frozen-ok` is required or the legacy maps print `FROZEN` and skip - and for THIS feature they
are not optional, because the provincial cities and the frozen pool are the only artifacts that
exercise the city wing at all. `wip/` is deliberately excluded (research R3, quoting 112 R11).

Record the hashes:

    find pool -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) | sort \
      | xargs sha256sum > /tmp/113-baseline.sha

## 2. Sweep and compare (after Stage 1, and after EACH Stage 2 decomposition - seven runs total)

    WORK=/tmp/claude-1000/-gm-assistant/<session>/scratchpad/113-work
    rm -rf "$WORK" && mkdir -p "$WORK"
    cp -a .claude/skills/diagram "$WORK/diagram"
    cd "$WORK/diagram" && python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py
    find pool -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) | sort \
      | xargs sha256sum > /tmp/113-work.sha
    diff /tmp/113-baseline.sha /tmp/113-work.sha && echo "BYTE-IDENTICAL"

An empty diff is the pass condition. **Sweep in the scratch copy, never in the clone** - that is
what keeps the clone's committed frozen artifacts untouched. Both sweeps use the same relative
paths, so the `sha256sum` diff is a pure content comparison.

A NON-empty diff is a stop condition, not a diff to inspect and accept. After a pure move it means
the composition or an import binding is wrong; after a decomposition it means a draw was reordered
(almost always an RNG call that changed position relative to another).

## 3. Confirm the clone stayed clean

    git status --porcelain -- .claude/skills/diagram/pool

Must print nothing. A frozen map's committed bytes changing is a stop-work condition.

Note also: `.coverage.*` is gitignored as of the reorg tip (only bare `.coverage` was before), so a
routine `git add -A` no longer sweeps xdist parallel-mode data files into the index.

## 4. Gate

    cd .claude/skills/diagram
    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy   # cheap prefix first
    python3 -m pytest tests/settlement/ -q -n auto --no-cov                  # WHOLE files, no -k
    make done > /tmp/113-gate.log 2>&1                                       # backgrounded, once

Background `make done` and act on the completion notification; do not poll it. Read the log's tail
before believing green - do NOT append `; echo EXIT=$?`, which makes a failed gate report exit 0.

Known pre-existing failure in a FRESHLY created clone:
`tests/pipeline/test_gencache.py::test_the_real_pool_round_trips_through_the_cache` reads
`pool/hamlets/inashiro.svg`, which is gitignored. It goes green after the first
`python3 -m pipeline.regen`. If exactly that one test fails on a new clone, that is what it is - not
this feature.

## 5. Prove the guard test fires

Per `contracts/mixin-surface.md`, before trusting the composed-surface guard:

    # break it one way, observe the failure, revert
    # 1. delete a method from a sub-mixin      -> assertion 1 must fail, naming it
    # 2. duplicate a method into a second one  -> assertion 2 must fail, naming the collision

Record both failure texts in tasks.md. A guard never seen red is an assumption wearing a test's
clothes.

## 6. Check the file-size and function-size result

    wc -l settlement/city/*.py | sort -rn
    python3 - <<'EOF'
    import ast, pathlib
    for p in sorted(pathlib.Path('settlement/city').glob('*.py')):
        t = ast.parse(p.read_text())
        for n in ast.walk(t):
            if isinstance(n, ast.FunctionDef) and n.end_lineno - n.lineno + 1 > 150:
                print(f"OVER 150: {p.name}:{n.lineno} {n.name} ({n.end_lineno-n.lineno+1})")
    EOF

Every file under ~1,000 lines; nothing printed by the second command without an inline
justification comment at that function's `def`.

## 7. Coverage

    python3 -m coverage report --include='*/settlement/*'

At or above `SETTLEMENT_COV_FLOOR` (94 on the reorg tip; 95 measured). Raise the floor only to a
figure THIS feature measured, and record the measurement in the comment above it in the Makefile.
Never lower it. A pure move cannot change coverage - a movement after Stage 1 is a signal to
investigate, not a number to bank (research R7).

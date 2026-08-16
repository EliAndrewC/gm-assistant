# Quickstart: running feature 112's verification harness

All paths relative to `.claude/skills/diagram/` inside the session clone.

## 1. Capture the baseline (BEFORE any code change)

The committed pool artifacts are not a valid baseline (research R4). Capture from a scratch copy of
the pre-split tree:

    BASE=/tmp/claude-1000/-gm-assistant/<session>/scratchpad/112-baseline
    rm -rf "$BASE" && mkdir -p "$BASE"
    cp -a .claude/skills/diagram "$BASE/diagram"     # from the repo root

Then sweep every generator in the copy, live and frozen alike, writing manifests where they land:

    cd "$BASE/diagram"
    python3 regen.py --no-cache --frozen-ok pool/*/*.gen.py

`--frozen-ok` is required: `regen.py` prints `FROZEN` and skips the legacy maps otherwise, and those
maps are the only exercisers of the land-use overlay wing. `wip/` is deliberately NOT swept - see
research.md R11.

Record the hashes:

    find pool -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) | sort | xargs sha256sum > /tmp/112-baseline.sha

## 2. Sweep and compare (after Stage 1, and after EACH Stage 2 decomposition)

Sweep a scratch copy of the CURRENT tree the same way, then diff the hash lists:

    WORK=/tmp/.../112-work && rm -rf "$WORK" && mkdir -p "$WORK"
    cp -a .claude/skills/diagram "$WORK/diagram"
    cd "$WORK/diagram" && python3 regen.py --no-cache --frozen-ok pool/*/*.gen.py
    find pool -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) | sort | xargs sha256sum > /tmp/112-work.sha
    diff /tmp/112-baseline.sha /tmp/112-work.sha && echo "BYTE-IDENTICAL"

An empty diff is the pass condition. **Sweep in the scratch copy, never in the clone** - that is what
keeps the clone's committed frozen artifacts untouched.

Note the filename basis: `sha256sum` output includes the path, and both sweeps use the same relative
paths, so the diff is a pure content comparison.

## 3. Confirm the clone stayed clean

    git status --porcelain -- .claude/skills/diagram/pool

Must print nothing. A frozen map's committed bytes changing is a stop-work condition, not a diff to
accept.

## 4. Gate

    cd .claude/skills/diagram
    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy      # cheap prefix first
    python3 -m pytest test_settlement/ -q -n auto --no-cov                       # WHOLE files, no -k
    make done > /tmp/112-gate.log 2>&1                                           # backgrounded, once

Background `make done` and act on the completion notification; do not poll it. Read the log's tail
before believing green - do not append `; echo EXIT=$?`, which makes a failed gate report exit 0.

## 5. Prove the guard test fires

Per the contract, before trusting the composed-surface guard:

    # break it one way, observe the failure, revert
    # 1. delete a method from a sub-mixin      -> assertion 1 must fail, naming it
    # 2. duplicate a method into a second one  -> assertion 2 must fail, naming the collision

## 6. Check the file-size result

    wc -l settlement/fields/*.py | sort -rn
    python3 - <<'EOF'
    import ast, pathlib
    for p in sorted(pathlib.Path('settlement/fields').glob('*.py')):
        t = ast.parse(p.read_text())
        for n in ast.walk(t):
            if isinstance(n, ast.FunctionDef) and n.end_lineno - n.lineno + 1 > 150:
                print(f"OVER 150: {p.name}:{n.lineno} {n.name} ({n.end_lineno-n.lineno+1})")
    EOF

Every file under ~1,000 lines; nothing printed by the second command without an inline
justification comment at that function.

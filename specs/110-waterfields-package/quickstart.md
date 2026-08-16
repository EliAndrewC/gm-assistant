# Quickstart: verifying the waterfields/ split

**Feature**: 110-waterfields-package

All commands run from the session clone's diagram skill dir:
`/gm-assistant/.clones/diagram-architecture/.claude/skills/diagram`

## 1. Capture the baseline (BEFORE any split work)

```bash
SCRATCH=/tmp/claude-1000/-gm-assistant/*/scratchpad/wf-baseline
# copy the skill tree at HEAD, run every waterfields-consuming gen, keep the manifests
cp -r . $SCRATCH/tree && cd $SCRATCH/tree
for g in $(grep -rl "from waterfields import\|import waterfields" pool/*/*.gen.py); do python3 "$g"; done
mkdir -p $SCRATCH/manifests && cp pool/*/*.json $SCRATCH/manifests/
```

(Direct `python3 <gen>` bypasses regen.py's frozen-legacy skip - that guard protects the REAL
pool; the scratch copy is throwaway. Committed pool artifacts in the clone are never touched.)

## 2. After the move (and after EACH mega-function decomposition)

```bash
# fresh scratch copy of the WORKING tree, same gen sweep, then byte-diff
diff -r $SCRATCH/manifests $SCRATCH/post/manifests   # must be empty
```

## 3. The gate

```bash
make done          # ruff + format + mypy --strict + pytest (+ per-module 100% coverage)
```

- `test_villages.py` regenerates every scripted map through gencache and runs the full
  check_village battery (checks never cached) - the regression corpus rides along.
- `test_waterfields_surface.py` (new) pins the consumed import surface.
- Background the final gate; act on the notification (`make done > /tmp/gate.log 2>&1`,
  nothing appended after it).

## 4. Size checks

```bash
wc -l waterfields/*.py                 # every file < 1,000
python3 - <<'EOF'                      # no function > ~150 lines
import ast, glob
for f in glob.glob('waterfields/*.py'):
    t = ast.parse(open(f).read())
    for n in ast.walk(t):
        if isinstance(n, ast.FunctionDef) and (n.end_lineno - n.lineno) > 150:
            print(f, n.name, n.end_lineno - n.lineno)
EOF
```

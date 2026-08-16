# Quickstart: verifying the hamletgen package split

**Feature**: 111-hamletgen-package | **Date**: 2026-08-16

All commands run from `.claude/skills/diagram/` **inside the session clone**
(`/gm-assistant/.clones/diagram-architecture/`). `$SCRATCH` is this session's scratchpad.

## 1. Capture the pre-split baseline (BEFORE any code change)

The committed pool manifests are not a valid oracle (the pool is frozen against re-rolls -
research R3). Capture from a scratch copy of the tree at HEAD:

```bash
SCRATCH=/tmp/claude-1000/-gm-assistant/<session>/scratchpad
rm -rf $SCRATCH/hg-baseline && mkdir -p $SCRATCH/hg-baseline
cp -a /gm-assistant/.clones/diagram-architecture/.claude/skills/diagram $SCRATCH/hg-baseline/tree
cd $SCRATCH/hg-baseline/tree

# the four live hamlets, at their committed seeds
for h in inashiro mizuguchi kashikawa sawada; do python3 pool/hamlets/$h.gen.py; done
mkdir -p $SCRATCH/hg-baseline/manifests
cp pool/hamlets/*.json pool/hamlets/*.svg $SCRATCH/hg-baseline/manifests/

# the fixed-seed cohort (24 seeds), written out rather than thrown away
python3 $SPEC/baseline_cohort.py --out $SCRATCH/hg-baseline/cohort
# and the cohort report table, which carries the per-seed gate verdicts
python3 -c "import hamletgen,sys; sys.exit(hamletgen.main(['--batch','24']))" \
  > $SCRATCH/hg-baseline/cohort-report.txt 2>&1; echo "batch exit=$?"
```

`baseline_cohort.py` (in this spec dir) mirrors `cohort()`'s own seed/household formula
(`hh = 10 + (seed * 7) % 11`) but passes `out_base` so each roll writes a manifest;
`cohort()` itself finishes into a temp dir and discards it.

## 2. Byte-identity after any change

Re-run the same sweep against a fresh scratch copy of the CURRENT working tree and diff:

```bash
rm -rf $SCRATCH/hg-now && mkdir -p $SCRATCH/hg-now
cp -a /gm-assistant/.clones/diagram-architecture/.claude/skills/diagram $SCRATCH/hg-now/tree
cd $SCRATCH/hg-now/tree
for h in inashiro mizuguchi kashikawa sawada; do python3 pool/hamlets/$h.gen.py; done
python3 $SPEC/baseline_cohort.py --out $SCRATCH/hg-now/cohort
python3 -m hamletgen --batch 24 > $SCRATCH/hg-now/cohort-report.txt 2>&1

diff -r $SCRATCH/hg-baseline/manifests <(ls) >/dev/null   # see the script below for the real form
diff -r $SCRATCH/hg-baseline/cohort   $SCRATCH/hg-now/cohort
diff      $SCRATCH/hg-baseline/cohort-report.txt $SCRATCH/hg-now/cohort-report.txt
```

**Must be empty every time.** A single differing byte is a failed refactor, not a tolerance.

Use a scratch COPY rather than the clone itself so the frozen pool files are never dirtied.

## 3. Consumer-surface guard

```bash
python3 -m pytest test_hamletgen_surface.py -v
```

Prove it fires before trusting it (SC-006): comment out one `from .<module> import *` line in
`hamletgen/__init__.py`, re-run, confirm FAIL naming the missing names, restore, confirm green.

## 4. Function-scale check (US2)

```bash
python3 - <<'PY'
import ast, pathlib
for p in sorted(pathlib.Path("hamletgen").glob("*.py")):
    t = ast.parse(p.read_text())
    for n in ast.walk(t):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            size = n.end_lineno - n.lineno + 1
            if size > 150:
                print(f"{p}:{n.lineno} {n.name} = {size} lines")
PY
```

Any hit is either split further or carries an inline one-line justification.

## 5. File-scale check (US3)

```bash
wc -l hamletgen/*.py test_hamletgen/*.py | sort -rn | head -20
```

Every file under ~1,000 raw lines.

## 6. The gate

```bash
cd /gm-assistant/.clones/diagram-architecture/.claude/skills/diagram
make done > /tmp/gate-111.log 2>&1     # background it; do NOT append `; echo EXIT=$?`
tail -40 /tmp/gate-111.log
```

Runs ruff + `check-duplicate-defs.py` + `ruff format --check` + `mypy --strict` + pytest `-n auto`
+ the per-module 100% coverage gate. `hamletgen` is in both the mypy `files` list and the coverage
`source` list, so both follow the package automatically once the mypy entry is updated.

## 7. Consumer-diff scope (SC-002)

```bash
git status --short
git diff --stat HEAD
```

Changes must appear ONLY in: `hamletgen/` (new), `hamletgen.py` (deleted), `test_hamletgen/` (new),
`test_hamletgen.py` (deleted), `test_hamletgen_surface.py` (new), `pyproject.toml`, docs, and
`specs/`. Any change under `pool/hamlets/*.gen.py` or in `cohort_audit.py` is a contract violation.

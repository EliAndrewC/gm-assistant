"""Research probe for feature 109: are registry.py's rows fully derivable?

Re-runs feature 022's own AST analysis (imported from specs/022-gate-check-registry/
transform_gate.py) against the verbatim segment bodies in the segments_* modules and
compares every derived field against the live GATE_SEGMENTS rows. Also probes the
cheap derivations (free == signature, order == name sort, META_CHECKS) and times
the whole analysis to answer import-time-vs-build-step.
"""

import ast
import importlib.util
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / ".claude" / "skills" / "diagram"
sys.path.insert(0, str(SKILL))

spec = importlib.util.spec_from_file_location("transform_gate", REPO / "specs" / "022-gate-check-registry" / "transform_gate.py")
tg = importlib.util.module_from_spec(spec)
sys.modules["transform_gate"] = tg
spec.loader.exec_module(tg)

t0 = time.perf_counter()
from check_village.registry import GATE_SEGMENTS, META_CHECKS  # noqa: E402

t_import = time.perf_counter() - t0

gate_locals = set()
for s in GATE_SEGMENTS:
    gate_locals |= set(s.free) | set(s.writes)

# emissions: helper -> check names, over every module in the package
t1 = time.perf_counter()
emissions = {}
seg_files = sorted((SKILL / "check_village").glob("*.py"))
trees = {}
for f in seg_files:
    tree = ast.parse(f.read_text())
    trees[f.name] = tree
    emissions.update(tg._module_emissions(tree))

# index the segment function defs by name
seg_defs = {}
for name, tree in trees.items():
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_seg_"):
            seg_defs[node.name] = node

mismatch = {"free": [], "writes": [], "checks": [], "needs": [], "meta": [], "always": [], "sig": [], "order": [], "missing": []}
for i, row in enumerate(GATE_SEGMENTS):
    fn = row.fn
    nm = fn.__name__
    node = seg_defs.get(nm)
    if node is None:
        mismatch["missing"].append(nm)
        continue
    # signature probe: keyword-only params == free?
    kwonly = tuple(a.arg for a in node.args.kwonlyargs)
    if kwonly != row.free:
        mismatch["sig"].append((nm, kwonly, row.free))
    body = [st for st in node.body if not (isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant))]
    # the original analysis ran per-statement on statement s; segment body should be exactly that
    loads = set()
    stores = set()
    muts = set()
    exposed = set()
    checks_d = []
    opaque = 0
    for st in body:
        if isinstance(st, ast.Return):
            continue  # the return _kept(...) epilogue was added by the transform, not part of s
        loads |= tg._loads(st)
        stores |= tg._stores(st, into_defs=False)
        muts |= tg._mutation_targets(st)
        c, o = tg._check_names(st, emissions)
        checks_d += c
        opaque += o
        exposed |= tg._exposed_reads([st], set())[0]
    writes_d = tuple(sorted(stores | (muts & gate_locals)))
    free_d = tuple(sorted((loads & gate_locals) | (muts & gate_locals)))
    needs_d = tuple(sorted((((exposed & gate_locals) | (muts & gate_locals))) & set(free_d)))
    meta_d = bool({"_ran", "_waived", "fails"} & loads)
    always_d = bool(opaque)
    if free_d != row.free:
        mismatch["free"].append((nm, free_d, row.free))
    if writes_d != row.writes:
        mismatch["writes"].append((nm, writes_d, row.writes))
    if tuple(sorted(set(checks_d))) != tuple(sorted(row.checks)):
        mismatch["checks"].append((nm, checks_d, row.checks))
    if needs_d != tuple(sorted(row.needs)):
        mismatch["needs"].append((nm, needs_d, row.needs))
    if meta_d != row.meta:
        mismatch["meta"].append((nm, meta_d, row.meta))
    if always_d != row.always:
        mismatch["always"].append((nm, always_d, row.always))

t_analyze = time.perf_counter() - t1

# order probe: numeric key from the name reproduces registry order?
def key(nm):
    parts = nm[len("_seg_"):].split("__")[0].split("_")
    return tuple(int(p) for p in parts if p.isdigit() or (p and p[0].isdigit()))

names = [r.fn.__name__ for r in GATE_SEGMENTS]
keys = [key(n) for n in names]
order_ok = keys == sorted(keys) and len(set(keys)) == len(keys)

# META_CHECKS probe
meta_d = frozenset(c for r in GATE_SEGMENTS if r.meta for c in r.checks)

print(f"rows={len(GATE_SEGMENTS)} segs_found={len(seg_defs)} import_s={t_import:.3f} analyze_s={t_analyze:.3f}")
print(f"order_derivable={order_ok} meta_checks_match={meta_d == META_CHECKS}")
for k, v in mismatch.items():
    print(f"{k}: {len(v)} mismatches")
    for entry in v[:3]:
        print("   ", str(entry)[:300])

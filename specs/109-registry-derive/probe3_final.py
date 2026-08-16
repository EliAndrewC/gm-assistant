"""Post-merge probe: auto-discovers PLACEMENTS (rows out of key order) and NEEDS_OVERRIDES
(rows whose derived needs differ), verifies everything else derives exactly. The output of this
probe IS the decided-data content for the new registry.py."""

import ast
import importlib.util
import re
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
from check_village.registry import GATE_SEGMENTS, META_CHECKS

t0 = time.perf_counter()
segdefs, emissions = {}, {}
for f in sorted((SKILL / "check_village").glob("*.py")):
    tree = ast.parse(f.read_text())
    emissions.update(tg._module_emissions(tree))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_seg_"):
            segdefs[node.name] = node

gate_locals = set()
for s in GATE_SEGMENTS:
    gate_locals |= set(s.free) | set(s.writes)

def body_of(node):
    b = [st for st in node.body if not (isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant))]
    return b[:-1], b[-1]

helper_mut = {}
for node in segdefs.values():
    stmts, _ = body_of(node)
    for st in stmts:
        for n in ast.walk(st):
            if isinstance(n, ast.FunctionDef) and n.name in gate_locals:
                helper_mut[n.name] = (tg._mutation_targets(n) - tg._bound_anywhere(n)) & gate_locals
for _ in range(len(helper_mut) + 1):
    changed = False
    for node in segdefs.values():
        stmts, _ = body_of(node)
        for st in stmts:
            for n in ast.walk(st):
                if isinstance(n, ast.FunctionDef) and n.name in helper_mut:
                    via = set().union(*(helper_mut.get(c, set()) for c in tg._loads(n)), set()) - tg._bound_anywhere(n)
                    if not via <= helper_mut[n.name]:
                        helper_mut[n.name] |= via
                        changed = True
    if not changed:
        break

mm = {"free": [], "writes": [], "checks": [], "meta": [], "always": []}
needs_overrides = {}
for row in GATE_SEGMENTS:
    node = segdefs[row.fn.__name__]
    stmts, ret = body_of(node)
    sig = tuple(a.arg for a in node.args.kwonlyargs)
    if sig != row.free: mm["free"].append(row.fn.__name__)
    wr = tuple(ast.literal_eval(ret.value.args[1]))
    if wr != row.writes: mm["writes"].append(row.fn.__name__)
    loads = set().union(*(tg._loads(st) for st in stmts), set())
    muts = set().union(*(tg._mutation_targets(st) for st in stmts), set())
    via = set().union(*(helper_mut.get(c, set()) for c in loads), set())
    exposed = tg._exposed_reads(stmts, set())[0]
    needs_d = tuple(sorted(((exposed & gate_locals) | (muts & gate_locals) | via) & set(sig)))
    if needs_d != tuple(sorted(row.needs)):
        needs_overrides[row.fn.__name__] = (needs_d, tuple(sorted(row.needs)))
    checks_d, opq = [], 0
    for st in stmts:
        c, o = tg._check_names(st, emissions)
        checks_d += c; opq += o
    if tuple(sorted(set(checks_d))) != tuple(sorted(row.checks)): mm["checks"].append(row.fn.__name__)
    if bool({"_ran", "_waived", "fails"} & loads) != row.meta: mm["meta"].append(row.fn.__name__)
    if bool(opq) != row.always: mm["always"].append(row.fn.__name__)

def nkey(nm):
    m = re.match(r"_seg_(\d+)(?:_(\d+))?", nm)
    return (int(m.group(1)), int(m.group(2)) if m.group(2) else -1)

# auto-discover placements: minimal set whose removal leaves the keys sorted =
# complement of the longest non-decreasing subsequence (the inserts are FEW; keep the many)
import bisect
names = [r.fn.__name__ for r in GATE_SEGMENTS]
keys = [nkey(nm) for nm in names]
tails, tidx, parent = [], [], [None] * len(keys)
for i, k in enumerate(keys):
    j = bisect.bisect_right(tails, k)
    if j == len(tails):
        tails.append(k); tidx.append(i)
    else:
        tails[j] = k; tidx[j] = i
    parent[i] = tidx[j - 1] if j else None
keep = set()
i = tidx[-1]
while i is not None:
    keep.add(i); i = parent[i]
placements = {names[i]: names[i - 1] for i in range(len(names)) if i not in keep}
base = sorted((nm for nm in names if nm not in placements), key=nkey)
order = []
for nm in base:
    order.append(nm)
    order += [ins for ins, anch in placements.items() if anch == nm]
print("PLACEMENTS =", placements)
print("order_reproduced:", order == names)
print("rows:", len(GATE_SEGMENTS), "derive_time:", round(time.perf_counter() - t0, 3))
for k, v in mm.items(): print(k, len(v), v[:6])
print("NEEDS_OVERRIDES rows:", len(needs_overrides))
for nm, (d, r) in needs_overrides.items(): print("  ", nm, "derived:", d, "registry:", r)
meta_d = frozenset(c for r in GATE_SEGMENTS if r.meta for c in r.checks)
print("meta_checks_match:", meta_d == META_CHECKS)

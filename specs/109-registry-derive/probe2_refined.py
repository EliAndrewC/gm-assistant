"""Refined derivation probe: the actual candidate derivation, field by field.
free=signature, writes=return-tuple, needs/checks/meta/always=AST with via_helpers
fixpoint, order=numeric name key + explicit placement overrides for hand-added segs."""

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

from check_village.registry import GATE_SEGMENTS

t0 = time.perf_counter()
segdefs = {}
emissions = {}
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
    assert isinstance(b[-1], ast.Return)
    return b[:-1], b[-1]

# helper_mut fixpoint over nested defs bound to gate-local names
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

mm = {"free": [], "writes": [], "checks": [], "needs": [], "meta": [], "always": []}
for row in GATE_SEGMENTS:
    node = segdefs[row.fn.__name__]
    stmts, ret = body_of(node)
    sig = tuple(a.arg for a in node.args.kwonlyargs)
    free_d = sig
    writes_d = tuple(ast.literal_eval(ret.value.args[1]))
    loads = set().union(*(tg._loads(st) for st in stmts), set())
    muts = set().union(*(tg._mutation_targets(st) for st in stmts), set())
    via = set().union(*(helper_mut.get(c, set()) for c in loads), set())
    exposed = tg._exposed_reads(stmts, set())[0]
    needs_d = tuple(sorted(((exposed & gate_locals) | (muts & gate_locals) | via) & set(sig)))
    checks_d, opaque = [], 0
    for st in stmts:
        c, o = tg._check_names(st, emissions)
        checks_d += c
        opaque += o
    meta_d = bool({"_ran", "_waived", "fails"} & loads)
    always_d = bool(opaque)
    if free_d != row.free: mm["free"].append((row.fn.__name__, free_d, row.free))
    if writes_d != row.writes: mm["writes"].append((row.fn.__name__, writes_d, row.writes))
    if tuple(sorted(set(checks_d))) != tuple(sorted(row.checks)): mm["checks"].append((row.fn.__name__, checks_d, row.checks))
    if needs_d != tuple(sorted(row.needs)): mm["needs"].append((row.fn.__name__, needs_d, row.needs))
    if meta_d != row.meta: mm["meta"].append((row.fn.__name__, meta_d, row.meta))
    if always_d != row.always: mm["always"].append((row.fn.__name__, always_d, row.always))
t_analyze = time.perf_counter() - t0

# order: numeric key sort + placements spliced after an anchor
PLACEMENTS = {  # hand-added segments registered mid-sequence: execution position is a DECISION
    "_seg_0595__paddy_bunds_clear_the_supply_channels": "_seg_0532",
    "_seg_0596__dry_plot_seams_shared": "_seg_0317",
}
def nkey(nm):
    m = re.match(r"_seg_(\d+)(?:_(\d+))?", nm)
    return (int(m.group(1)), int(m.group(2)) if m.group(2) else -1)
placed = {nm for nm in segdefs if any(nm.startswith(k) or nm == k for k in PLACEMENTS)}
base = sorted((nm for nm in segdefs if nm not in PLACEMENTS), key=nkey)
order = []
for nm in base:
    order.append(nm)
    for ins, anchor in PLACEMENTS.items():
        if nm.startswith(anchor):
            order.append(ins)
order = [nm for nm in order if nm not in PLACEMENTS] + []
# rebuild properly: base excludes placements, splice after anchor prefix match
order = []
for nm in base:
    order.append(nm)
    for ins, anchor in PLACEMENTS.items():
        if nkey(nm)[0] == int(anchor.split("_")[-1]) and nkey(nm) == max((nkey(x) for x in base if nkey(x)[0] == nkey(nm)[0])):
            order.append(ins)
reg_order = [r.fn.__name__ for r in GATE_SEGMENTS]
print(f"analyze_s={t_analyze:.3f} helpers={len(helper_mut)}")
for k, v in mm.items():
    print(f"{k}: {len(v)}")
    for e in v[:4]: print("   ", str(e)[:220])
print("order_reproduced:", order == reg_order)
if order != reg_order:
    for i, (a, b) in enumerate(zip(order, reg_order)):
        if a != b:
            print("first divergence at", i, a, "vs", b); break

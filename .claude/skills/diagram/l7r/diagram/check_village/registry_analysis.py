"""AST derivation of the gate registry's row fields (feature 109).

Every `_GateSeg` field is a restatement of facts the `segments_*` modules already carry, so the
registry DERIVES them instead of maintaining them (constitution Principle X clause 14):

- `free` is the segment function's keyword-only parameter tuple - feature 022 GENERATED the
  signatures FROM the analyzed free sets, so the signature is the roster fact itself.
- `writes` is the literal name tuple in the terminal `return _kept(locals(), (...))`.
- `checks` / `needs` / `meta` / `always` re-run the same AST analysis feature 022's transformer
  ran on these exact statement bodies (`specs/022-gate-check-registry/transform_gate.py` is the
  provenance of every function below; the port is verbatim plus strict typing).

The analysis was proven equal to the hand-maintained rows across all 1,371 of them before the
swap (specs/109-registry-derive/research.md, probe scripts alongside it). Two conservatisms are
load-bearing and must not be "simplified" away:

- `_exposed_reads` counts a name as bound only when the binding DEFINITELY executes before the
  read - imprecision must OVER-expose (more dependency edges, less pruning), never under.
- The helper-mutation fixpoint: calling a gate-local helper closure is a write/read of whatever
  that helper mutates (e.g. `_wtr_add` appends into `_wtr` from another segment) - without it a
  targeted run can skip a producer and a check silently sees an empty list.
"""

import ast
from pathlib import Path
from typing import NamedTuple

MUTATORS = {"append", "extend", "add", "update", "insert", "setdefault", "pop", "remove", "sort", "clear", "discard", "appendleft"}

SCALES = ("hamlet", "village", "town", "city", "capital")

META_NAMES = frozenset({"_ran", "_waived", "fails"})


class _DerivationError(RuntimeError):
    """A segment module violates the derivation contract (see the guard tests)."""


class _SegFields(NamedTuple):
    """The six derived metadata fields of one registry row (everything but `fn`)."""

    free: tuple[str, ...]
    writes: tuple[str, ...]
    checks: tuple[str, ...]
    needs: tuple[str, ...]
    meta: bool
    always: bool


def _loads(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def _bound_anywhere(node: ast.AST) -> set[str]:
    """Every name bound at ANY depth under node: stores, def/class names, and - easy to miss -
    function/lambda PARAMETERS, which are bindings but not Name-Store nodes."""
    bound: set[str] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            bound.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(n.name)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = n.args
            for arg in [*a.posonlyargs, *a.args, *a.kwonlyargs, *([a.vararg] if a.vararg else []), *([a.kwarg] if a.kwarg else [])]:
                bound.add(arg.arg)
    return bound


def _mutation_targets(node: ast.AST) -> set[str]:
    out: set[str] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in MUTATORS and isinstance(n.func.value, ast.Name):
            out.add(n.func.value.id)
        elif isinstance(n, (ast.Subscript, ast.Attribute)) and isinstance(n.ctx, (ast.Store, ast.Del)):
            root: ast.expr = n
            while isinstance(root, (ast.Subscript, ast.Attribute)):
                root = root.value
            if isinstance(root, ast.Name):
                out.add(root.id)
        elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
            out.add(n.target.id)
    return out


def _bases_of(a: ast.expr) -> list[str] | None:
    """All check base names an expression can evaluate to, or None if opaque. Handles literals,
    f-strings with a constant prefix, f-strings keyed on the tier (`f"{scale}_..."` expands over
    the five scales), and conditional expressions over resolvable branches."""
    if isinstance(a, ast.Constant) and isinstance(a.value, str):
        return [a.value.split("[")[0]]
    if isinstance(a, ast.IfExp):
        yes, no = _bases_of(a.body), _bases_of(a.orelse)
        return yes + no if yes is not None and no is not None else None
    if isinstance(a, ast.JoinedStr) and a.values:
        first = a.values[0]
        if isinstance(first, ast.Constant):
            return [str(first.value).split("[")[0].rstrip("[")]
        if isinstance(first, ast.FormattedValue) and isinstance(first.value, ast.Name) and first.value.id == "scale":
            suffix = "".join(str(v.value) for v in a.values[1:] if isinstance(v, ast.Constant))
            return [f"{s}{suffix}".split("[")[0] for s in SCALES]
    return None


def _module_emissions(tree: ast.Module) -> dict[str, list[str]]:
    """Check names emitted by module-level HELPERS that receive the check closure as a parameter
    (e.g. check_fire_features(check, ...)). A segment calling such a helper emits its names, which
    a scan for direct check() calls cannot see (the fire_tower_*/theater_stage_* fires come from
    exactly this)."""
    out: dict[str, list[str]] = {}
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef):
            continue
        params = {a.arg for a in [*fn.args.posonlyargs, *fn.args.args, *fn.args.kwonlyargs]}
        names: list[str] = []
        for n in ast.walk(fn):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in params and n.args:
                b = _bases_of(n.args[0])
                if b:
                    names += b
        if names:
            out[fn.name] = sorted(set(names))
    return out


def _check_names(node: ast.AST, emissions: dict[str, list[str]]) -> tuple[list[str], int]:
    """(base names from check() calls, count of opaque ones). A Name argument resolves through a
    same-segment `nm = ...` assignment; calls into emitting module helpers contribute their names;
    anything still opaque makes the segment ALWAYS-RUN in targeted mode (conservative: run more,
    never miss)."""
    assigned: dict[str, list[str]] = {}
    for n in ast.walk(node):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            b = _bases_of(n.value)
            if b is not None:
                assigned[n.targets[0].id] = b
    bases: list[str] = []
    opaque = 0
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            if n.func.id in emissions:
                bases += emissions[n.func.id]
            if n.func.id == "check" and n.args:
                a = n.args[0]
                b = _bases_of(a)
                if b is None and isinstance(a, ast.Name):
                    b = assigned.get(a.id)
                if b is not None:
                    bases += b
                else:
                    opaque += 1
    return bases, opaque


def _targets_of(t: ast.expr) -> set[str]:
    return {n.id for n in ast.walk(t) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}


def _free_loads(node: ast.AST) -> set[str]:
    """Loads of an EXPRESSION minus names the expression itself binds (comprehension targets,
    lambda params). Raw _loads counted `[.. for c in xs]`'s own uses of `c` as reads of the OUTER
    `c`, which made every generic loop-variable name a dependency hub chaining ~70% of the gate
    into every 'targeted' closure. Comprehension targets are their own scope in Python 3, so
    excluding them is exact; the one approximation (a name used BOTH as an outer read and a
    comprehension target inside one expression would be under-exposed) is a shape the house style
    never uses, and the fixture-equality guard is the empirical backstop that it stays absent."""
    loads: set[str] = set()
    bound: set[str] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            loads.add(n.id)
        elif isinstance(n, ast.Lambda):
            a = n.args
            for arg in [*a.posonlyargs, *a.args, *a.kwonlyargs, *([a.vararg] if a.vararg else []), *([a.kwarg] if a.kwarg else [])]:
                bound.add(arg.arg)
        elif isinstance(n, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            for gen in n.generators:
                bound |= _targets_of(gen.target)
    return loads - bound


def _exposed_reads(stmts: list[ast.stmt], bound: set[str]) -> tuple[set[str], set[str]]:
    """(UPWARD-EXPOSED loads, names definitely bound after) for a statement sequence: what it can
    READ before it definitely binds it - the true meaning of a dependency edge. Imprecision must
    OVER-expose (more edges, less pruning), never under: a name counts as bound only when the
    binding DEFINITELY executes before the read."""
    exposed: set[str] = set()
    bound = set(bound)
    for st in stmts:
        if isinstance(st, ast.Assign):
            exposed |= _free_loads(st.value) - bound
            for t in st.targets:
                if not isinstance(t, ast.Name):
                    exposed |= {nm for tt in ast.walk(t) if isinstance(tt, (ast.Subscript, ast.Attribute)) for nm in _free_loads(tt)} - bound
                if isinstance(t, ast.Name):
                    bound.add(t.id)
                elif isinstance(t, (ast.Tuple, ast.List)) and all(isinstance(e, (ast.Name, ast.Starred)) for e in t.elts):
                    bound |= _targets_of(t)
        elif isinstance(st, ast.AnnAssign) and st.value is not None and isinstance(st.target, ast.Name):
            exposed |= _free_loads(st.value) - bound
            bound.add(st.target.id)
        elif isinstance(st, ast.AugAssign):
            exposed |= (_free_loads(st) | ({st.target.id} if isinstance(st.target, ast.Name) else set())) - bound
            if isinstance(st.target, ast.Name):
                bound.add(st.target.id)
        elif isinstance(st, ast.FunctionDef):
            exposed |= (_loads(st) - _bound_anywhere(st)) - bound
            bound.add(st.name)
        elif isinstance(st, ast.For):
            exposed |= _free_loads(st.iter) - bound
            body_exp, _ = _exposed_reads(st.body, bound | _targets_of(st.target))
            else_exp, _ = _exposed_reads(st.orelse, bound)
            exposed |= body_exp | else_exp
        elif isinstance(st, ast.While):
            exposed |= _free_loads(st.test) - bound
            body_exp, _ = _exposed_reads(st.body, bound)
            else_exp, _ = _exposed_reads(st.orelse, bound)
            exposed |= body_exp | else_exp
        elif isinstance(st, ast.If):
            exposed |= _free_loads(st.test) - bound
            body_exp, body_bound = _exposed_reads(st.body, bound)
            else_exp, else_bound = _exposed_reads(st.orelse, bound)
            exposed |= body_exp | else_exp
            if st.orelse:  # a name bound in BOTH branches is definitely bound after the if
                bound |= body_bound & else_bound
        elif isinstance(st, ast.With):
            for item in st.items:
                exposed |= _free_loads(item.context_expr) - bound
                if item.optional_vars is not None:
                    bound |= _targets_of(item.optional_vars)
            body_exp, body_bound = _exposed_reads(st.body, bound)
            exposed |= body_exp
            bound |= body_bound
        elif isinstance(st, ast.Try):
            for blk in (st.body, *[h.body for h in st.handlers], st.orelse, st.finalbody):
                blk_exp, _ = _exposed_reads(blk, bound)
                exposed |= blk_exp
        else:
            exposed |= _free_loads(st) - bound
    return exposed, bound


def _segment_parts(node: ast.FunctionDef) -> tuple[list[ast.stmt], tuple[str, ...]]:
    """(body statements sans docstring and terminal return, the literal writes tuple).

    Enforces the segment shape contract (data-model rule 1): every `_seg_*` function must end
    with `return _kept(locals(), (<string literal tuple>))` - the writes fact lives in that
    literal, so a non-conforming segment fails HERE at derive time instead of mis-deriving."""
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    ret = body[-1] if body else None
    if not isinstance(ret, ast.Return) or not isinstance(ret.value, ast.Call) or not isinstance(ret.value.func, ast.Name) or ret.value.func.id != "_kept" or len(ret.value.args) != 2:
        raise _DerivationError(f"{node.name}: segment must end with `return _kept(locals(), (<names>))`")
    try:
        writes = tuple(ast.literal_eval(ret.value.args[1]))
    except ValueError as exc:
        raise _DerivationError(f"{node.name}: _kept names tuple must be a literal") from exc
    if not all(isinstance(w, str) for w in writes):
        raise _DerivationError(f"{node.name}: _kept names must all be strings")
    return body[:-1], writes


def _derive_fields(pkg_dir: Path) -> dict[str, _SegFields]:
    """Derive every row's six metadata fields from the package sources. Pure: reads files, holds
    no state, imports nothing - the caller binds actual function objects by name."""
    trees = [ast.parse(f.read_text()) for f in sorted(pkg_dir.glob("*.py"))]
    emissions: dict[str, list[str]] = {}
    for tree in trees:
        emissions.update(_module_emissions(tree))
    segdefs: dict[str, ast.FunctionDef] = {}
    for tree in trees:
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("_seg_"):
                if node.name in segdefs:
                    raise _DerivationError(f"duplicate segment name {node.name}")
                segdefs[node.name] = node
    parts = {nm: _segment_parts(d) for nm, d in segdefs.items()}
    sigs = {nm: tuple(a.arg for a in d.args.kwonlyargs) for nm, d in segdefs.items()}
    gate_locals = {n for sig in sigs.values() for n in sig} | {n for _, w in parts.values() for n in w}

    # helper-mutation fixpoint: a nested def bound to a gate-local name mutates gate locals;
    # helpers calling helpers close transitively (see module docstring for why this is mandatory)
    helper_mut: dict[str, set[str]] = {}
    for stmts, _ in parts.values():
        for st in stmts:
            for n in ast.walk(st):
                if isinstance(n, ast.FunctionDef) and n.name in gate_locals:
                    helper_mut[n.name] = (_mutation_targets(n) - _bound_anywhere(n)) & gate_locals
    for _ in range(len(helper_mut) + 1):
        changed = False
        for stmts, _ in parts.values():
            for st in stmts:
                for n in ast.walk(st):
                    if isinstance(n, ast.FunctionDef) and n.name in helper_mut:
                        via = set().union(*(helper_mut.get(c, set()) for c in _loads(n)), set()) - _bound_anywhere(n)
                        if not via <= helper_mut[n.name]:
                            helper_mut[n.name] |= via
                            changed = True
        if not changed:
            break

    out: dict[str, _SegFields] = {}
    for nm, (stmts, writes) in parts.items():
        loads = set().union(*(_loads(st) for st in stmts), set())
        muts = set().union(*(_mutation_targets(st) for st in stmts), set())
        via = set().union(*(helper_mut.get(c, set()) for c in loads), set())
        exposed = _exposed_reads(stmts, set())[0]
        needs = tuple(sorted(((exposed & gate_locals) | (muts & gate_locals) | via) & set(sigs[nm])))
        checks: list[str] = []
        opaque = 0
        for st in stmts:
            c, o = _check_names(st, emissions)
            checks += c
            opaque += o
        out[nm] = _SegFields(
            free=sigs[nm],
            writes=writes,
            checks=tuple(sorted(set(checks))),
            needs=needs,
            meta=bool(META_NAMES & loads),
            always=bool(opaque),
        )
    return out

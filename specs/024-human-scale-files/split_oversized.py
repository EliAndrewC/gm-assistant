#!/usr/bin/env python3
"""One-shot transformer for feature 024: split the oversized multi-check gate segments (census in
research.md R3 - led by _seg_0285__wells_clear_of_shrine_and_torii, 1,351 lines / 42 check names)
into per-statement segments spliced at each original's GATE_SEGMENTS position.

    python3 split_oversized.py census      # analyze only; print stats, hard-fail on model violations
    python3 split_oversized.py generate    # rewrite check_village.py (refuses to run twice)

Model (023's, generalized): each target is a 022-generated segment - keyword params defaulting to
_UNBOUND, an optional docstring, ONE guarded `if <test>:` statement, and a final
`return _kept(locals(), writes)`. The guard's body statements are flattened in textual order into
spans; a no-orelse inner If whose body exceeds BIG_IF stmt-units is flattened one level deeper
(0285 has a 372-unit inner; 0562 a 96-unit one), recursively. Bodies move VERBATIM with ZERO
re-indentation: a span at guard depth d is emitted under a scaffold of its d re-evaluated guard
tests, which reproduces the source indentation exactly. Guard re-evaluation is sound iff no span
AT OR AFTER a guard's first use stores/mutates any of the guard's free names - hard-failed by the
census (a guard name like 0562's `_ty_yards` is PRODUCED by earlier spans in the same region;
stores strictly before the guard's first use are the producer and are fine).

Dataflow (free/writes/needs, helper-mutation fixpoint, upward-exposed reads, check-name
extraction) is IMPORTED from specs/022-gate-check-registry/transform_gate.py - the code the
791-fixture sweeps validated against the three documented holes (022 research.md R9). Stale-cell
hazards (a nested helper def split away from a later rebind of one of its free names, referenced
after the rebind) are resolved by MERGING the offending consecutive same-guard-path spans into
one segment - verbatim-safe by construction - iterated to a fixpoint (023's rule).

Like 022/023, this tool is retired the moment the transform lands; check_village stays the
hand-maintained truth. Never hand-edit generated bodies during the feature - fix this tool,
restore the pre-split file, and re-run.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import statistics
import sys
from dataclasses import dataclass, field

HERE = __import__("os").path.dirname(__import__("os").path.abspath(__file__))
REPO = __import__("os").path.dirname(__import__("os").path.dirname(HERE))
SKILL = f"{REPO}/.claude/skills/diagram"
CHECK_VILLAGE = f"{SKILL}/check_village.py"
BIG_IF = 60  # stmt-units past which a no-orelse inner If is flattened rather than moved whole

# research.md R3 census: every segment >= 300 raw lines; all are multi-check bundles.
# _seg_0133 (289 lines, 6 checks) included per tasks.md T006 - same shape, same method.
TARGETS = [
    "_seg_0040__city_commoner_dwellings_inside_walls",
    "_seg_0106__capital_declares_a_budget",
    "_seg_0133__outside_fields_farmhouse_density",
    "_seg_0285__wells_clear_of_shrine_and_torii",
    "_seg_0286__cemetery_clear_of_shrine",
    "_seg_0438__near_ring_cultivated_fraction",
    "_seg_0523__drain_flows_downhill",
    "_seg_0543__town_farmers_plurality",
    "_seg_0555__punishment_spot_in_the_core",
    "_seg_0562__settlement_has_tanning_yard",
]

_spec = importlib.util.spec_from_file_location("transform_gate", f"{REPO}/specs/022-gate-check-registry/transform_gate.py")
tg = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["transform_gate"] = tg  # 3.14 dataclasses resolve cls.__module__ via sys.modules
_spec.loader.exec_module(tg)  # type: ignore[union-attr]

sys.path.insert(0, SKILL)


@dataclass
class Span:
    """One or more CONSECUTIVE same-guard-path statements that become one new segment
    (>1 statement only when the stale-cell census forced a merge)."""

    idx: int
    guards: tuple[str, ...]
    stmts: list[ast.stmt]
    free: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    checks: tuple[str, ...] = ()
    needs: tuple[str, ...] = ()
    always: bool = False
    name: str = ""


@dataclass
class Target:
    """One oversized segment and its computed replacement spans."""

    seg_name: str
    fn: ast.FunctionDef
    row_call: ast.Call
    spans: list[Span] = field(default_factory=list)


def _body_region(fn: ast.FunctionDef) -> ast.If:
    body = list(fn.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    assert body and isinstance(body[-1], ast.Return) and ast.unparse(body[-1]).startswith("return _kept(locals()"), f"{fn.name}: body shape drifted from the 022 form"
    assert len(body) == 2 and isinstance(body[0], ast.If) and not body[0].orelse, f"{fn.name}: expected exactly one guarded If before the return"
    return body[0]


def _flatten(outer: ast.If) -> list[tuple[tuple[str, ...], ast.stmt]]:
    """Textual-order flattening; descend into no-orelse Ifs bigger than BIG_IF stmt-units."""
    out: list[tuple[tuple[str, ...], ast.stmt]] = []

    def walk(stmts: list[ast.stmt], guards: tuple[str, ...]) -> None:
        for s in stmts:
            if isinstance(s, ast.If) and not s.orelse and sum(1 for x in ast.walk(s) if isinstance(x, ast.stmt)) > BIG_IF:
                walk(s.body, guards + (ast.unparse(s.test),))
            else:
                out.append((guards, s))

    walk(outer.body, (ast.unparse(outer.test),))
    return out


def _census_hard_fails(seg: str, flat: list[tuple[tuple[str, ...], ast.stmt]], gate_locals: set[str]) -> None:
    problems: list[str] = []
    # guard stability: from a guard's first use onward, its free names are never stored/mutated
    first_use: dict[str, int] = {}
    for k, (guards, _) in enumerate(flat):
        for g in guards:
            first_use.setdefault(g, k)
    guard_frees = {g: tg._loads(ast.parse(g, mode="eval")) for g in first_use}
    for k, (_, s) in enumerate(flat):
        touched = tg._stores(s, into_defs=False) | tg._mutation_targets(s)
        for g, p in first_use.items():
            if k >= p and (bad := touched & guard_frees[g]):
                problems.append(f"{seg}: guard name(s) {sorted(bad)} of {g!r} stored/mutated at line {s.lineno} at/after the guard's first use")
        for n in tg._walk_shallow(s):
            if isinstance(n, ast.Return):
                problems.append(f"{seg}: return inside the region at line {n.lineno}")
            if isinstance(n, ast.Delete):
                problems.append(f"{seg}: del at line {n.lineno}")
        for n in ast.walk(s):
            if isinstance(n, (ast.Global, ast.Nonlocal)):
                problems.append(f"{seg}: global/nonlocal at line {n.lineno}")
        unstripped = tg._stores(s, into_defs=False) - gate_locals
        if unstripped:
            problems.append(f"{seg}: store(s) {sorted(unstripped)} at line {s.lineno} not in the registry row vocabulary - row.writes is stale")
    if problems:
        raise SystemExit("CENSUS HARD-FAIL:\n  " + "\n  ".join(problems))


def _merge_hazard_spans(spans: list[Span], gate_locals: set[str]) -> tuple[list[Span], list[str]]:
    """023's rule: no nested helper def may be separated from a later rebind of one of its free
    names that precedes a later reference. Merges must not cross a guard-path boundary."""
    log: list[str] = []
    while True:
        stores = [set().union(*(tg._stores(s, into_defs=False) for s in sp.stmts)) for sp in spans]
        loads = [set().union(*(tg._loads(s) for s in sp.stmts)) for sp in spans]
        merge: tuple[int, int] | None = None
        for i, sp in enumerate(spans):
            for s in sp.stmts:
                for n in ast.walk(s):
                    if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    free = (tg._loads(n) - tg._bound_anywhere(n)) & gate_locals
                    rebinds = [j for j in range(i + 1, len(spans)) if free & stores[j]]
                    hazardous = [r for r in rebinds if any(n.name in loads[c] for c in range(r, len(spans)) if c != i)]
                    if hazardous:
                        merge = (i, max(hazardous))
                        log.append(f"MERGE spans {i}-{max(hazardous)}: helper '{n.name}' (line {n.lineno}) frees {sorted(free & set().union(*(stores[j] for j in hazardous)))} rebound before a later reference")
                        break
                if merge:
                    break
            if merge:
                break
        if merge is None:
            for i, sp in enumerate(spans):
                for s in sp.stmts:
                    for n in ast.walk(s):
                        if isinstance(n, ast.Lambda):
                            stale = (tg._loads(n) - tg._bound_anywhere(n)) & gate_locals & set().union(*stores[i + 1 :], set())
                            if stale:
                                log.append(f"WARN lambda at line {n.lineno} freezes {sorted(stale)} - verify it never escapes its span (022 precedent: all such lambdas were consumed in-span)")
            return spans, log
        a, b = merge
        if len({spans[j].guards for j in range(a, b + 1)}) != 1:
            raise SystemExit(f"CENSUS HARD-FAIL: hazard merge {a}-{b} crosses a guard-path boundary; needs a hand decision")
        merged = Span(a, spans[a].guards, [st for j in range(a, b + 1) for st in spans[j].stmts])
        spans = spans[:a] + [merged] + spans[b + 1 :]


def _analyze_target(tree: ast.Module, emissions, cv, seg_name: str, log: list[str]) -> Target:
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == seg_name)
    row = next(r for r in cv.GATE_SEGMENTS if r.fn.__name__ == seg_name)
    assert not row.meta, f"{seg_name} is a meta segment - out of the model"
    assign = next(n for n in tree.body if isinstance(n, (ast.Assign, ast.AnnAssign)) and "GATE_SEGMENTS" in ast.unparse(n).split("=")[0])
    row_call = next(c for c in ast.walk(assign) if isinstance(c, ast.Call) and c.args and isinstance(c.args[0], ast.Name) and c.args[0].id == seg_name)

    gate_locals = set(row.free) | set(row.writes)
    flat = _flatten(_body_region(fn))
    _census_hard_fails(seg_name, flat, gate_locals)

    spans = [Span(i, g, [s]) for i, (g, s) in enumerate(flat)]
    spans, mlog = _merge_hazard_spans(spans, gate_locals)
    log += [f"{seg_name}: {m}" for m in mlog]

    # helper-mutation fixpoint (022 R9 rule 1): calling a gate-local helper counts as writing
    # (and needing) everything it transitively mutates
    helper_mut: dict[str, set[str]] = {}
    region_defs = [n for _, s in flat for n in ast.walk(s) if isinstance(n, ast.FunctionDef)]
    for n in region_defs:
        helper_mut[n.name] = (tg._mutation_targets(n) - tg._bound_anywhere(n)) & gate_locals
    for _ in range(len(helper_mut) + 1):
        changed = False
        for n in region_defs:
            via = set().union(*(helper_mut.get(c, set()) for c in tg._loads(n)), set()) - tg._bound_anywhere(n)
            if not via <= helper_mut[n.name]:
                helper_mut[n.name] |= via
                changed = True
        if not changed:
            break

    base = seg_name.split("__")[0]  # e.g. _seg_0285
    used: dict[str, int] = {}
    all_checks: list[str] = []
    all_writes: set[str] = set()
    for k, sp in enumerate(spans):
        sp.idx = k
        guard_reads = set().union(*(tg._loads(ast.parse(g, mode="eval")) for g in sp.guards), set())
        assert guard_reads <= gate_locals, f"{seg_name} span {k}: guard reads {sorted(guard_reads - gate_locals)} outside the row vocabulary"
        loads = set().union(*(tg._loads(s) for s in sp.stmts))
        muts = set().union(*(tg._mutation_targets(s) for s in sp.stmts)) & gate_locals
        via: set[str] = set().union(*(helper_mut.get(c, set()) for c in loads), set())
        stores = set().union(*(tg._stores(s, into_defs=False) for s in sp.stmts))
        free = (loads & gate_locals) | muts | via | guard_reads
        writes = stores | muts | via
        exposed, _ = tg._exposed_reads(list(sp.stmts), set())
        needs = ((exposed & gate_locals) | muts | via | guard_reads) & free
        checks: list[str] = []
        opaque = 0
        for s in sp.stmts:
            c, o = tg._check_names(s, emissions)
            checks += c
            opaque += o
        all_checks += checks
        all_writes |= writes
        assert not ({"_ran", "_waived", "fails"} & loads), f"{seg_name} span {k} reads run state - meta segments cannot appear here"
        slug = re.sub(r"\W+", "_", (checks[0] if checks else (sorted(writes)[0] if writes else "stmt")))[:48]
        n_used = used.get(slug, 0)
        used[slug] = n_used + 1
        sp.free, sp.writes, sp.checks = tuple(sorted(free)), tuple(sorted(writes)), tuple(sorted(set(checks)))
        sp.needs, sp.always = tuple(sorted(needs)), bool(opaque) or bool(row.always)
        sp.name = f"{base}_{k:03d}__{slug}" + (f"_{n_used}" if n_used else "")

    if set(all_checks) != set(row.checks):
        raise SystemExit(f"CENSUS HARD-FAIL: {seg_name} check-name union mismatch: missing={sorted(set(row.checks) - set(all_checks))} extra={sorted(set(all_checks) - set(row.checks))}")
    if not all_writes >= set(row.writes):
        raise SystemExit(f"CENSUS HARD-FAIL: {seg_name} lost writes {sorted(set(row.writes) - all_writes)}")
    return Target(seg_name, fn, row_call, spans)


def analyze() -> tuple[str, list[Target], list[str]]:
    src = open(CHECK_VILLAGE).read()
    if any(f"{t.split('__')[0]}_000__" in src for t in TARGETS):
        raise SystemExit("already transformed (found a _seg_NNNN_000__* name) - this tool runs once, from the pre-split file")
    tree = ast.parse(src)
    import check_village as cv

    emissions = tg._module_emissions(tree)
    log: list[str] = []
    targets = [_analyze_target(tree, emissions, cv, t, log) for t in TARGETS]
    return src, targets, log


def _span_lines(lines: list[str], sp: Span) -> str:
    return "".join(lines[sp.stmts[0].lineno - 1 : sp.stmts[-1].end_lineno])


def _gap(lines: list[str], prev_end: int, start: int) -> str:
    import textwrap

    gap = "".join(lines[prev_end:start])
    if not gap.strip():
        return ""
    assert all(ln.lstrip().startswith("#") or not ln.strip() for ln in gap.splitlines()), f"non-comment gap lines before line {start + 1}"
    return "\n\n" + textwrap.dedent(gap).strip("\n") + "\n"


def _render_target(lines: list[str], t: Target) -> tuple[str, str]:
    """(replacement text for the function's line range, replacement text for its registry row)."""
    out: list[str] = []
    prev_end: dict[tuple[str, ...], int] = {}
    for sp in t.spans:
        start = sp.stmts[0].lineno - 1
        out.append(_gap(lines, prev_end.get(sp.guards, start), start))
        prev_end[sp.guards] = sp.stmts[-1].end_lineno
        params = ", ".join(f"{n}: Any = _UNBOUND" for n in sp.free)
        label = ", ".join(sp.checks) or ", ".join(sp.writes[:4]) or "derivation"
        num = t.seg_name.split("__")[0].removeprefix("_seg_")
        out.append(f"\n\ndef {sp.name}(*, {params}) -> dict[str, Any]:\n")
        out.append(f'    """Gate segment {num}.{sp.idx:03d} ({label}) - body verbatim from {t.seg_name} (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""\n')
        for d, g in enumerate(sp.guards):
            out.append("    " * (d + 1) + f"if {g}:\n")
        out.append(_span_lines(lines, sp))
        out.append(f"    return _kept(locals(), {sp.writes!r})\n")
    rows = "".join(f"    _GateSeg({sp.name}, {sp.free!r}, {sp.writes!r}, {sp.checks!r}, {sp.needs!r}, False, {sp.always!r}),\n" for sp in t.spans)
    return "".join(out).lstrip("\n") + "\n", rows


def generate() -> None:
    src, targets, log = analyze()
    for entry in log:
        print(entry)
    lines = src.splitlines(keepends=True)
    patches: list[tuple[int, int, str]] = []
    for t in targets:
        fn_text, rows = _render_target(lines, t)
        patches.append((t.fn.lineno - 1, t.fn.end_lineno, fn_text))
        patches.append((t.row_call.lineno - 1, t.row_call.end_lineno, rows))
    patches.sort()
    for i in range(1, len(patches)):
        assert patches[i - 1][1] <= patches[i][0], "overlapping patches"
    text_parts: list[str] = []
    pos = 0
    for start, end, repl in patches:
        text_parts.append("".join(lines[pos:start]))
        text_parts.append(repl)
        pos = end
    text_parts.append("".join(lines[pos:]))
    open(CHECK_VILLAGE, "w").write("".join(text_parts))
    n = sum(len(t.spans) for t in targets)
    print(f"wrote {CHECK_VILLAGE}: {n} segments replacing {len(targets)} oversized ones")
    tg._inject_type_ignores()


def census() -> None:
    _, targets, log = analyze()
    for entry in log:
        print(entry)
    import json

    for t in targets:
        sizes = [sum(1 for s in sp.stmts for x in ast.walk(s) if isinstance(x, ast.stmt)) for sp in t.spans]
        print(json.dumps({"seg": t.seg_name, "lines": t.fn.end_lineno - t.fn.lineno + 1, "spans": len(t.spans), "stmt_median": statistics.median(sizes), "stmt_max": max(sizes), "depth_max": max(len(sp.guards) for sp in t.spans), "checks": len({c for sp in t.spans for c in sp.checks}), "merged": [(sp.name, len(sp.stmts)) for sp in t.spans if len(sp.stmts) > 1]}))
    print(f"TOTAL new segments: {sum(len(t.spans) for t in targets)} replacing {len(targets)}")


if __name__ == "__main__":
    {"census": census, "generate": generate}[sys.argv[1]]()

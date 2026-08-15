#!/usr/bin/env python3
"""One-shot transformer for feature 023: split _seg_0563__city_has_six_ministries (the city/
capital urban battery: 1,040 logical statements, 148 check names - the only clause-12 debt left
after feature 022) into per-statement segments in the same GATE_SEGMENTS position.

    python3 split_megaseg.py census      # analyze only; print stats, hard-fail on model violations
    python3 split_megaseg.py generate    # rewrite check_village.py (refuses to run twice)

Model (research.md R2-R4): the mega-segment's body is exactly (docstring, one
`if scale in ('city', 'capital'):` statement, `return _kept(...)`). Its if-body's 83 top-level
statements - one of which is a 295-statement `if meta.get('walled'):` block - are flattened in
textual order into SubSegs. Bodies are emitted VERBATIM with ZERO re-indentation: an outer
statement (source indent 8) sits under `if scale in ('city', 'capital'):` (guard at indent 4,
body at 8); a walled statement (source indent 12) sits under that guard plus a nested
`if meta.get('walled'):` (body at 12). Guard re-evaluation is sound because the census hard-fails
if `scale` or `meta` is ever rebound or mutated in the region (R3).

Stale-cell hazards (a nested helper def split away from a later rebind of one of its free names,
referenced after the rebind) are resolved by MERGING the offending span of consecutive same-guard
statements into one segment - verbatim-safe by construction - iterated to a fixpoint.

Dataflow analysis is IMPORTED from specs/022-gate-check-registry/transform_gate.py (the code the
791-fixture sweeps validated against the three documented holes), never copied. Like 022, this
tool is retired the moment the transform lands; check_village.py stays the hand-maintained truth.
Never hand-edit generated bodies during the feature - fix this tool, restore the pre-split file,
and re-run.
"""

from __future__ import annotations

import ast
import importlib.util
import statistics
import sys
from dataclasses import dataclass

HERE = __import__("os").path.dirname(__import__("os").path.abspath(__file__))
REPO = __import__("os").path.dirname(__import__("os").path.dirname(HERE))
SKILL = f"{REPO}/.claude/skills/diagram"
CHECK_VILLAGE = f"{SKILL}/check_village.py"
MEGA = "_seg_0563__city_has_six_ministries"
OUTER_GUARD = "scale in ('city', 'capital')"
WALLED_GUARD = "meta.get('walled')"

_spec = importlib.util.spec_from_file_location("transform_gate", f"{REPO}/specs/022-gate-check-registry/transform_gate.py")
tg = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["transform_gate"] = tg  # 3.14 dataclasses resolve cls.__module__ via sys.modules
_spec.loader.exec_module(tg)  # type: ignore[union-attr]

sys.path.insert(0, SKILL)


@dataclass
class Span:
    """One or more CONSECUTIVE same-guard statements that become one segment (data-model.md
    SubSeg; >1 statement only when the stale-cell census forced a merge)."""

    idx: int
    walled: bool
    stmts: list[ast.stmt]
    free: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    checks: tuple[str, ...] = ()
    needs: tuple[str, ...] = ()
    always: bool = False
    name: str = ""


def _region(tree: ast.Module) -> tuple[ast.FunctionDef, ast.If, ast.If]:
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == MEGA)
    assert len(fn.body) == 3 and isinstance(fn.body[1], ast.If) and isinstance(fn.body[2], ast.Return), "mega body shape drifted from the R1 census (docstring, one if, return)"
    outer = fn.body[1]
    assert ast.unparse(outer.test) == OUTER_GUARD and not outer.orelse
    walled = next(s for s in outer.body if isinstance(s, ast.If) and ast.unparse(s.test) == WALLED_GUARD)
    assert not walled.orelse
    return fn, outer, walled


def _flatten(outer: ast.If, walled: ast.If) -> list[tuple[bool, ast.stmt]]:
    out: list[tuple[bool, ast.stmt]] = []
    for s in outer.body:
        if s is walled:
            out += [(True, w) for w in walled.body]
        else:
            out.append((False, s))
    return out


def _census_hard_fails(flat: list[tuple[bool, ast.stmt]], gate_locals: set[str]) -> None:
    problems: list[str] = []
    for _, s in flat:
        for n in tg._walk_shallow(s):
            if isinstance(n, ast.Return):
                problems.append(f"return inside the region at line {n.lineno}")
            if isinstance(n, ast.Delete):
                problems.append(f"del at line {n.lineno}")
        for n in ast.walk(s):
            if isinstance(n, (ast.Global, ast.Nonlocal)):
                problems.append(f"global/nonlocal at line {n.lineno}")
        # R3: guard re-evaluation is sound only while scale/meta are never rebound or mutated
        touched = (tg._stores(s, into_defs=False) | tg._mutation_targets(s)) & {"scale", "meta"}
        if touched:
            problems.append(f"guard name(s) {sorted(touched)} rebound/mutated at line {s.lineno} - R3 fallback (hoisted provider) required")
        unstripped = tg._stores(s, into_defs=False) - gate_locals
        if unstripped:
            problems.append(f"store(s) {sorted(unstripped)} at line {s.lineno} not in the registry row vocabulary - row.writes is stale")
    if problems:
        raise SystemExit("CENSUS HARD-FAIL:\n  " + "\n  ".join(problems))


def _merge_hazard_spans(spans: list[Span], gate_locals: set[str]) -> tuple[list[Span], list[str]]:
    """Iteratively merge spans so no nested helper def is separated from a later rebind of one of
    its free names that precedes a later reference (research.md R4). Returns (spans, log)."""
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
        span_kinds = {spans[j].walled for j in range(a, b + 1)}
        if len(span_kinds) != 1:
            raise SystemExit(f"CENSUS HARD-FAIL: hazard merge {a}-{b} crosses the walled-guard boundary; needs a hand decision")
        merged = Span(a, spans[a].walled, [st for j in range(a, b + 1) for st in spans[j].stmts])
        spans = spans[:a] + [merged] + spans[b + 1 :]


def analyze() -> tuple[str, list[Span], list[str]]:
    src = open(CHECK_VILLAGE).read()
    if "_seg_0563_000__" in src:
        raise SystemExit("already transformed (found _seg_0563_000__*) - this tool runs once, from the pre-split file")
    tree = ast.parse(src)
    import check_village as cv

    row = next(r for r in cv.GATE_SEGMENTS if r.fn.__name__ == MEGA)
    assert not row.meta and not row.always
    gate_locals = set(row.free) | set(row.writes)
    fn, outer, walled = _region(tree)
    flat = _flatten(outer, walled)
    _census_hard_fails(flat, gate_locals)

    spans = [Span(i, w, [s]) for i, (w, s) in enumerate(flat)]
    spans, log = _merge_hazard_spans(spans, gate_locals)

    # helper-mutation fixpoint over the region's nested defs (022 R3 rule 1, one level deeper):
    # calling a helper counts as writing (and needing) everything it transitively mutates
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

    emissions = tg._module_emissions(tree)
    used: dict[str, int] = {}
    all_checks: list[str] = []
    for k, sp in enumerate(spans):
        sp.idx = k
        guard_reads = {"scale"} | ({"meta"} if sp.walled else set())
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
        assert not ({"_ran", "_waived", "fails"} & loads), f"span {k} reads run state - meta segments cannot appear here"
        slug = __import__("re").sub(r"\W+", "_", (checks[0] if checks else (sorted(writes)[0] if writes else "stmt")))[:48]
        n_used = used.get(slug, 0)
        used[slug] = n_used + 1
        sp.free, sp.writes, sp.checks = tuple(sorted(free)), tuple(sorted(writes)), tuple(sorted(set(checks)))
        sp.needs, sp.always = tuple(sorted(needs)), bool(opaque)
        sp.name = f"_seg_0563_{k:03d}__{slug}" + (f"_{n_used}" if n_used else "")

    if set(all_checks) != set(row.checks):
        raise SystemExit(f"CENSUS HARD-FAIL: check-name union mismatch: missing={sorted(set(row.checks) - set(all_checks))} extra={sorted(set(all_checks) - set(row.checks))}")
    return src, spans, log


def _span_lines(lines: list[str], sp: Span) -> str:
    return "".join(lines[sp.stmts[0].lineno - 1 : sp.stmts[-1].end_lineno])


def _gap(lines: list[str], prev_end: int, start: int, dedent_ok: bool = True) -> str:
    import textwrap

    gap = "".join(lines[prev_end:start])
    if not gap.strip():
        return ""
    assert all(ln.lstrip().startswith("#") or not ln.strip() for ln in gap.splitlines()), f"non-comment gap lines before line {start + 1}"
    return "\n\n" + textwrap.dedent(gap).strip("\n") + "\n"


def generate() -> None:
    src, spans, log = analyze()
    for entry in log:
        print(entry)
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)
    fn, outer, walled = _region(tree)

    out: list[str] = []
    prev_end = {False: outer.body[0].lineno - 1, True: walled.body[0].lineno - 1}
    for sp in spans:
        out.append(_gap(lines, prev_end[sp.walled], sp.stmts[0].lineno - 1))
        prev_end[sp.walled] = sp.stmts[-1].end_lineno
        params = ", ".join(f"{n}: Any = _UNBOUND" for n in sp.free)
        label = ", ".join(sp.checks) or ", ".join(sp.writes[:4]) or "derivation"
        out.append(f"\n\ndef {sp.name}(*, {params}) -> dict[str, Any]:\n")
        out.append(f'    """Gate segment 563.{sp.idx:03d} ({label}) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""\n')
        if sp.walled:
            out.append(f"    if {OUTER_GUARD}:\n        if {WALLED_GUARD}:\n")
        else:
            out.append(f"    if {OUTER_GUARD}:\n")
        out.append(_span_lines(lines, sp))
        out.append(f"    return _kept(locals(), {sp.writes!r})\n")

    rows = "".join(f"    _GateSeg({sp.name}, {sp.free!r}, {sp.writes!r}, {sp.checks!r}, {sp.needs!r}, False, {sp.always!r}),\n" for sp in spans)

    # find the registry row lines for the mega entry
    assign = next(n for n in tree.body if isinstance(n, (ast.Assign, ast.AnnAssign)) and "GATE_SEGMENTS" in ast.unparse(n).split("=")[0])
    row_call = next(c for c in ast.walk(assign) if isinstance(c, ast.Call) and c.args and isinstance(c.args[0], ast.Name) and c.args[0].id == MEGA)

    fn_start, fn_end = fn.lineno - 1, fn.end_lineno  # 0-based slice bounds
    row_start, row_end = row_call.lineno - 1, row_call.end_lineno
    # the row line ends with "),\n" - the Call's end excludes the trailing comma; replace whole lines
    assert fn_end < row_start
    text = "".join(lines[:fn_start]) + "".join(out).lstrip("\n") + "\n" + "".join(lines[fn_end:row_start]) + rows + "".join(lines[row_end:])
    open(CHECK_VILLAGE, "w").write(text)
    print(f"wrote {CHECK_VILLAGE}: {len(spans)} segments replacing {MEGA}")
    tg._inject_type_ignores()


def census() -> None:
    _, spans, log = analyze()
    for entry in log:
        print(entry)
    sizes = [sum(1 for s in sp.stmts for x in ast.walk(s) if isinstance(x, ast.stmt)) for sp in spans]
    print(f"spans: {len(spans)} ({sum(1 for sp in spans if sp.walled)} walled) | stmt sizes: median {statistics.median(sizes)} p90 {sorted(sizes)[int(len(sizes) * 0.9)]} max {max(sizes)}")
    print(f"check-emitting spans: {sum(1 for sp in spans if sp.checks)} | names: {len({c for sp in spans for c in sp.checks})} | always-run: {[sp.name for sp in spans if sp.always]}")
    print(f"merged spans (>1 stmt): {[(sp.name, len(sp.stmts)) for sp in spans if len(sp.stmts) > 1]}")


if __name__ == "__main__":
    {"census": census, "generate": generate}[sys.argv[1]]()

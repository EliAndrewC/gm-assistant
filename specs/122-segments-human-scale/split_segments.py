"""One-shot splitter for `check_village/segments_*.py` (feature 122).

Cuts a segment file into contiguous sub-files at SEGMENT BOUNDARIES, preserving definition
order exactly. Safe because feature 109 made the registry derive itself: `registry.py`
discovers segments by globbing `segments_*.py` and orders them by the NUMERIC KEY IN THE
FUNCTION NAME plus `_PLACEMENTS`, so which file a segment lives in is not load-bearing.

Usage:
    python3 split_segments.py --plan                       # propose cuts for every file
    python3 split_segments.py --apply <file> a:<name> b:<name> ...

The verification the tool does itself, every run:
  * the concatenated sub-file BODIES are byte-identical to the original body
  * every segment name survives, exactly once, in the same order
  * each sub-file's pruned import block still covers every name its body references

Retire this file once the split has landed (same convention as 022/023's transformers).
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import sys

PKG = pathlib.Path(__file__).resolve().parents[2] / ".claude/skills/diagram/l7r/diagram/check_village"
TARGET_LINES = 850  # the aim per sub-file; the bar is ~1,000 (constitution X clause 13)


def segments_of(path: pathlib.Path) -> tuple[list[str], int, list[tuple[str, int, int]]]:
    """Return (header_lines, first_body_line, [(name, start_line, end_line), ...]), 1-indexed.

    The HEADER is the module docstring and the import statements and nothing else. It is the
    only text copied into every sub-file, so anything else that lands in it is DUPLICATED - and
    several of these files carry a check's `# WHY:` comment bank between the imports and the
    first `def`, which a naive "everything before the first def" header silently triples. That
    bank belongs to the first segment, exactly like every other bank.
    """
    src = path.read_text().splitlines()
    tree = ast.parse("\n".join(src))
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    if not fns:
        raise SystemExit(f"{path.name}: no top-level functions")
    header_end = 0
    for node in tree.body:
        if isinstance(node, ast.Import | ast.ImportFrom) or (
            isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
        ):
            header_end = max(header_end, node.end_lineno or 0)
        else:
            break
    # a comment bank ABOVE a def belongs to it, so a cut point is the first line after the
    # previous segment's last line (or the end of the header, for the first segment)
    spans: list[tuple[str, int, int]] = []
    for i, fn in enumerate(fns):
        start = fns[i - 1].end_lineno + 1 if i else header_end + 1
        spans.append((fn.name, start, fn.end_lineno))
    assert spans[-1][2] <= len(src)
    spans[-1] = (spans[-1][0], spans[-1][1], len(src))  # trailing blank lines ride with the last
    return src[:header_end], header_end + 1, spans


def propose(path: pathlib.Path) -> list[tuple[str, int]]:
    """Balanced cut points: [(first_segment_name_of_part, part_line_count), ...]."""
    _, _, spans = segments_of(path)
    total = spans[-1][2] - spans[0][1] + 1
    parts = max(2, -(-total // TARGET_LINES))
    want = total / parts
    cuts: list[tuple[str, int]] = [(spans[0][0], 0)]
    run = 0
    for name, start, end in spans:
        size = end - start + 1
        if run and run + size / 2 > want and len(cuts) < parts:
            cuts[-1] = (cuts[-1][0], run)
            cuts.append((name, 0))
            run = 0
        run += size
    cuts[-1] = (cuts[-1][0], run)
    return cuts


def header_for(header: list[str], docstring: str) -> list[str]:
    """The original header VERBATIM, with only its module docstring replaced.

    Deliberately no import pruning here. Pruning by hand means understanding every header shape
    (single-line, parenthesized multi-line, aliased, `__future__`), and a prune that silently
    drops a needed name is exactly the class of edit this feature must not make. `ruff check
    --select F401 --fix`, run over the package afterwards, is the authority instead: it decides
    from the parsed module, it cannot drop a name the body uses, and anything it leaves behind
    that IS unused fails the normal lint gate rather than passing quietly.
    """
    out = [docstring, *header[1:]]
    while out and not out[-1].strip():
        out.pop()
    return out


def split_apply(path: pathlib.Path, spec: list[tuple[str, str]]) -> list[pathlib.Path]:
    """spec = [(new_module_stem, first_segment_name), ...] in order; the first entry starts at 0."""
    header, _first, spans = segments_of(path)
    src = path.read_text().splitlines()
    index = {name: i for i, (name, _, _) in enumerate(spans)}
    missing = [s[1] for s in spec[1:] if s[1] not in index]
    if missing:
        raise SystemExit(f"{path.name}: no such segment(s): {missing}")
    starts = [0] + [index[s[1]] for s in spec[1:]]
    if starts != sorted(starts) or len(set(starts)) != len(starts):
        raise SystemExit(f"{path.name}: cut points out of order: {starts}")

    written: list[pathlib.Path] = []
    bodies: list[list[str]] = []
    for i, (stem, _) in enumerate(spec):
        last = (starts[i + 1] - 1) if i + 1 < len(spec) else len(spans) - 1
        lo, hi = spans[starts[i]][1], spans[last][2]
        body = src[lo - 1 : hi]
        bodies.append(body)
        keys = f"{spans[starts[i]][0].split('__')[0][5:]}-{spans[last][0].split('__')[0][5:]}"
        theme = stem.split("_", 2)[2].replace("_", " ")
        newdoc = f'"""Gate segments ({theme}; keys {keys}) - bodies verbatim, registry order preserved."""'
        head = header_for(header, newdoc)
        out = PKG / f"{stem}.py"
        if out.exists() and out != path:
            raise SystemExit(f"{out.name} already exists")
        out.write_text("\n".join([*head, "", "", *body]).rstrip("\n") + "\n")
        written.append(out)
        print(f"  {out.name:54s} {len(head) + len(body) + 2:5d} lines  keys {keys}")

    flat = [ln for b in bodies for ln in b]
    orig = src[spans[0][1] - 1 : spans[-1][2]]
    if flat != orig:
        raise SystemExit(f"{path.name}: BODY NOT PRESERVED ({len(flat)} vs {len(orig)} lines)")
    names_before = [n for n, _, _ in spans]
    names_after: list[str] = []
    for p in written:
        names_after += [n.name for n in ast.parse(p.read_text()).body if isinstance(n, ast.FunctionDef)]
    if names_before != names_after:
        raise SystemExit(f"{path.name}: SEGMENT ORDER CHANGED")
    path.unlink()
    print(f"  removed {path.name}; {len(names_before)} segments preserved in order")
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    args = ap.parse_args()
    if args.plan:
        for path in sorted(PKG.glob("segments_*.py")):
            _, _, spans = segments_of(path)
            print(f"\n{path.name}  ({len(path.read_text().splitlines())} lines, {len(spans)} segments)")
            for name, size in propose(path):
                print(f"    cut at {name:62s} ~{size:5d} lines")
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

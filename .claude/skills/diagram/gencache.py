#!/usr/bin/env python3
"""Skip regenerating a map whose inputs did not change (GM 2026-08-08).

WHY. A city gen costs 10-21s and most engine edits do not touch most maps: a farmhouse tweak
leaves Minami's interior identical, a docs edit leaves everything identical. Re-deriving all of it
is the single biggest cost in the iteration loop, and the pool only grows.

THE PROBLEM, AND WHY THIS IS NOT A GUESS. Cache invalidation goes wrong when someone PREDICTS what
matters. This engine has already been bitten three times in one week by exactly that (a `placed`
index keyed on length, a well memo keyed on record counts, an index keyed on list identity), so
nothing here predicts. The key is derived from EVERYTHING that can reach the output:

  * the gen file's bytes;
  * the MODULE-LEVEL source of every engine module (constants, class attributes, decorators,
    imports - anything that runs at import time and can change behavior without any function
    changing);
  * the source of every FUNCTION the map actually executed;
  * every non-source FILE the run opened for reading;
  * the interpreter version, the renderer version, and this format's own version.

SOUNDNESS OF THE FINE-GRAINED PART. A function the map never executed can only reach the map if
something the map DOES execute calls it - and that requires changing the caller, which is in the
dep set and hashed. A newly added function cannot be called by unchanged code. Module-level changes
are hashed wholesale rather than per-name, so a changed constant invalidates even though no
function's source moved. A dep whose source cannot be resolved (a renamed or deleted function, a
comprehension the AST walk does not name) degrades that file to a WHOLE-FILE hash rather than being
ignored - the failure direction is always "regenerate unnecessarily", never "serve staleness".

WHAT IT DELIBERATELY DOES NOT DO. It is never the source of truth. `test_villages.py` - the gate -
calls the gens directly and always regenerates, so a stale entry cannot ship a wrong map: it could
only mislead an interactive look, and `make done` catches it before any commit. Keep it that way;
`test_gencache.py::test_the_gate_never_reads_the_cache` holds the line.

Dependency capture costs nothing measurable: `sys.monitoring` reports each code object once and
then returns DISABLE, so the overhead is proportional to the number of distinct functions (a few
hundred), not to the number of calls (tens of millions).
"""

from __future__ import annotations

import ast
import builtins
import hashlib
import json
import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(HERE, ".gencache")
FORMAT_VERSION = "1"  # bump to invalidate every entry when this file's key scheme changes

# The cache itself never participates in generating a map, so its own source is not an input; every
# other .py here is (tests excluded - they cannot affect a gen either, and including them would
# invalidate the whole pool on every test edit).
_NOT_ENGINE = {"gencache.py", "regen.py"}
OUTPUT_SUFFIXES = (".json", ".svg", ".png")


def engine_files() -> list[str]:
    return sorted(os.path.join(HERE, f) for f in os.listdir(HERE) if f.endswith(".py") and not f.startswith("test_") and f not in _NOT_ENGINE)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:32]


def split_sources(path: str) -> tuple[str, dict[str, str], set[str]]:
    """(module-level hash, {qualname: source hash}, {class qualnames}) for one Python file.

    "Module level" is everything that is not inside a function body - so a changed constant, class
    attribute, decorator or import invalidates every map, which is the conservative direction. A
    file that will not parse hashes whole, likewise conservatively."""
    src = Path(path).read_bytes()
    try:
        tree = ast.parse(src)
    except SyntaxError:  # pragma: no cover - defensive: a broken file regenerates everything
        return _sha(src), {}, set()
    lines = src.decode("utf-8", "replace").splitlines(keepends=True)
    funcs: dict[str, str] = {}
    classes: set[str] = set()
    spans: list[tuple[int, int]] = []

    def walk(node: Any, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            name = getattr(child, "name", None)
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                qual = f"{prefix}{name}"
                funcs[qual] = _sha("".join(lines[child.lineno - 1 : child.end_lineno]).encode())
                spans.append((child.lineno, child.end_lineno or child.lineno))
                walk(child, f"{qual}.")  # nested defs get their own entry AND stay in their parent's span
            elif isinstance(child, ast.ClassDef):
                classes.add(f"{prefix}{name}")
                walk(child, f"{prefix}{name}.")
            else:
                walk(child, prefix)

    walk(tree, "")
    inside = {n for lo, hi in spans for n in range(lo, hi + 1)}
    module_level = "".join(line for i, line in enumerate(lines, 1) if i not in inside)
    return _sha(module_level.encode()), funcs, classes


def _renderer_version() -> str:
    try:
        out = subprocess.run(["resvg", "--version"], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or "unknown"
    except OSError, subprocess.SubprocessError:  # pragma: no cover - defensive: resvg absent
        return "absent"


def compute_key(gen: str, deps: dict[str, Any] | None) -> str:
    """The cache key for `gen`. With no recorded deps this is the COARSE key - every engine file
    hashed whole - which is what a first run and any unrecorded map get."""
    parts = [FORMAT_VERSION, sys.version, _renderer_version(), _sha(Path(gen).read_bytes())]
    funcs_wanted: dict[str, set[str]] = {}
    if deps is not None:
        for filename, qual in deps.get("functions", []):
            funcs_wanted.setdefault(filename, set()).add(qual)
    for path in engine_files():
        if deps is None:
            parts.append(f"{os.path.basename(path)}={_sha(Path(path).read_bytes())}")
            continue
        mod_hash, funcs, classes = split_sources(path)
        parts.append(f"{os.path.basename(path)}:mod={mod_hash}")
        for qual in sorted(funcs_wanted.get(path, ())):
            if qual in funcs:
                parts.append(f"{os.path.basename(path)}:{qual}={funcs[qual]}")
            elif qual.rpartition(".")[2].startswith("<") or qual in classes:
                # SYNTHETIC code objects - "<module>", "<listcomp>", "<genexpr>", "<lambda>" - and
                # class BODIES. None is a def the AST walk names, and none needs to be: a
                # comprehension executes only if its enclosing function does, and that function's
                # source hash already contains the comprehension's text; a module or class body is
                # inside the module-level hash by construction. Without this they all fell through
                # to the whole-file fallback below - 114 of Minami's 476 key parts - and the
                # fine-grained key silently collapsed into the coarse one, which is exactly the
                # "looks like it works" failure this whole design is meant to avoid.
                continue
            else:
                # a dep we can no longer resolve (renamed, deleted, or a construct the walk does
                # not name): fall back to the WHOLE file rather than silently dropping it
                parts.append(f"{os.path.basename(path)}:whole={_sha(Path(path).read_bytes())}")
    for datafile in sorted(deps.get("files", []) if deps else ()):
        parts.append(f"data:{datafile}={_sha(Path(datafile).read_bytes()) if os.path.isfile(datafile) else 'missing'}")
    return _sha("\n".join(parts).encode())


def run_and_record(gen: str) -> dict[str, Any]:
    """Run a gen, recording which functions executed and which files it read.

    `sys.monitoring` with a DISABLE return reports each code object once, so this is free (measured:
    within noise on 800k calls). Nested-function qualnames carry `.<locals>.`, which the AST walk
    does not, so they are normalized here to match."""
    functions: set[tuple[str, str]] = set()
    files: set[str] = set()
    engine = set(engine_files())
    real_open = builtins.open

    def spy_open(file: Any, mode: str = "r", *a: Any, **k: Any) -> Any:
        try:
            path = os.path.abspath(file)
            if "r" in mode and "w" not in mode and "a" not in mode and not path.endswith(OUTPUT_SUFFIXES) and os.path.isfile(path):
                files.add(path)
        except TypeError:  # pragma: no cover - defensive: open() on a file descriptor
            pass
        return real_open(file, mode, *a, **k)

    mon = sys.monitoring
    tool = mon.PROFILER_ID

    def on_start(code: Any, offset: int) -> Any:
        path = code.co_filename
        if path in engine:
            functions.add((path, code.co_qualname.replace(".<locals>", "")))
        return mon.DISABLE

    builtins.open = spy_open  # type: ignore[assignment]
    mon.use_tool_id(tool, "gencache")
    try:
        mon.register_callback(tool, mon.events.PY_START, on_start)
        mon.set_events(tool, mon.events.PY_START)
        try:
            runpy.run_path(gen, run_name="__main__")
        finally:
            mon.set_events(tool, 0)
            mon.register_callback(tool, mon.events.PY_START, None)
    finally:
        mon.free_tool_id(tool)
        builtins.open = real_open  # type: ignore[assignment]
    return {"functions": sorted(functions), "files": sorted(files - engine)}


def _entry_dir(gen: str) -> str:
    return os.path.join(CACHE_DIR, os.path.basename(gen)[: -len(".gen.py")])


def _outputs(gen: str) -> list[str]:
    stem = gen[: -len(".gen.py")]
    return [stem + suffix for suffix in OUTPUT_SUFFIXES]


def load(gen: str) -> bool:
    """Restore this gen's outputs from cache if the key still matches. True on a hit."""
    entry = _entry_dir(gen)
    meta_path = os.path.join(entry, "meta.json")
    if not os.path.isfile(meta_path):
        return False
    meta = json.loads(Path(meta_path).read_text())
    if compute_key(gen, meta.get("deps")) != meta.get("key"):
        return False
    for out in _outputs(gen):
        cached = os.path.join(entry, os.path.basename(out))
        if os.path.isfile(cached):
            shutil.copy2(cached, out)
        elif os.path.exists(out):  # pragma: no cover - defensive: an output the build never made
            os.remove(out)
    return True


def store(gen: str, deps: dict[str, Any]) -> None:
    entry = _entry_dir(gen)
    os.makedirs(entry, exist_ok=True)
    for out in _outputs(gen):
        if os.path.isfile(out):
            shutil.copy2(out, os.path.join(entry, os.path.basename(out)))
    Path(os.path.join(entry, "meta.json")).write_text(json.dumps({"key": compute_key(gen, deps), "deps": deps}))

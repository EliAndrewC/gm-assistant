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
  * the interpreter version, the renderer version, and this format's own version;
  * the installed third-party distribution set and the renderer font bytes (feature 026) - the
    dependency surface BELOW the Python-source horizon, where the PIL layout-engine incident
    lived (a Pillow bump rewrote 16 manifests with no code change).

SOUNDNESS OF THE FINE-GRAINED PART. A function the map never executed can only reach the map if
something the map DOES execute calls it - and that requires changing the caller, which is in the
dep set and hashed. A newly added function cannot be called by unchanged code. Module-level changes
are hashed wholesale rather than per-name, so a changed constant invalidates even though no
function's source moved. A dep whose source cannot be resolved (a renamed or deleted function, a
comprehension the AST walk does not name) degrades that file to a WHOLE-FILE hash rather than being
ignored - the failure direction is always "regenerate unnecessarily", never "serve staleness".

WHAT THE GATE DOES WITH IT (GM 2026-08-16, feature 026 - reversing the 2026-08-08 "the gate never
reads the cache" rule; the reversal's reasoning is recorded in specs/026-cache-backed-gate/).
`tests/test_villages.py` obtains each live map via `gate_obtain`: a verified HIT skips GENERATION only -
the full current check battery still runs against the served manifest, and the entry's stored
coverage data replays into the run so the coverage floors stay honest - while any doubt at all
(key moved, entry absent or incomplete, no stored coverage, `GATE_NO_CACHE=1`) regenerates in a
coverage-recording subprocess. What makes this safe to trust: generation is deterministic, so a
sound key implies byte-identical output; the key's one known blind spot (dependencies below the
Python-source horizon) is closed by `_deps_state`; and `cache_audit.py` remains the standing
empirical auditor - run it after ANY change to this file or to how generation is driven. After a
dependency-level change, the belt-and-suspenders procedure is one bypassed sweep:
`GATE_NO_CACHE=1 make done`.

Dependency capture costs nothing measurable: `sys.monitoring` reports each code object once and
then returns DISABLE, so the overhead is proportional to the number of distinct functions (a few
hundred), not to the number of calls (tens of millions).
"""

from __future__ import annotations

import ast
import builtins
import functools
import glob
import hashlib
import importlib.metadata
import json
import os
import runpy
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)  # the SKILL ROOT, not this package: every path below is relative to it. FOUR levels up since feature 119 (l7r/diagram/pipeline/), not two
CACHE_DIR = os.path.join(HERE, ".gencache")
FORMAT_VERSION = "1"  # bump to invalidate every entry when this file's key scheme changes

# The cache itself never participates in generating a map, so its own source is not an input; every
# other .py here is (tests excluded - they cannot affect a gen either, and including them would
# invalidate the whole pool on every test edit).
_NOT_ENGINE = {"gencache.py", "regen.py"}
OUTPUT_SUFFIXES = (".json", ".svg", ".png")
GATE_BYPASS = "GATE_NO_CACHE"  # =1 forces the gate to regenerate everything (feature 026)
COVERAGE_NAME = "coverage.data"  # per-entry generation coverage, stored by the gate's miss path


def engine_files() -> list[str]:
    """Every engine .py AT ANY DEPTH (feature 025 made settlement/ a package - a root-only listing
    would silently stop keying the cache on the main engine, serving stale maps after engine
    edits). Same walk rule as render_cache.engine_fingerprint: prune pool/, wip/, caches, hidden
    dirs and the tests/ tree; skip test files and the non-engine modules."""
    out: list[str] = []
    for dirpath, dirnames, filenames in os.walk(HERE):
        dirnames[:] = sorted(d for d in dirnames if d not in ("pool", "wip", "tests", "__pycache__", ".gencache") and not d.startswith(("test_", ".")))
        # dotFILES are excluded like dot-dirs: a hidden .py is never an engine module, it is a
        # transient (an editor swap, a tool's scratch driver). The gate's own miss drivers used to
        # land here as `.gatecov-*-driver.py` and every concurrent key computation counted them as
        # engine modules - so a parallel sweep poisoned every other map's key and nothing ever hit
        # (feature 026's first warm-gate measurement, 2026-08-16, came out SLOWER than cold).
        out.extend(os.path.join(dirpath, f) for f in filenames if f.endswith(".py") and not f.startswith(("test_", ".")) and f not in _NOT_ENGINE)
    return sorted(out)


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


_FONT_DIR = "/usr/share/fonts/truetype/dejavu"  # the faces PIL measures with and resvg renders with


@functools.lru_cache(maxsize=1)
def _deps_state() -> str:
    """The dependency surface BELOW the Python-source horizon (feature 026, research R1).

    Installed distributions rather than lockfile bytes, because what runs is what is INSTALLED - a
    one-off exploratory `pip install` (blessed by project doctrine) changes behavior without
    touching any lockfile. Font bytes because PIL opens them in C where the `open` spy cannot see,
    and glyph metrics feed label boxes and therefore manifests - the PIL layout-engine incident
    rewrote 16 manifests with no code change behind it. On any failure the component degrades to a
    never-match marker: regenerate unnecessarily, never serve staleness - the same convention as
    `split_sources`."""
    try:
        dists = sorted({f"{d.name}=={d.version}" for d in importlib.metadata.distributions()})
        fonts = [f"font:{os.path.basename(p)}={_sha(Path(p).read_bytes())}" for p in sorted(glob.glob(os.path.join(_FONT_DIR, "*.ttf")))]
        return _sha("\n".join(dists + fonts).encode())
    except Exception:  # pragma: no cover - defensive: conservative degradation, never staleness
        return "unresolvable-" + os.urandom(8).hex()


def compute_key(gen: str, deps: dict[str, Any] | None) -> str:
    """The cache key for `gen`. With no recorded deps this is the COARSE key - every engine file
    hashed whole - which is what a first run and any unrecorded map get."""
    parts = [FORMAT_VERSION, sys.version, _renderer_version(), _deps_state(), _sha(Path(gen).read_bytes())]
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
        # RE-ENABLE every location this tool disabled earlier IN THIS PROCESS. `on_start` returns
        # DISABLE so each code object reports once - which is what makes capture free - but that
        # disable is permanent per code object, so a second gen in the same process recorded only
        # the functions the FIRST one had not already touched. A whole-pool sweep therefore gave
        # map #1 a full dep set (473 functions) and everyone after it almost nothing (nagahara: 3),
        # leaving those maps keyed on so little that nearly any engine change would still read as a
        # hit. Found 2026-08-08 by the GM's end-to-end "change one algorithm and see what
        # regenerates" test - exactly the check the unit tests could not make, since each of them
        # traces a fresh module whose code objects had never been disabled.
        mon.restart_events()
        try:
            try:
                runpy.run_path(gen, run_name="__main__")
            except SystemExit as ex:
                # A GEN MAY FINISH BY EXITING, and in-process that would take the whole sweep with
                # it. Every Mode A gen ends `raise SystemExit(main())`, which is a normal successful
                # return for a script - but `runpy` runs it in THIS interpreter, so the exception
                # propagated out of regen.py and the batch stopped, silently, reporting exit 0. On
                # 2026-08-08 `python3 -m l7r.diagram.pipeline.regen pool/*/*.gen.py` - the whole-pool invocation this
                # file's docstring recommends - therefore rebuilt the nine hamlets, hit the first
                # magistracy, and quit before a single town, village or city, looking for all the
                # world like it had done the lot. A non-zero code is a real failure and still
                # raises; zero (or None) is just how a script says it is done.
                if ex.code:
                    raise
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
        elif os.path.isfile(out):
            # DELETE an output the entry LACKS - do not leave it standing (2026-08-17). This used to
            # keep it, arguing that "the key just matched, so any standing artifact was derived from
            # these same sources". That step is false, and it shipped four maps whose .png was the
            # PREVIOUS roll while their .json and .svg were the current one: a gate-built entry is
            # stored with rendering skipped, so it has no PNG, and the stale one on disk was left in
            # place and then re-dated by the copy of its siblings. Nothing looked wrong - all three
            # files carried the same mtime - and two review rounds judged the wrong image.
            # The key matched THIS entry's outputs; it says nothing about a file the entry does not
            # contain. Deleting is what forces the re-render, and a re-render is exactly right when
            # the only alternative is showing the wrong map.
            os.remove(out)
    return True


def store(gen: str, deps: dict[str, Any], *, gen_cpu_s: float | None = None, coverage_data: str | None = None) -> None:
    """Write an entry so that a CONCURRENT reader never sees a half-made one.

    The gate's miss path (026) also passes `coverage_data` (a coverage.py data file, copied in as
    COVERAGE_NAME) and `gen_cpu_s` (child-measured CPU seconds, into meta.json). Both land BEFORE
    the final meta.json publish, so the atomic-publish invariant below still holds for them.

    Two things make this safe. Every file lands by write-to-temp-then-os.replace, which is atomic
    within a filesystem, so a reader sees the old bytes or the new bytes and never a partial file.
    And meta.json - the thing `load` trusts - is written LAST, so an entry is only ever declared
    valid after the artifacts it describes are fully in place.

    A `.gencache` is per-CLONE (it lives beside the engine), so the concurrent writers to worry
    about are two runs inside one working tree, not two sessions. Those necessarily generate from
    the same sources, and generation is deterministic, so their artifacts are byte-identical and
    interleaving them cannot produce a mismatched entry. The atomicity here is what keeps that
    argument true even while a file is mid-copy."""
    entry = _entry_dir(gen)
    os.makedirs(entry, exist_ok=True)

    def place(data: bytes, dest: str) -> None:
        tmp = f"{dest}.tmp{os.getpid()}"
        Path(tmp).write_bytes(data)
        os.replace(tmp, dest)  # atomic: a reader sees old or new, never half

    # FILE ONLY WHAT THIS RUN WROTE. With `DIAGRAM_SKIP_RENDER` the run produces no PNG, and the
    # file standing on disk belongs to some earlier roll - filing it would declare a stale render to
    # be this key's output, which is how four hamlets came to ship the previous roll's image while
    # their manifests were current. The entry is simply PNG-less; `load` deletes any standing PNG
    # rather than restoring one, and the next render regenerates it.
    _skip_render = bool(os.environ.get("DIAGRAM_SKIP_RENDER"))
    for out in _outputs(gen):
        if _skip_render and out.endswith(".png"):
            continue
        if os.path.isfile(out):
            place(Path(out).read_bytes(), os.path.join(entry, os.path.basename(out)))
    if coverage_data is not None and os.path.isfile(coverage_data):
        place(Path(coverage_data).read_bytes(), os.path.join(entry, COVERAGE_NAME))
    meta: dict[str, Any] = {"key": compute_key(gen, deps), "deps": deps}
    if gen_cpu_s is not None:
        meta["gen_cpu_s"] = gen_cpu_s
    place(json.dumps(meta).encode(), os.path.join(entry, "meta.json"))


def _coverage_is_current(cov_src: str) -> bool:
    """Does this stored coverage still measure files that EXIST?

    THE HOLE THIS CLOSES, and it is one the KEY structurally cannot (2026-08-17). A cache hit
    replays the entry's coverage into the gate's combine, and coverage data is keyed by FILE PATH.
    So when a peer session's package split DELETES a module - `settlement/civic_grounds.py`, one of
    six such splits in a fortnight - every entry built before that sync goes on replaying coverage
    that measures it, `coverage report` dies with `No source for code`, and the Makefile reports it
    as the settlement RATCHET FLOOR being breached. A routine refactor in someone else's module
    then surfaces, in a clone that merely synced, as a coverage regression in code this session
    never opened.

    The key is right not to move: generation is unaffected and the map is correct. It is only the
    COVERAGE half of the entry that has gone stale, so that is what this tests. Any doubt at all
    regenerates - the same rule the rest of `gate_obtain` runs on - which costs one small sqlite
    read per map and turns a mystifying red gate into a silent `REGENERATED`.

    (Before this, the recovery was `GATE_NO_CACHE=1 make done`, which worked only if you knew the
    failure had nothing to do with the file it named. That is precisely the kind of tip that must
    live in the code rather than in a doc nobody re-reads - CLAUDE.md's "tips live in error
    output", one step better: no error to read.)"""
    try:
        from coverage import CoverageData  # noqa: PLC0415 - keep `coverage` off the import path of every generator run

        data = CoverageData(basename=cov_src)
        data.read()
        return all(os.path.isfile(f) for f in data.measured_files())
    except Exception:  # noqa: BLE001 - unreadable stored coverage IS doubt, and doubt regenerates
        return False


def gate_obtain(gen: str) -> tuple[str, str, float | None]:
    """Obtain a map for the GATE (feature 026): returns `(manifest_path, how, gen_cpu_s)`.

    HIT ("HIT"): the key matches AND the entry carries generation coverage data - restore the
    artifacts, replay the stored coverage into this run as a parallel-mode data file, execute no
    generation. MISS ("REGENERATED"): anything else - key moved, entry absent or incomplete, no
    coverage data (an iteration-path entry), or the GATE_NO_CACHE=1 bypass - regenerate in a
    subprocess under `coverage run --parallel-mode`, so the refreshed entry gains the coverage
    data and the child-measured CPU seconds the next hit needs. The caller runs the check battery
    in-process on BOTH paths - checking is never cached. Contract and pinning tests:
    specs/026-cache-backed-gate/contracts/gate-cache.md."""
    manifest = gen[: -len(".gen.py")] + ".json"
    stem = os.path.basename(gen)[: -len(".gen.py")]
    cov_src = os.path.join(_entry_dir(gen), COVERAGE_NAME)
    if os.environ.get(GATE_BYPASS) != "1" and os.path.isfile(cov_src) and os.path.getsize(cov_src) > 0 and _coverage_is_current(cov_src) and load(gen):
        shutil.copyfile(cov_src, os.path.join(HERE, f".coverage.gatehit-{stem}-{os.getpid()}"))
        return manifest, "HIT", None
    # The child's scratch files (driver, record, raw coverage data) live OUTSIDE the engine tree:
    # anything transient dropped into HERE risks contaminating concurrent key computations - the
    # dotfile filter in engine_files() is the second layer of the same defense.
    workdir = tempfile.mkdtemp(prefix=f"gatecov-{stem}-")
    covbase = os.path.join(workdir, "cov")
    recfile = os.path.join(workdir, "rec.json")
    driver = os.path.join(workdir, "driver.py")
    Path(driver).write_text(
        "import json, sys, time\n"
        f"sys.path.insert(0, {HERE!r})\n"
        "from l7r.diagram.pipeline import gencache\n"
        "t0 = time.process_time()\n"
        f"deps = gencache.run_and_record({gen!r})\n"
        f"json.dump({{'deps': deps, 'cpu': time.process_time() - t0}}, open({recfile!r}, 'w'))\n"
    )
    # the child must be the ONLY coverage recorder in its process: strip the parent pytest-cov
    # session's subprocess hooks, or two recorders fight over the sys.monitoring tool id
    env = {k: v for k, v in os.environ.items() if not k.startswith(("COV_CORE_", "COVERAGE_"))}
    env["DIAGRAM_SKIP_RENDER"] = "1"  # the gate reads the manifest, never the PNG
    env["COVERAGE_FILE"] = covbase
    try:
        proc = subprocess.run([sys.executable, "-m", "coverage", "run", "--parallel-mode", driver], cwd=HERE, env=env, capture_output=True, text=True)
        if proc.returncode:
            raise RuntimeError(f"gate regeneration failed for {os.path.basename(gen)} (exit {proc.returncode}):\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
        with open(recfile) as fh:
            rec = json.load(fh)
        covfiles = sorted(glob.glob(covbase + ".*"))
        store(gen, rec["deps"], gen_cpu_s=rec["cpu"], coverage_data=covfiles[0] if covfiles else None)
        for i, covfile in enumerate(covfiles):
            # the child's recording also feeds THIS run's coverage: published onto the session
            # data-file glob (`.coverage.*`) that the Makefile's `coverage combine --append`
            # sweeps. Copy-then-replace, because the scratch dir is on another filesystem (a bare
            # os.replace raises EXDEV) and the final landing must still be atomic.
            dest = os.path.join(HERE, f".coverage.gatehit-{stem}-{os.getpid()}-{i}")
            shutil.copyfile(covfile, dest + ".tmp")
            os.replace(dest + ".tmp", dest)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    return manifest, "REGENERATED", float(rec["cpu"])

#!/usr/bin/env python3
"""The cache is only allowed to exist because it is DEMONSTRABLY safe (GM 2026-08-08: "if both the
coarse and fine grained version are demonstrably safe"). These are that demonstration.

Every test below is about one question: can a change reach a map's output WITHOUT moving its key?
The failure direction that matters is only ever "served a stale map"; regenerating unnecessarily is
free correctness. So each test that asserts a HIT also proves the hit was RIGHT, by regenerating
and comparing bytes - an assertion that the key did not move is worth nothing on its own.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import gencache

HERE = os.path.dirname(os.path.abspath(__file__))

_ENGINE = '''
CONSTANT = 3

def used(x):
    return x * CONSTANT

def unused(x):
    return x * 999

class Thing:
    def method(self, x):
        return used(x) + 1
'''

_GEN = '''
import sys
sys.path.insert(0, {here!r})
import {mod} as fakeengine
open({out!r}, "w").write(str(fakeengine.Thing().method(2)))
'''


def _fixture(tmp_path, engine=_ENGINE):
    """A miniature engine + gen, wired so gencache treats the temp dir as the engine.

    The module name is UNIQUE PER TEST on purpose. With a shared name, `sys.modules` served the
    first test's module to every later one - so the engine file a test edited was not the module
    its gen actually imported, and the tests quietly stopped testing anything (found 2026-08-08,
    when only the test that happened to run first behaved)."""
    mod = "fe_" + "".join(c if c.isalnum() else "_" for c in os.path.basename(str(tmp_path)))
    eng = tmp_path / f"{mod}.py"
    eng.write_text(textwrap.dedent(engine))
    out = tmp_path / "toy.json"
    gen = tmp_path / "toy.gen.py"
    gen.write_text(textwrap.dedent(_GEN).format(here=str(tmp_path), out=str(out), mod=mod))
    return eng, gen, out


def _with_engine(monkeypatch, tmp_path, eng):
    monkeypatch.setattr(gencache, "engine_files", lambda: [str(eng)])
    monkeypatch.setattr(gencache, "CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(gencache, "_renderer_version", lambda: "pinned")


def test_a_change_to_an_executed_function_invalidates(tmp_path, monkeypatch):
    eng, gen, _ = _fixture(tmp_path)
    _with_engine(monkeypatch, tmp_path, eng)
    deps = gencache.run_and_record(str(gen))
    before = gencache.compute_key(str(gen), deps)
    eng.write_text(eng.read_text().replace("return x * CONSTANT", "return x * CONSTANT + 1"))
    assert gencache.compute_key(str(gen), deps) != before, "a changed function the map RAN must move the key"


def test_a_change_outside_the_dep_set_is_a_hit_AND_the_hit_is_correct(tmp_path, monkeypatch):
    """The whole point of the fine-grained key - and the assertion that makes it honest is the
    second one: regenerate anyway and prove the bytes really are identical, so serving the cache
    was not merely permitted but RIGHT."""
    eng, gen, out = _fixture(tmp_path)
    _with_engine(monkeypatch, tmp_path, eng)
    deps = gencache.run_and_record(str(gen))
    before, fresh = gencache.compute_key(str(gen), deps), out.read_bytes()
    eng.write_text(eng.read_text().replace("return x * 999", "return x * 12345"))
    assert gencache.compute_key(str(gen), deps) == before, "a function the map never ran must NOT move the key"
    out.unlink()
    gencache.run_and_record(str(gen))
    assert out.read_bytes() == fresh, "the cache would have served this - so it must be what regeneration produces"


def test_a_module_level_change_invalidates_even_though_no_function_moved(tmp_path, monkeypatch):
    # the hole a per-function key would leave: a constant read by an executed function
    eng, gen, _ = _fixture(tmp_path)
    _with_engine(monkeypatch, tmp_path, eng)
    deps = gencache.run_and_record(str(gen))
    before = gencache.compute_key(str(gen), deps)
    eng.write_text(eng.read_text().replace("CONSTANT = 3", "CONSTANT = 4"))
    assert gencache.compute_key(str(gen), deps) != before


def test_a_renamed_dep_falls_back_to_the_whole_file_rather_than_being_ignored(tmp_path, monkeypatch):
    # an unresolvable dep must degrade CONSERVATIVELY - the direction of failure is everything
    eng, gen, _ = _fixture(tmp_path)
    _with_engine(monkeypatch, tmp_path, eng)
    deps = gencache.run_and_record(str(gen))
    eng.write_text(eng.read_text().replace("def used(", "def renamed("))
    key_after_rename = gencache.compute_key(str(gen), deps)
    eng.write_text(eng.read_text() + "\n# an edit nothing in the dep set can see\n")
    assert gencache.compute_key(str(gen), deps) != key_after_rename, "with a dep unresolved the file must hash WHOLE"


def test_the_gen_file_itself_is_part_of_the_key(tmp_path, monkeypatch):
    eng, gen, _ = _fixture(tmp_path)
    _with_engine(monkeypatch, tmp_path, eng)
    deps = gencache.run_and_record(str(gen))
    before = gencache.compute_key(str(gen), deps)
    gen.write_text(gen.read_text() + "\n# touched\n")
    assert gencache.compute_key(str(gen), deps) != before


def test_a_data_file_the_run_read_is_part_of_the_key(tmp_path, monkeypatch):
    """A gen that READS a data file has an input no source hash covers. `open` is spied during the
    recorded run so that input tracks itself, instead of someone having to remember it."""
    eng, gen, out = _fixture(tmp_path)
    data = tmp_path / "table.txt"
    data.write_text("7")
    gen.write_text(gen.read_text().replace("fakeengine.Thing().method(2)", f"fakeengine.Thing().method(int(open({str(data)!r}).read()))"))
    _with_engine(monkeypatch, tmp_path, eng)
    deps = gencache.run_and_record(str(gen))
    assert str(data) in deps["files"], "the spied open() must record a data input"
    before = gencache.compute_key(str(gen), deps)
    data.write_text("9")
    assert gencache.compute_key(str(gen), deps) != before


def test_round_trip_restores_byte_identical_outputs(tmp_path, monkeypatch):
    eng, gen, out = _fixture(tmp_path)
    _with_engine(monkeypatch, tmp_path, eng)
    deps = gencache.run_and_record(str(gen))
    fresh = out.read_bytes()
    gencache.store(str(gen), deps)
    out.unlink()
    assert gencache.load(str(gen)) is True
    assert out.read_bytes() == fresh
    # and a moved key is a MISS, not a silently-served stale entry
    stored = json.loads(Path(gencache.CACHE_DIR, "toy", "meta.json").read_text())
    eng.write_text(eng.read_text().replace("return x * CONSTANT", "return x * CONSTANT + 1"))
    assert gencache.compute_key(str(gen), stored["deps"]) != stored["key"], "a changed dep must not still match the stored key"


def test_no_recorded_deps_falls_back_to_the_coarse_whole_engine_key(tmp_path, monkeypatch):
    eng, gen, _ = _fixture(tmp_path)
    _with_engine(monkeypatch, tmp_path, eng)
    before = gencache.compute_key(str(gen), None)
    eng.write_text(eng.read_text().replace("return x * 999", "return x * 12345"))  # an UNUSED function
    assert gencache.compute_key(str(gen), None) != before, "with no dep set every engine byte counts"


def test_a_second_gen_in_the_same_process_records_its_own_full_dep_set(tmp_path, monkeypatch):
    """`sys.monitoring`'s DISABLE is permanent per code object, and that is what makes capture free
    - but without `restart_events()` the SECOND map traced in one process records only what the
    first did not already touch. A whole-pool sweep gave map #1 473 deps and nagahara 3, leaving it
    keyed on so little that almost any engine change would still have read as a hit.

    The unit tests could not catch this: each builds a FRESH engine module whose code objects were
    never disabled. It took an end-to-end "change one algorithm and see what regenerates" sweep, so
    the lesson gets pinned here where it is cheap to re-check.
    """
    eng, gen1, out1 = _fixture(tmp_path)
    mod = eng.stem
    out2 = tmp_path / "toy2.json"
    gen2 = tmp_path / "toy2.gen.py"
    gen2.write_text(textwrap.dedent(_GEN).format(here=str(tmp_path), out=str(out2), mod=mod))
    _with_engine(monkeypatch, tmp_path, eng)
    first = gencache.run_and_record(str(gen1))
    second = gencache.run_and_record(str(gen2))
    quals = {q for _, q in second["functions"]}
    assert "used" in quals and "Thing.method" in quals, f"the second gen recorded only {quals} - DISABLE leaked across runs"
    # every real FUNCTION the first run saw must be seen again; module and class BODIES
    # legitimately are not, because a second import of an already-imported module does not
    # re-execute them (and both are covered by the module-level hash anyway)
    bodies = {"<module>", "Thing"}
    assert {q for _, q in first["functions"]} - bodies <= quals, (first["functions"], sorted(quals))


def test_a_gen_that_ends_by_exiting_does_not_kill_the_sweep(tmp_path, monkeypatch):
    """Every Mode A gen ends `raise SystemExit(main())` - a normal successful return for a script,
    but `runpy` runs it in THIS interpreter, so it used to propagate straight out of regen.py and
    stop the batch dead at exit 0. `regen.py pool/*/*.gen.py` did the nine hamlets, hit the first
    magistracy, and reported success having skipped every town, village and city (2026-08-08)."""
    eng, gen, out = _fixture(tmp_path)
    _with_engine(monkeypatch, tmp_path, eng)
    gen.write_text(gen.read_text() + "\nraise SystemExit(0)\n")
    deps = gencache.run_and_record(str(gen))  # must RETURN, not raise
    assert out.read_text() == "7"  # ...and the gen still ran to completion
    assert deps["functions"], "the dep capture must survive the exit too"


def test_a_gen_that_exits_NONZERO_still_fails_loudly(tmp_path, monkeypatch):
    # the other direction: a real failure must not be swallowed by the tolerance above
    eng, gen, _ = _fixture(tmp_path)
    _with_engine(monkeypatch, tmp_path, eng)
    gen.write_text(gen.read_text() + "\nraise SystemExit(2)\n")
    with pytest.raises(SystemExit):
        gencache.run_and_record(str(gen))


def test_the_environment_is_part_of_the_key(tmp_path, monkeypatch):
    """A container rebuild changes the interpreter or the renderer, and both change what a map
    comes out as - the PIL layout-engine incident already rewrote 16 manifests with no code change
    behind it. All three environment inputs are asserted here rather than trusted, because none of
    them is exercised by an ordinary run: they only move when the box underneath you does."""
    eng, gen, _ = _fixture(tmp_path)
    _with_engine(monkeypatch, tmp_path, eng)
    deps = gencache.run_and_record(str(gen))
    before = gencache.compute_key(str(gen), deps)
    monkeypatch.setattr(gencache, "_renderer_version", lambda: "resvg 9.9.9")
    assert gencache.compute_key(str(gen), deps) != before, "a new renderer must invalidate - it draws the PNG"
    monkeypatch.setattr(gencache, "_renderer_version", lambda: "pinned")
    monkeypatch.setattr(sys, "version", "3.99.0 (fake)")
    assert gencache.compute_key(str(gen), deps) != before, "a new interpreter must invalidate"
    monkeypatch.undo()
    _with_engine(monkeypatch, tmp_path, eng)
    monkeypatch.setattr(gencache, "FORMAT_VERSION", "99")
    assert gencache.compute_key(str(gen), deps) != before, "bumping FORMAT_VERSION must invalidate every entry"


def test_an_entry_is_written_atomically_and_declared_valid_last(tmp_path, monkeypatch):
    """Concurrency safety, asserted as the two properties it rests on rather than by racing threads
    and hoping to hit the window.

    (1) Nothing is written in place - every artifact lands via a temp file and os.replace - so a
    reader mid-write sees the old bytes or the new bytes, never half a file. (2) meta.json, the
    only thing `load` trusts, is written LAST, so an entry is never declared valid before the
    artifacts it describes exist. Together those mean a concurrent reader either misses (no meta,
    or a stale key) or hits on a complete, self-consistent entry."""
    eng, gen, out = _fixture(tmp_path)
    _with_engine(monkeypatch, tmp_path, eng)
    deps = gencache.run_and_record(str(gen))

    order: list[str] = []
    real_replace = os.replace

    def spy_replace(src, dst, *a, **k):
        order.append(os.path.basename(str(dst)))
        return real_replace(src, dst, *a, **k)

    real_write = Path.write_bytes

    def no_direct_write(self, data):  # any write must go to a .tmp path, never to the live name
        assert ".tmp" in self.name, f"{self.name} was written in place - a reader could see it half-made"
        return real_write(self, data)

    monkeypatch.setattr(os, "replace", spy_replace)
    monkeypatch.setattr(Path, "write_bytes", no_direct_write)
    gencache.store(str(gen), deps)
    monkeypatch.undo()

    assert order, "store wrote nothing"
    assert order[-1] == "meta.json", f"meta.json must be published LAST, got order {order}"
    assert "toy.json" in order


def test_the_gate_never_reads_the_cache():
    """The property that makes the whole thing safe to adopt: `make done` regenerates from scratch,
    so a stale entry can mislead an interactive look but can never put a wrong map past the gate.
    If someone ever routes test_villages through regen.py, this fails and they have to argue with
    this docstring first."""
    gate = Path(os.path.join(HERE, "test_villages.py")).read_text()
    imports = [ln.strip() for ln in gate.splitlines() if ln.startswith(("import ", "from "))]
    assert not [ln for ln in imports if "gencache" in ln or ln.split()[1].split(".")[0] == "regen"], imports


def test_the_real_pool_round_trips_through_the_cache():
    """The end-to-end proof on a REAL map: regenerate, cache, wipe, restore, and demand the bytes
    match. Uses the cheapest SCRIPTED hamlet - the hand-authored pool is FROZEN (poolmaps.py) and
    its gens are never run - and restores the committed artifacts BYTE-FOR-BYTE afterwards rather
    than by re-running the gen: the engine is free to drift from what a live map was generated
    with, so a final re-run could leave the pool dirty."""
    gen = os.path.join(HERE, "pool", "hamlets", "inashiro.gen.py")
    base = gen[: -len(".gen.py")]
    manifest = base + ".json"
    committed = {p: Path(p).read_bytes() for p in (manifest, base + ".svg")}
    env = {**os.environ, "DIAGRAM_SKIP_RENDER": "1"}
    try:
        subprocess.run([sys.executable, gen], check=True, capture_output=True, env=env, cwd=HERE)
        fresh = Path(manifest).read_bytes()
        deps = json.loads(json.dumps(gencache.run_and_record(gen)))  # round-trips through JSON like a stored entry
        assert any(f.endswith("settlement.py") for f, _ in deps["functions"]), "a real gen must record engine deps"
        gencache.store(gen, deps)
        os.remove(manifest)
        assert gencache.load(gen) is True, "an unchanged pool map must hit"
        assert Path(manifest).read_bytes() == fresh
    finally:
        shutil.rmtree(os.path.join(gencache.CACHE_DIR, "inashiro"), ignore_errors=True)
        for p, data in committed.items():
            Path(p).write_bytes(data)


def test_regen_skips_frozen_legacy_maps():
    """The 2026-08-16 legacy freeze, enforced at the ITERATION path: `regen.py pool/*/*.gen.py`
    must not rewrite a frozen exhibit - the engine drifts freely now, so a re-run would replace
    committed artifacts with output nobody reviewed. The skip happens BEFORE any cache or
    generation work, and the message carries the policy and the `--frozen-ok` override (tips live
    in the blocking output, not in docs the moment forgets)."""
    import contextlib
    import io

    import regen

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = regen.main([os.path.join(HERE, "pool", "towns", "hoshizora.gen.py")])
    out = buf.getvalue()
    assert rc == 0
    assert "FROZEN" in out and "--frozen-ok" in out and "migration-plan.md" in out
    assert "REGENERATED" not in out and "CACHED" not in out, out

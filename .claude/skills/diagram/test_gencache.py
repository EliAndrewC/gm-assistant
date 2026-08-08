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
    match. Uses the cheapest hamlet so the suite stays fast; the mechanism is map-independent."""
    gen = os.path.join(HERE, "pool", "hamlets", "moritono.gen.py")
    manifest = gen[: -len(".gen.py")] + ".json"
    env = {**os.environ, "DIAGRAM_SKIP_RENDER": "1"}
    subprocess.run([sys.executable, gen], check=True, capture_output=True, env=env, cwd=HERE)
    fresh = Path(manifest).read_bytes()
    deps = json.loads(json.dumps(gencache.run_and_record(gen)))  # round-trips through JSON like a stored entry
    assert any(f.endswith("settlement.py") for f, _ in deps["functions"]), "a real gen must record engine deps"
    gencache.store(gen, deps)
    os.remove(manifest)
    try:
        assert gencache.load(gen) is True, "an unchanged pool map must hit"
        assert Path(manifest).read_bytes() == fresh
    finally:
        shutil.rmtree(os.path.join(gencache.CACHE_DIR, "moritono"), ignore_errors=True)
        subprocess.run([sys.executable, gen], check=True, capture_output=True, env=env, cwd=HERE)

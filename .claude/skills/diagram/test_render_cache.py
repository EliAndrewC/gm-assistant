"""Tests for render_cache - the content-hash short-circuit that regenerates the pool renders in
main. External boundaries (real git check-ignore, real generator subprocesses) are exercised
against a throwaway git repo and trivial fake generators, per the project's fixture-not-mock rule.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

import render_cache as rc

# A trivial stand-in generator: writes <stem>.svg + <stem>.png next to itself (the Mode B naming
# convention render_cache predicts) and records whether the main-tree override reached it.
FAKE_GEN = (
    "import os\n"
    "base = os.path.abspath(__file__)[:-len('.gen.py')]\n"
    "open(base + '.svg', 'w').write('<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 10 10\">\\n<rect/>\\n</svg>')\n"
    "open(base + '.png', 'wb').write(b'PNGDATA')\n"
    "open(base + '.ran', 'w').write(os.environ.get('GM_ASSISTANT_ALLOW_MAIN', 'unset'))\n"
)


def _make_gen(pool: str, subdir: str, stem: str) -> str:
    d = os.path.join(pool, subdir)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, stem + ".gen.py")
    with open(path, "w") as fh:
        fh.write(FAKE_GEN)
    return path


@pytest.fixture
def repo(tmp_path):
    """A throwaway git repo whose .gitignore ignores derived (Mode B) renders under
    pool/villages but keeps pool/magistracies svgs tracked (Mode A source), mirroring the real
    skill. Returns (repo_dir, skill_dir, pool_dir)."""
    repo_dir = str(tmp_path)
    subprocess.run(["git", "-C", repo_dir, "init", "-q"], check=True)
    skill = os.path.join(repo_dir, "skill")
    pool = os.path.join(skill, "pool")
    os.makedirs(pool)
    # engine sources + files the fingerprint must SKIP (non-.py, test_, and the module's own name)
    with open(os.path.join(skill, "settlement.py"), "w") as fh:
        fh.write("# engine v1\n")
    with open(os.path.join(skill, "waterfields.py"), "w") as fh:
        fh.write("# engine\n")
    with open(os.path.join(skill, "test_engine.py"), "w") as fh:
        fh.write("# excluded: a test file\n")
    with open(os.path.join(skill, "render_cache.py"), "w") as fh:
        fh.write("# excluded: the cache module itself\n")
    with open(os.path.join(skill, "notes.md"), "w") as fh:
        fh.write("excluded: not python\n")
    with open(os.path.join(repo_dir, ".gitignore"), "w") as fh:
        fh.write("skill/pool/villages/*.svg\nskill/pool/villages/*.png\nskill/pool/magistracies/*.png\n")
    return repo_dir, skill, pool


def test_sha256_and_predicted_svg():
    assert rc._sha256(b"abc") == rc._sha256(b"abc") != rc._sha256(b"abd")
    assert rc._predicted_svg("/x/foo.gen.py") == "/x/foo.svg"


def test_engine_fingerprint_covers_and_skips(repo):
    _, skill, _ = repo
    fp1 = rc.engine_fingerprint(skill)
    assert len(fp1) == 64
    # editing an engine file changes the fingerprint...
    with open(os.path.join(skill, "settlement.py"), "w") as fh:
        fh.write("# engine v2\n")
    assert rc.engine_fingerprint(skill) != fp1
    # ...but editing a skipped file (test_/non-.py/the module itself) does not
    with open(os.path.join(skill, "settlement.py"), "w") as fh:
        fh.write("# engine v2\n")
    fp2 = rc.engine_fingerprint(skill)
    for skipped in ("test_engine.py", "notes.md", "render_cache.py"):
        with open(os.path.join(skill, skipped), "w") as fh:
            fh.write("# changed but irrelevant\n")
    assert rc.engine_fingerprint(skill) == fp2


def test_input_hash_depends_on_gen_and_fingerprint(repo, tmp_path):
    gen = tmp_path / "m.gen.py"
    gen.write_text("A\n")
    h_a = rc.input_hash(str(gen), "fp1")
    assert h_a != rc.input_hash(str(gen), "fp2")  # fingerprint matters
    gen.write_text("B\n")
    assert rc.input_hash(str(gen), "fp1") != h_a  # gen source matters


def test_stamp_roundtrip_and_restamp(tmp_path):
    svg = tmp_path / "m.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">\n<rect/>\n</svg>')
    h = "a" * 64
    rc.stamp_svg(str(svg), h)
    assert rc.read_stamp(str(svg)) == h
    assert svg.read_text().startswith('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">')
    assert "<rect/>" in svg.read_text()  # body preserved
    # re-stamping replaces cleanly, does not accumulate
    h2 = "b" * 64
    rc.stamp_svg(str(svg), h2)
    assert rc.read_stamp(str(svg)) == h2
    assert svg.read_text().count("render-cache") == 1


def test_read_stamp_missing_and_unstamped(tmp_path):
    assert rc.read_stamp(str(tmp_path / "nope.svg")) is None
    plain = tmp_path / "plain.svg"
    plain.write_text("<svg></svg>")
    assert rc.read_stamp(str(plain)) is None


def test_is_cacheable_reads_gitignore(repo):
    repo_dir, _, pool = repo
    mode_b = _make_gen(pool, "villages", "hoshi")
    mode_a = _make_gen(pool, "magistracies", "ochiba")
    assert rc.is_cacheable(mode_b, repo_dir) is True
    assert rc.is_cacheable(mode_a, repo_dir) is False


def test_is_fresh_all_paths(repo):
    _, skill, pool = repo
    gen = _make_gen(pool, "villages", "hoshi")
    fp = rc.engine_fingerprint(skill)
    svg = rc._predicted_svg(gen)
    png = svg[:-4] + ".png"
    assert rc._is_fresh(gen, fp) is False  # no svg/png yet
    with open(svg, "w") as fh:
        fh.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"></svg>')
    with open(png, "wb") as fh:
        fh.write(b"x")
    assert rc._is_fresh(gen, fp) is False  # svg+png but unstamped
    rc.stamp_svg(svg, "0" * 64)
    assert rc._is_fresh(gen, fp) is False  # stamped, but wrong hash
    rc.stamp_svg(svg, rc.input_hash(gen, fp))
    assert rc._is_fresh(gen, fp) is True  # stamped with the right hash


def test_regen_pool_runs_stale_skips_fresh_and_exempts_mode_a(repo):
    repo_dir, skill, pool = repo
    fp = rc.engine_fingerprint(skill)
    stale = _make_gen(pool, "villages", "stale")
    fresh = _make_gen(pool, "villages", "fresh")
    mode_a = _make_gen(pool, "magistracies", "ochiba")
    # pre-satisfy the fresh one so it is skipped (svg stamped correctly + png present)
    fsvg = rc._predicted_svg(fresh)
    with open(fsvg, "w") as fh:
        fh.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><SENTINEL/></svg>')
    with open(fsvg[:-4] + ".png", "wb") as fh:
        fh.write(b"OLD")
    rc.stamp_svg(fsvg, rc.input_hash(fresh, fp))

    skipped, ran = rc.regen_pool(pool, repo_dir, skill_dir=skill, jobs=2)

    assert skipped == [fresh]
    assert ran == sorted([stale, mode_a])
    # fresh was not re-run: its sentinel svg body survived and its png is untouched
    assert "<SENTINEL/>" in Path(fsvg).read_text()
    assert Path(fsvg[:-4] + ".png").read_bytes() == b"OLD"
    # stale (Mode B) ran and got stamped with the current input hash
    assert rc.read_stamp(rc._predicted_svg(stale)) == rc.input_hash(stale, fp)
    assert Path(rc._predicted_svg(stale)[:-4] + ".ran").read_text() == "1"  # allow_main reached it
    # Mode A ran but its (tracked) svg was NOT stamped
    assert rc.read_stamp(rc._predicted_svg(mode_a)) is None


def test_regen_pool_no_allow_main(repo):
    repo_dir, skill, pool = repo
    gen = _make_gen(pool, "villages", "m")
    skipped, ran = rc.regen_pool(pool, repo_dir, skill_dir=skill, jobs=None, allow_main=False)
    assert skipped == [] and ran == [gen]
    assert Path(rc._predicted_svg(gen)[:-4] + ".ran").read_text() == "unset"


def test_main_reports_and_returns_zero(repo, capsys):
    repo_dir, skill, pool = repo
    _make_gen(pool, "villages", "m")
    rv = rc.main(["--pool", pool, "--main-repo", repo_dir, "--skill-dir", skill, "--jobs", "2"])
    assert rv == 0
    out = capsys.readouterr().out
    assert "1 regenerated, 0 cached" in out
    assert "regen  villages/m.gen.py" in out


def test_main_no_allow_main_flag(repo):
    repo_dir, skill, pool = repo
    gen = _make_gen(pool, "villages", "m")
    assert rc.main(["--pool", pool, "--main-repo", repo_dir, "--skill-dir", skill, "--no-allow-main"]) == 0
    assert Path(rc._predicted_svg(gen)[:-4] + ".ran").read_text() == "unset"

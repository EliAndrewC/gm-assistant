"""Unit tests for pool_index.py - the pool/index.html generator.

The synthetic-pool tests pin every branch (positive Mode A classification, the manifest-missing
warning, the derived columns, per-section column pruning, the unknown-folder section, missing
renders/notes); the real-pool test at the bottom pins the one property that matters against the
actual pool: every generator in it appears in the index.
"""

import glob
import os

from pipeline import pool_index as pi


def _mk(path: str, content: str = "") -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(content)
    return path


def _mini_pool(tmp_path):
    pool = str(tmp_path / "pool")
    _mk(
        os.path.join(pool, "hamlets", "aoi.json"),
        '{"meta": {"name": "Aoi & Co", "scale": "hamlet", "ftpx": 1.0, "generated_by": "hamletgen",'
        ' "households": 15, "field_archetype": "valley_paddy", "land_use_overlay": "lotus",'
        ' "nucleated": false, "lane_skeleton": "spine", "waivers": {"some_check": "a reason"},'
        ' "capital_dir": [1, 2], "water_source": "head_center", "water_source_position": "head_center"}}',
    )
    _mk(os.path.join(pool, "hamlets", "aoi.gen.py"))
    _mk(os.path.join(pool, "hamlets", "aoi.notes.md"), "# Design notes: Aoi\n")
    _mk(os.path.join(pool, "hamlets", "aoi.png"), "png")
    _mk(os.path.join(pool, "hamlets", "burned.gen.py"))  # settlement map with NO manifest
    _mk(
        os.path.join(pool, "towns", "beni.json"),
        '{"meta": {"scale": "town", "ftpx": 1, "walled": true, "population": 900, "settlement_form": "dispersed"}}',
    )
    _mk(os.path.join(pool, "towns", "beni.gen.py"))
    _mk(os.path.join(pool, "magistracies", "kiku-magistracy.gen.py"))
    _mk(
        os.path.join(pool, "magistracies", "kiku-magistracy.notes.md"),
        "# Design notes\n\n**Program type**: magistrate's manor (county magistracy) - see buildings.md.\n",
    )
    _mk(os.path.join(pool, "forts", "castle.gen.py"))
    _mk(os.path.join(pool, "forts", "castle.json"), '{"meta": {"name": "Castle", "walled": false}}')
    _mk(os.path.join(pool, "regressions", "bad.gen.py"))
    os.makedirs(os.path.join(pool, "villages"))  # present but empty -> no section
    return pool


def _section(page: str, dirname: str) -> str:
    start = page.index(f'<h2 id="{dirname}"')
    return page[start : page.index("</table>", start)]


def test_fmt_val_shapes():
    assert pi._fmt_val({"b_check": "why", "a_check": "why"}) == "a_check, b_check"
    assert pi._fmt_val([1, "S"]) == "1, S"
    assert pi._fmt_val(3.5) == "3.5"


def test_knobs_drops_the_duplicate_water_source_position():
    meta = {"water_source": "head_center", "water_source_position": "head_center", "windward": "W"}
    assert pi._knobs(meta) == "water_source=head_center; windward=W"
    meta2 = {"water_source": "corner_NW", "water_source_position": "head_left"}
    assert "water_source_position=head_left" in pi._knobs(meta2)


def test_mode_a_program_variants(tmp_path):
    pool = str(tmp_path)
    assert pi._mode_a_program(pool, "missing") == ""
    _mk(os.path.join(pool, "plain.notes.md"), "# notes with no program line\n")
    assert pi._mode_a_program(pool, "plain") == ""


def test_subtype_composition():
    assert pi._subtype({"field_archetype": "polder_grid", "walled": True}) == "polder_grid, walled"
    assert pi._subtype({"nucleated": True}) == ""
    assert pi._subtype({"nucleated": False}) == "dispersed"


def test_index_contents(tmp_path):
    pool = _mini_pool(tmp_path)
    page = pi.build_index(pool)

    # Mode B, scripted: name escaped, method, subtype, size, knobs (waivers by check name).
    assert "Aoi &amp; Co" in page
    assert "scripted (hamletgen)" in page
    assert "valley_paddy, overlay: lotus, dispersed" in page
    assert "hamlet (1 ft/px)" in page
    assert "15 households" in page
    assert "lane_skeleton=spine" in page
    assert "waivers=some_check" in page
    assert "capital_dir=1, 2" in page
    assert "water_source_position" not in page  # identical to water_source -> deduplicated
    assert 'src="hamlets/aoi.png"' in page
    # Map thumbnails open in a new tab; in-page nav anchors (pinned above) do not.
    assert '<a href="hamlets/aoi.png" target="_blank" rel="noopener">' in page
    assert 'href="hamlets/aoi.notes.md"' in page

    # A settlement-tier map with no manifest is reported as WRONG, never guessed at.
    assert "manifest missing" in _section(page, "hamlets")

    # Mode B, hand-authored, no name/notes/png: stem-derived name, population, missing-render text.
    assert "Beni" in page
    assert "hand-authored" in page
    assert "walled, dispersed" in page
    assert "pop 900" in page
    assert "render not synced" in page

    # Mode A: classified by FOLDER (positively), program read from the notes, compound scale.
    magi = _section(page, "magistracies")
    assert "Kiku Magistracy" in magi
    assert "Mode A compound" in magi
    assert "magistrate&#x27;s manor (county magistracy)" in magi
    assert "1/3 ft/px (3 px = 1 ft)" in magi

    # Column pruning: the magistracies section has no Size/Knobs cells to show, so no such columns;
    # the hamlets section keeps them.
    assert "<th>Size</th>" not in magi and "<th>Knobs</th>" not in magi
    assert "<th>Size</th>" in _section(page, "hamlets")

    # Empty cells in a kept column render as a dash, not as blank space.
    assert "<span class=none>-</span>" in page

    # Nav jump links, one per non-empty section, none for the empty villages folder.
    assert '<a href="#hamlets">Hamlets</a>' in page
    assert "#villages" not in page

    # Sections: known tiers in reading order, the unknown folder appended, empty/skip dirs absent.
    assert page.index('<h2 id="hamlets"') < page.index('<h2 id="towns"') < page.index('<h2 id="magistracies"')
    assert page.index('<h2 id="magistracies"') < page.index('<h2 id="forts"')
    assert "<h2>Villages</h2>" not in page
    assert "Regressions" not in page and "bad" not in page


def test_build_is_deterministic(tmp_path):
    pool = _mini_pool(tmp_path)
    assert pi.build_index(pool) == pi.build_index(pool)


def test_main_writes_the_file(tmp_path, capsys):
    pool = _mini_pool(tmp_path)
    assert pi.main(["--pool", pool]) == 0
    out = capsys.readouterr().out
    assert "pool-index: wrote" in out
    with open(os.path.join(pool, "index.html")) as fh:
        assert '<h2 id="hamlets">Hamlets</h2>' in fh.read()


def test_real_pool_every_gen_is_indexed():
    pool = os.path.join(pi.SKILL_DIR, "pool")
    page = pi.build_index(pool)
    gens = glob.glob(os.path.join(pool, "*", "*.gen.py"))
    assert gens, "the real pool has generators"
    for gen in gens:
        d = os.path.basename(os.path.dirname(gen))
        stem = os.path.basename(gen)[: -len(".gen.py")]
        if d in pi.SKIP_DIRS:
            continue
        assert f"{d}/{stem}.notes.md" in page or stem in page, f"{d}/{stem} missing from the index"
    # And no real map is in the manifest-missing state (a red cell here means a map lost its json).
    assert "manifest missing" not in page

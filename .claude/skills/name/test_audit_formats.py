"""Tests for audit_formats.py - the format-suitability rules."""

import audit_formats as af


def e(name, fmt, notes, prov="historical"):
    return {"name": name, "format": fmt, "notes": notes, "provenance": prov}


def test_two_kanji_format_needs_an_alternate_spelling():
    assert 4 not in af.allowed(e("Masahiro", 4, "Kanji 正広: upright + wide."))
    assert 4 in af.allowed(e("Masahiro", 4, "Kanji 正広, also written 雅広."))
    assert 4 in af.allowed(e("Kiku", 4, "The register recorded it in kana (きく)."))


def test_deity_format_only_for_constructed_or_kana_names():
    assert 8 not in af.allowed(e("Kiyomori", 8, "Kanji 清盛, Taira no Kiyomori."))
    assert 8 in af.allowed(e("Zuiran", 8, "Constructed; kanji 瑞蘭.", prov="invented"))


def test_nature_format_needs_a_nature_word_and_two_element_formats_need_two_kanji():
    assert 15 not in af.allowed(e("Tadashi", 15, "Kanji 忠: loyal."))
    assert 15 in af.allowed(e("Matsu", 15, "Kanji 松: pine tree."))
    assert {10, 16}.isdisjoint(af.allowed(e("Sen", 10, "Kanji 千: thousand.")))
    assert {10, 16} <= af.allowed(e("Sadako", 10, "Kanji 貞子: chaste + child."))


def test_preferences_by_provenance():
    assert af.preferred(e("Bara", 1, "Constructed; 薔薇 rose.", prov="invented")) == af.ORIGIN
    assert 2 in af.preferred(e("Masako", 2, "Kanji 雅子."))
    assert 4 in af.preferred(e("Kiku", 2, "Recorded in kana (きく)."))


def test_audit_reports_violations_and_lopsided_letters():
    rows = [e("Tadashi", 15, "Kanji 忠: loyal.")] + [e(f"W{i}", 7, "Kanji 和: harmony.") for i in range(9)]
    rep = af.audit(rows)
    assert rep["violations"] == [("Tadashi", 15)]
    assert rep["lopsided"] == [("W", 7, 9, 9)]
    assert rep["by_format"][7] == 9 and rep["n"] == 10


def test_real_world_leak_in_explanation_is_reported():
    rows = [
        {"name": "Jubei", "format": 7, "notes": "Kanji 十兵衛; the famous bearer is Yagyu Jubei.", "provenance": "historical",
         "explanation": "Jubei chose their name in honor of the famous Yagyu Jubei, who ..."},
        {"name": "Kiku", "format": 2, "notes": "Kanji 菊.", "provenance": "historical",
         "explanation": "Kiku - This name means \"chrysanthemum\". It represents autumn."},
    ]
    rep = af.audit(rows)
    assert rep["leaks"] == [("Jubei", "Yagyu")]


def test_main_exits_nonzero_on_violation(tmp_path, monkeypatch, capsys):
    import json

    for g, rows in (("male", [e("Tadashi", 15, "Kanji 忠: loyal.")]), ("female", [])):
        (tmp_path / f"pool-{g}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    monkeypatch.setattr(af, "SKILL_DIR", str(tmp_path))
    assert af.main() == 1
    assert "VIOLATION: Tadashi" in capsys.readouterr().out
    (tmp_path / "pool-male.jsonl").write_text("")
    assert af.main() == 0

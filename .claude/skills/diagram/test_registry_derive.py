"""Feature 109: the derived registry's guards, and the frozen-legacy equality oracle.

The registry stopped being hand-maintained data on 2026-08-16; these tests hold everything the
explicit roster used to provide (clause 14: move the safety property into tests proven to fire):

1. Fixture equality: every derived row equals its pre-collapse counterpart, by name, all six
   fields (`test_fixtures/registry_legacy_rows.json`, frozen and never regenerated).
2. Order: the fixture's order is a subsequence of the derived order - the execution contract.
3. Structural invariants: literal-return shape, unique keys, needs within free, META_CHECKS.
4. Fire-proofs: every guard demonstrably fails on a synthetic violation (a checker never seen
   failing is not a check - same doctrine as test_check_village_surface).
5. The cache is faithful (round-trip identical) and failure-soft (corruption -> re-derive).
"""

import json
from pathlib import Path

import pytest

import check_village
from check_village import registry as reg
from check_village.registry_analysis import _DerivationError, _derive_fields

HERE = Path(__file__).resolve().parent
FIXTURE = json.loads((HERE / "test_fixtures" / "registry_legacy_rows.json").read_text())

FIELDS = ("free", "writes", "checks", "needs", "meta", "always")


def _diff_rows(fixture_rows: list[dict], derived_by_name: dict[str, reg._GateSeg]) -> list[tuple[str, str]]:
    """(segment, field) for every divergence between fixture and derived - including a fixture
    segment the derivation lost entirely (field 'missing'). The equality oracle's engine."""
    out: list[tuple[str, str]] = []
    for row in fixture_rows:
        seg = derived_by_name.get(row["name"])
        if seg is None:
            out.append((row["name"], "missing"))
            continue
        for f in FIELDS:
            want = tuple(row[f]) if isinstance(row[f], list) else row[f]
            if getattr(seg, f) != want:
                out.append((row["name"], f))
    return out


def _by_name() -> dict[str, reg._GateSeg]:
    return {r.fn.__name__: r for r in reg.GATE_SEGMENTS}


def test_derived_rows_equal_frozen_legacy_fixture():
    assert _diff_rows(FIXTURE["rows"], _by_name()) == []


def test_meta_checks_equal_frozen_fixture():
    assert sorted(reg.META_CHECKS) == FIXTURE["meta_checks"]


def test_fixture_order_is_subsequence_of_derived_order():
    derived = [r.fn.__name__ for r in reg.GATE_SEGMENTS]
    it = iter(derived)
    missing = [row["name"] for row in FIXTURE["rows"] if row["name"] not in it]
    assert missing == [], f"fixture order not preserved at {missing[:3]}"


def test_structural_invariants():
    names = [r.fn.__name__ for r in reg.GATE_SEGMENTS]
    assert len(names) == len(set(names))
    for r in reg.GATE_SEGMENTS:
        assert set(r.needs) <= set(r.free), r.fn.__name__
    assert frozenset(c for r in reg.GATE_SEGMENTS if r.meta for c in r.checks) == reg.META_CHECKS
    assert len(reg._SEG_DEPS) == len(reg.GATE_SEGMENTS)
    assert all(d < i for i, deps in enumerate(reg._SEG_DEPS) for d in deps)


def test_package_surface_unchanged():
    assert check_village.GATE_SEGMENTS is reg.GATE_SEGMENTS
    assert check_village.META_CHECKS is reg.META_CHECKS


# ---- fire-proofs: each guard fails on a synthetic violation --------------------------------


def test_equality_guard_fires_on_flipped_meta_naming_segment_and_field():
    by_name = _by_name()
    victim = FIXTURE["rows"][0]["name"]
    by_name[victim] = by_name[victim]._replace(meta=not by_name[victim].meta)
    assert (victim, "meta") in _diff_rows(FIXTURE["rows"], by_name)


def test_equality_guard_fires_on_dropped_needs_name():
    by_name = _by_name()
    victim = next(r for r in reg.GATE_SEGMENTS if len(r.needs) > 1).fn.__name__
    by_name[victim] = by_name[victim]._replace(needs=by_name[victim].needs[1:])
    assert (victim, "needs") in _diff_rows(FIXTURE["rows"], by_name)


def test_equality_guard_fires_on_missing_segment():
    by_name = _by_name()
    victim = FIXTURE["rows"][-1]["name"]
    del by_name[victim]
    assert (victim, "missing") in _diff_rows(FIXTURE["rows"], by_name)


def test_order_guard_fires_on_swapped_placement_anchors():
    a, b = "_seg_0596__dry_plot_seams_shared", "_seg_0595__paddy_bunds_clear_the_supply_channels"
    swapped = dict(reg._PLACEMENTS)
    swapped[a], swapped[b] = swapped[b], swapped[a]
    names = {r.fn.__name__ for r in reg.GATE_SEGMENTS}
    assert reg._ordered_names(names, swapped) != [r.fn.__name__ for r in reg.GATE_SEGMENTS]


def test_order_guard_fires_on_stale_placement_entry():
    stale = dict(reg._PLACEMENTS)
    stale["_seg_9999__long_gone"] = "_seg_0317__dry_plot_furrows_vary"
    with pytest.raises(_DerivationError, match="names no live segment"):
        reg._ordered_names({r.fn.__name__ for r in reg.GATE_SEGMENTS}, stale)


def test_order_guard_fires_on_missing_anchor():
    broken = dict(reg._PLACEMENTS)
    broken["_seg_0596__dry_plot_seams_shared"] = "_seg_9999__long_gone"
    with pytest.raises(_DerivationError, match="anchor"):
        reg._ordered_names({r.fn.__name__ for r in reg.GATE_SEGMENTS}, broken)


def test_order_guard_fires_on_placement_cycle():
    names = {"_seg_0001__a", "_seg_0002__b", "_seg_0003__c"}
    cyclic = {"_seg_0002__b": "_seg_0003__c", "_seg_0003__c": "_seg_0002__b"}
    with pytest.raises(_DerivationError, match="chain"):
        reg._ordered_names(names, cyclic)


def test_order_guard_fires_on_duplicate_numeric_key():
    with pytest.raises(_DerivationError, match="duplicate numeric key"):
        reg._ordered_names({"_seg_0001__a", "_seg_0001__b"}, {})


def test_numeric_key_rejects_unkeyed_name():
    with pytest.raises(_DerivationError, match="numeric key"):
        reg._numeric_key("_seg_nokey__x")


def test_derive_guard_fires_on_stale_needs_override():
    names = {r.fn.__name__ for r in reg.GATE_SEGMENTS}
    orig = reg._NEEDS_OVERRIDES
    try:
        reg._NEEDS_OVERRIDES = {**orig, "_seg_9999__long_gone": ("M",)}
        with pytest.raises(_DerivationError, match="override"):
            reg._derive_rows(names)
    finally:
        reg._NEEDS_OVERRIDES = orig


def test_derive_guard_fires_on_override_outside_free():
    names = {r.fn.__name__ for r in reg.GATE_SEGMENTS}
    orig = reg._NEEDS_OVERRIDES
    try:
        reg._NEEDS_OVERRIDES = {**orig, "_seg_0324_500__comb_supply_commands_both_flanks": ("not_a_param",)}
        with pytest.raises(_DerivationError, match="subset"):
            reg._derive_rows(names)
    finally:
        reg._NEEDS_OVERRIDES = orig


def test_dropping_the_needs_override_diverges_from_the_fixture():
    """The 0324_500 override is load-bearing: without it the derived needs is the conservative
    superset and the fixture oracle catches the divergence (research.md R5)."""
    fields = _derive_fields(reg._PKG_DIR)
    derived = fields["_seg_0324_500__comb_supply_commands_both_flanks"].needs
    frozen = next(tuple(r["needs"]) for r in FIXTURE["rows"] if r["name"] == "_seg_0324_500__comb_supply_commands_both_flanks")
    assert derived != frozen
    assert set(frozen) < set(derived)


def test_segment_shape_guard_fires_on_nonliteral_return(tmp_path):
    bad = tmp_path / "segments_99_bad.py"
    bad.write_text("def _seg_9998__bad(*, check=None):\n    names = ('x',)\n    return _kept(locals(), names)\n")
    with pytest.raises(_DerivationError, match="literal"):
        _derive_fields(tmp_path)


def test_segment_shape_guard_fires_on_missing_kept_return(tmp_path):
    bad = tmp_path / "segments_99_bad.py"
    bad.write_text("def _seg_9998__bad(*, check=None):\n    return {}\n")
    with pytest.raises(_DerivationError, match="_kept"):
        _derive_fields(tmp_path)


def test_segment_shape_guard_fires_on_nonstring_kept_names(tmp_path):
    bad = tmp_path / "segments_99_bad.py"
    bad.write_text("def _seg_9998__bad(*, check=None):\n    return _kept(locals(), (1,))\n")
    with pytest.raises(_DerivationError, match="strings"):
        _derive_fields(tmp_path)


def test_derive_guard_fires_on_duplicate_segment_def(tmp_path):
    src = "def _seg_9998__dup(*, check=None):\n    return _kept(locals(), ())\n"
    (tmp_path / "segments_98_a.py").write_text(src)
    (tmp_path / "segments_99_b.py").write_text(src)
    with pytest.raises(_DerivationError, match="duplicate segment name"):
        _derive_fields(tmp_path)


# ---- cache ---------------------------------------------------------------------------------


def test_cache_round_trip_and_failure_soft(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "_CACHE_PATH", tmp_path / "sub" / "registry_rows.json")
    names = {r.fn.__name__ for r in reg.GATE_SEGMENTS}
    rows = reg._derive_rows(names)
    key = reg._source_key()
    assert reg._load_cached(key, names) is None  # cold: no file yet
    reg._store_cache(key, rows)
    assert reg._load_cached(key, names) == rows  # warm: identical rows
    assert reg._load_cached("other-key", names) is None  # stale key
    assert reg._load_cached(key, names - {rows[0]["name"]}) is None  # segment set moved
    reg._CACHE_PATH.write_text("{ not json")
    assert reg._load_cached(key, names) is None  # corrupt -> derive live


def test_cached_rows_rebuild_identical_registry():
    rows = reg._derive_rows({r.fn.__name__ for r in reg.GATE_SEGMENTS})
    rebuilt = tuple(reg._row(d, reg._fns) for d in rows)
    assert rebuilt == reg.GATE_SEGMENTS


def test_cache_store_is_failure_soft_when_unwritable(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(reg, "_CACHE_PATH", tmp_path / "blocked" / "cache.json")
    (tmp_path / "blocked").write_text("a file where the cache dir should be")
    with caplog.at_level("WARNING"):
        reg._store_cache("k", [])
    assert "not written" in caplog.text


def test_assemble_derives_on_cache_miss_and_loads_on_hit(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "_CACHE_PATH", tmp_path / "cache.json")
    names = {r.fn.__name__ for r in reg.GATE_SEGMENTS}
    cold = reg._assemble(names)  # miss: derive + store
    warm = reg._assemble(names)  # hit: load
    assert cold == warm
    assert (tmp_path / "cache.json").exists()

"""The `/money` skill's arithmetic and data (feature 219)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from l7r.money import basket as bk
from l7r.money import coins, ledger, rules
from l7r.money.__main__ import main
from l7r.money.readings import (
    KOKU_KG,
    Wage,
    load_wages,
    resolve_koku_kg,
    wage_dollars_per_koku,
)

# --- coins ---------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('text', 'sen'),
    [
        ('1 koku', 1000),
        ('3 koku 2 bu 1 zeni 5 sen', 3215),
        ('1.5 koku', 1500),
        ('1.33 zeni', 13),
        ('1.35 zeni', 14),
        ('2 BU, 3 zeni', 230),
        ('1,000 sen', 1000),
        ('4 bu + 6 sen', 406),
    ],
)
def test_parse(text: str, sen: int) -> None:
    assert coins.parse(text) == sen


@pytest.mark.parametrize('text', ['', 'three koku', '3 ryo', '3 koku and a horse'])
def test_parse_refuses(text: str) -> None:
    with pytest.raises(ValueError, match='not an amount'):
        coins.parse(text)


def test_fmt() -> None:
    assert coins.fmt(3215) == '3 koku 2 bu 1 zeni 5 sen'
    assert coins.fmt(0) == '0 sen'
    assert coins.fmt(1_234_000) == '1,234 koku'
    assert coins.fmt(-15) == '-1 zeni 5 sen'
    assert coins.koku(1500) == 1.5


def test_everyday_keeps_copper_exact_and_rounds_larger_sums() -> None:
    assert coins.everyday(13) == '1 zeni 3 sen'
    assert coins.everyday(230) == '2 bu 3 zeni'
    assert coins.everyday(234) == 'about 2 bu 3 zeni'
    assert coins.everyday(1500) == '1 koku 5 bu'
    assert coins.everyday(1064) == 'about 1 koku 1 bu'


# --- readings ------------------------------------------------------------------------------------


def _sheet(koku_kg: float) -> bk.Reading:
    """The 2017 sheet: Kyoto 1745-54's prices alone and the whole basket (feature 223 keeps it)."""
    model = bk.load()
    return bk.reading(
        model,
        model.basket('bassino-ma-a'),
        model.snapshot('2017-04'),
        koku_kg,
        mean='arithmetic',
        weights=model.reference_only(),
    )


def model_rice_ref() -> float:
    return bk.load().rice_ref


def test_2017_snapshot_reproduces_the_spreadsheet() -> None:
    """219 SC-001: $797.22 = 144.32 zeni -> $552 per koku, at the sheet's own koku mass. Feature
    222 moved the sheet into a basket, a snapshot and the reference era; this pins that the move
    changed no number (and the standard basket at 2017 reads the same, its new goods unpriced)."""
    kg, label = resolve_koku_kg(None)
    assert label == 'sheet-2017'
    r = _sheet(kg)
    assert round(r.dollars, 2) == 797.22
    # the sheet's grams are Bassino & Ma's, at 3.11 g a monme; the reference era now holds them at
    # the Genbun monme's 1.725 g (diagram#13), a uniform rescale that moves no ratio
    assert round(r.silver * 3.11 / 1.725, 3) == 325.816
    assert round(r.silver * 100 / (kg * model_rice_ref()), 2) == 144.32
    assert round(r.per_koku, 2) == 552.39
    model = bk.load()
    std = bk.reading(
        model,
        model.basket(),
        model.snapshot('2017-04'),
        kg,
        mean='arithmetic',
        weights=model.reference_only(),
    )
    assert round(std.per_koku, 2) == 552.39
    assert std.left_out == ('Salt', 'Fuel', 'Housing')


def test_the_withdrawn_forty_us_gallon_koku_is_gone() -> None:
    """diagram 0248: 'about 40 gallons' holds only in imperial gallons; 121 kg is not a koku."""
    assert 'forty-gallons' not in KOKU_KG


def test_budgets_koku_sits_beside_the_sheet() -> None:
    """budgets.md's ~150 kg brown koku is within 1% of the sheet's 151.5 kg."""
    assert round(_sheet(KOKU_KG['budgets-brown']).per_koku) == 547
    assert round(_sheet(KOKU_KG['budgets-polished']).per_koku) == 496


def test_resolve_koku_kg_takes_a_number() -> None:
    assert resolve_koku_kg('150') == (150.0, '150 kg')
    assert resolve_koku_kg(180.5) == (180.5, '180.5 kg')


def test_wage_dollars_default_is_the_handoff_derivation() -> None:
    """219 SC-002: ~$9,400 at $15/hour full time over 3.32 koku per unskilled year."""
    wage = load_wages()[-1]
    assert wage.hourly == 15.0
    assert abs(wage_dollars_per_koku(wage) - 9400) / 9400 < 0.01
    assert wage_dollars_per_koku(Wage('x', 10.0, 2000, '', ''), 2.0) == 10_000
    assert wage.day == 124.8


# --- ledger --------------------------------------------------------------------------------------

GOOD = {'item': 'x', 'low': 1, 'high': 2, 'per': 'item', 'label': 'guess', 'source': 'lead:notes'}


def test_every_ledger_row_carries_label_and_source() -> None:
    """FR-006 / SC-003, at the standard: the real ledger loads, so every row passed `problems`."""
    rows = ledger.load()
    assert len(rows) >= 25
    assert {r.label for r in rows} <= set(ledger.LABELS)


@pytest.mark.parametrize(
    ('change', 'complaint'),
    [
        ({'label': 'attested'}, 'label must be'),
        ({'source': ''}, 'source must be'),
        ({'source': 'my memory'}, 'source must be'),
        ({'low': 3}, 'low/high'),
        ({'low': 1.5}, 'low/high'),
        ({'item': ' '}, 'item and per'),
        ({'color': 'red'}, 'unknown color'),
    ],
)
def test_problems_refuses(change: dict[str, object], complaint: str) -> None:
    assert ledger.problems(GOOD) == []
    assert ledger.problems({**GOOD, 'label': 'comparative'}) == []
    assert any(complaint in p for p in ledger.problems({**GOOD, **change}))


def test_problems_names_missing_fields() -> None:
    assert ledger.problems({'item': 'x'})[0] == 'missing high, label, low, per, source'


def test_load_names_the_bad_line(tmp_path: Path) -> None:
    path = tmp_path / 'ledger.jsonl'
    path.write_text(json.dumps(GOOD) + '\n\n' + json.dumps({**GOOD, 'label': 'x'}) + '\n')
    with pytest.raises(ValueError, match='line 3: label'):
        ledger.load(path)


def test_row_verification_states() -> None:
    lead = ledger.Row('x', 1, 1, 'item', 'historical', 'lead:notes')
    canon = ledger.Row('x', 1, 1, 'item', 'guess', 'canon:setting/l7r.md "Money"')
    researched = ledger.Row(
        'x',
        1,
        1,
        'item',
        'historical',
        'https://github.com/EliAndrewC/diagram/blob/main/research/questions/0200-x.html',
    )
    assert (lead.verified, canon.verified, researched.verified) == (False, True, True)
    assert (lead.researched, canon.researched, researched.researched) == (False, False, True)


def test_search_needs_every_word() -> None:
    rows = ledger.load()
    assert {r.item for r in ledger.search(rows, ['SWORD', 'medieval'])} == {
        'a common sword (medieval Lucca and Marseille)'
    }
    assert ledger.search(rows, ['sword', 'nonexistent']) == []


# --- command line --------------------------------------------------------------------------------


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    assert main(list(argv)) == 0
    return capsys.readouterr().out


# The 2017 sheet's basis: Kyoto 1745-54 alone, the whole basket's (arithmetic) reading.
SHEET = ('--reference-only', '--mean', 'arithmetic', '--snapshot', '2017-04')


def test_cli_convert(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, *SHEET, '--basket', 'bassino-ma-a', 'convert', '1', 'koku')
    assert '1 koku = 1.000 koku = 1,000 sen' in out
    assert 'goods $552.39 (whole basket $552.39); wage $9,398; 75.3 laborer-days' in out
    assert 'Rokugan priced by Kyoto 1745-54 alone' in out
    assert 'Bassino & Ma basket A (the 2017 sheet) basket at the 2017-04 snapshot' in out
    assert '[sheet-2017]' in out
    out = run(capsys, 'convert', '1', 'koku')
    assert 'Standard basket at the ' in out
    assert '(geometric mean over goods), up to $' in out
    assert 'Rokugan priced by the eras at their weights' in out
    assert 'left out' not in out
    out = run(capsys, '--snapshot', '2017-04', 'convert', '1', 'koku')
    assert 'unpriced at this date, so left out: Salt, Fuel, Housing' in out


def test_cli_knobs(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, '--koku-kg', 'budgets-polished', '--wage', '7.25', 'convert', '1 koku')
    assert '[budgets-polished]' in out
    assert '$7.25/hour' in out


def test_cli_dated_inputs(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, *SHEET, '--wage-date', '2026-10-18', 'convert', '1 bu')
    assert 'goods $55.24' in out
    with pytest.raises(SystemExit, match='no snapshot dated 1999-01; have 2017-04, '):
        main(['--snapshot', '1999-01', 'convert', '1 bu'])
    with pytest.raises(SystemExit, match="no basket 'nope'; have bassino-ma-a"):
        main(['--basket', 'nope', 'convert', '1 bu'])


def test_cli_dollars(capsys: pytest.CaptureFixture[str]) -> None:
    sheet = (*SHEET, '--basket', 'bassino-ma-a')
    assert '$500.00 (goods dollars) = 9 bu 5 sen (about 9 bu)' in run(
        capsys, *sheet, 'dollars', '500'
    )
    out = run(capsys, 'dollars', '10000', '--wage-dollars')
    assert '(wage dollars) = 1 koku 6 zeni 4 sen' in out


def test_cli_price(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, *SHEET, '--basket', 'bassino-ma-a', 'price', 'sword')
    assert 'a common sword (medieval Lucca and Marseille): 7 sen to 5 zeni 3 sen per item' in out
    assert '[comparative (unverified lead): a yardstick from another society' in out
    assert 'goods $3.87 to $29.28 (whole basket $3.87 to $29.28); wage $66 to $498;' in out
    assert "a samurai's wakizashi: 1 koku 5 bu per item" in out
    out = run(capsys, 'price', 'land', 'tax')
    assert '[guess]' in out
    assert 'notes:' in out
    assert 'derive from neighbors' in run(capsys, 'price', 'gladius')


def test_cli_history_and_check(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, '--reference-only', '--basket', 'bassino-ma-a', 'history')
    assert '2017-04: basket $797.22 = 144.32 zeni -> $552.39 per koku, whole basket' in out
    assert 'left out' not in out
    assert 'left out: Salt, Fuel, Housing' in run(capsys, 'history')
    assert 'snapshots and' in run(capsys, 'check')


# --- consistency rules ---------------------------------------------------------------------------


def test_real_rules_hold() -> None:
    """FR-011 at the standard: every rule over the real ledger holds."""
    assert rules.violations(rules.load_rules(), ledger.load()) == []
    assert len(rules.load_rules()) >= 15


def test_violations_name_the_rule_and_rows() -> None:
    silk = ledger.Row('silk', 2000, 3000, 'length', 'guess', 'lead:x', id='silk')
    kimono = ledger.Row('kimono', 1500, 4000, 'item', 'guess', 'lead:x', id='kimono')
    rule = rules.Rule('a kimono costs at least its silk', 'kimono', (('silk', 1.0),))
    assert rules.violations([rule], [silk, kimono]) == [
        'a kimono costs at least its silk: kimono starts at 1500 sen, below its floor of 2000 sen'
    ]
    ghost = rules.Rule('needs a ghost', 'kimono', (('ghost', 1.0),))
    assert rules.violations([ghost], [kimono]) == ['needs a ghost: no row with id ghost']


def test_duplicate_ids_are_refused(tmp_path: Path) -> None:
    path = tmp_path / 'ledger.jsonl'
    path.write_text(json.dumps({**GOOD, 'id': 'a'}) + '\n' + json.dumps({**GOOD, 'id': 'a'}) + '\n')
    with pytest.raises(ValueError, match="line 2: duplicate id 'a'"):
        ledger.load(path)


def test_derived_rows_are_not_verified() -> None:
    row = ledger.Row('x', 1, 1, 'item', 'guess', 'derived:questions.md#arrows', id='x')
    assert ledger.problems({**GOOD, 'source': 'derived:questions.md#arrows'}) == []
    assert not row.verified


def test_cli_check_fails_on_a_broken_rule(monkeypatch: pytest.MonkeyPatch) -> None:
    broken = rules.Rule('always broken', 'wage-unskilled-day', (('wage-skilled-day', 100.0),))
    monkeypatch.setattr('l7r.money.__main__.load_rules', lambda: [broken])
    with pytest.raises(SystemExit, match='broken consistency rules:\n  always broken'):
        main(['check'])


def test_cli_marks_source_and_synthesis_rows(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, 'price', 'valet', 'kanazawa')
    assert 'source row: synthesize before answering' in out
    out = run(capsys, 'price', 'stabling')
    assert (
        'stabling a horse for the night: 1 zeni 2 sen to 2 zeni per night  [guess (derived)]' in out
    )


def test_parse_names_the_missing_coin() -> None:
    # A SILENT finding typed as "--low 0" failed with no hint that a coin was missing.
    with pytest.raises(ValueError, match='nothing found is "0 sen"'):
        coins.parse('0')


def test_swing_notes_load_and_the_specific_class_wins() -> None:
    """GM 2026-10-24 (diagram#15): a price says how far its good swung across periods, and why."""
    swings = ledger.load_swings()
    salt = ledger.Row('salt', 1, 1, 'sho', 'guess', 'lead:x', tags=('food', 'salt'))
    assert (found := ledger.swing_for(salt, swings)) is not None
    assert found.cls == 'salt'
    assert 'monopoly' in found.note
    assert ledger.swing_for(ledger.Row('a sword', 1, 1, 'item', 'guess', 'lead:x'), swings) is None


@pytest.mark.parametrize(
    'line',
    [
        '{"class": "x", "tags": ["a"], "verdict": "wild", "note": "n", "source": "'
        + ledger.DIAGRAM
        + '"}',
        '{"class": "x", "tags": [], "verdict": "steady", "note": "n", "source": "'
        + ledger.DIAGRAM
        + '"}',
        '{"class": "x", "tags": ["a"], "verdict": "steady", "note": "n", "source": "lead:x"}',
        '{"class": "x", "tags": ["a"], "verdict": "steady", "note": "n"}',
    ],
)
def test_a_bad_swing_note_is_refused(tmp_path: Path, line: str) -> None:
    path = tmp_path / 'swings.jsonl'
    path.write_text('\n' + line + '\n')  # a blank line is skipped, and counted
    with pytest.raises(ValueError, match='swings.jsonl line 2'):
        ledger.load_swings(path)


def test_price_prints_the_swing_note_once(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, 'price', 'salt')
    assert out.count('across periods (salt: swung)') == 1
    assert 'across periods' not in run(capsys, 'price', 'sword')

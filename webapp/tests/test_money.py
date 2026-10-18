"""The `/money` skill's arithmetic and data (feature 219)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from l7r.money import coins, ledger
from l7r.money.__main__ import main
from l7r.money.readings import (
    KOKU_KG,
    Wage,
    big_deal_per_koku,
    load_snapshots,
    load_wages,
    ppp_per_koku,
    resolve_koku_kg,
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


def test_2017_snapshot_reproduces_the_spreadsheet() -> None:
    """SC-001: $797.22 = 144.32 zeni -> $552 per koku, at the sheet's own koku mass."""
    snap = load_snapshots()[0]
    assert snap.date == '2017-04'
    assert round(snap.dollars, 2) == 797.22
    assert round(snap.silver_g, 3) == 325.816
    kg, label = resolve_koku_kg(None)
    assert label == 'sheet-2017'
    assert round(snap.zeni(kg), 2) == 144.32
    assert round(ppp_per_koku(snap, kg)) == 552


def test_forty_gallons_of_uncooked_rice_gives_about_440() -> None:
    snap = load_snapshots()[0]
    assert round(ppp_per_koku(snap, KOKU_KG['forty-gallons'])) == 442


def test_resolve_koku_kg_takes_a_number() -> None:
    assert resolve_koku_kg('150') == (150.0, '150 kg')
    assert resolve_koku_kg(180.5) == (180.5, '180.5 kg')


def test_big_deal_default_is_the_handoff_derivation() -> None:
    """SC-002: ~$9,400 at $15/hour full time over 3.32 koku per unskilled year."""
    wage = load_wages()[-1]
    assert wage.hourly == 15.0
    assert abs(big_deal_per_koku(wage) - 9400) / 9400 < 0.01
    assert big_deal_per_koku(Wage('x', 10.0, 2000, '', ''), 2.0) == 10_000


def test_newest_snapshot_is_last(tmp_path: Path) -> None:
    raw = json.loads((Path(__file__).parents[1] / 'l7r/money/data/baskets/2017-04.json').read_text())
    (tmp_path / '2017-04.json').write_text(json.dumps(raw))
    (tmp_path / '2026-10.json').write_text(json.dumps({**raw, 'date': '2026-10'}))
    assert [s.date for s in load_snapshots(tmp_path)] == ['2017-04', '2026-10']


def test_no_snapshots_is_loud(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_snapshots(tmp_path)


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
        'x', 1, 1, 'item', 'historical',
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


def test_cli_convert(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, 'convert', '1', 'koku')
    assert '1 koku = 1.000 koku = 1,000 sen' in out
    assert 'PPP $552.39; "big deal" $9,398; 75.3 laborer-days' in out
    assert 'snapshot 2017-04' in out and '[sheet-2017]' in out


def test_cli_knobs(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, '--koku-kg', 'forty-gallons', '--wage', '7.25', 'convert', '1 koku')
    assert '[forty-gallons]' in out and '$7.25/hour' in out


def test_cli_dated_inputs(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, '--snapshot', '2017-04', '--wage-date', '2026-10-18', 'convert', '1 bu')
    assert 'PPP $55.24' in out
    with pytest.raises(SystemExit, match='no snapshot dated 1999-01; have 2017-04'):
        main(['--snapshot', '1999-01', 'convert', '1 bu'])


def test_cli_dollars(capsys: pytest.CaptureFixture[str]) -> None:
    assert '$500.00 (PPP) = 9 bu 5 sen (about 9 bu)' in run(capsys, 'dollars', '500')
    out = run(capsys, 'dollars', '10000', '--big-deal')
    assert '("big deal") = 1 koku 6 zeni 4 sen' in out


def test_cli_price(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, 'price', 'sword')
    assert 'a common sword (medieval Lucca and Marseille): 7 sen to 5 zeni 3 sen per item' in out
    assert '[historical (unverified lead)]' in out
    assert 'PPP $3.87 to $29.28; "big deal" $66 to $498; 0.5 to 4.0 laborer-days' in out
    assert "a samurai's wakizashi: 1 koku 5 bu per item" in out
    out = run(capsys, 'price', 'land', 'tax')
    assert '[guess]' in out and 'notes:' in out
    assert 'derive from neighbors' in run(capsys, 'price', 'gladius')


def test_cli_history_and_check(capsys: pytest.CaptureFixture[str]) -> None:
    assert '2017-04: basket $797.22 = 144.32 zeni -> $552.39 per koku' in run(capsys, 'history')
    assert 'ledger ok:' in run(capsys, 'check')

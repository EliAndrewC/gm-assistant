"""The estimate log and calibration (feature 220)."""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import pytest

from l7r.money import calibration as cal
from l7r.money.__main__ import main
from l7r.money.basket import load

ROOT = Path(__file__).parents[1]


def est(eid: str, low: int, high: int, category: str = 'weapons') -> cal.Estimate:
    return cal.Estimate(
        eid, '2026-10-18', 'x', 'what does x cost?', low, high, 'item', category, 'm'
    )


def fnd(
    eid: str, low: int, high: int, verdict: str = 'ATTESTED', date: str = '2026-11-01'
) -> cal.Finding:
    return cal.Finding(
        eid, date, low, high, 'https://github.com/EliAndrewC/diagram/blob/main/q.html', verdict
    )


# --- the measures --------------------------------------------------------------------------------


def test_grade_bias_spread_and_hit_rate() -> None:
    """SC-002: hand-computed. E1 guesses 2x high (inside? no), E2 2x low, E3 exact."""
    estimates = [est('E0001', 20, 20), est('E0002', 5, 5), est('E0003', 8, 12, 'food')]
    findings = [fnd('E0001', 10, 10), fnd('E0002', 10, 10), fnd('E0003', 10, 10)]
    weapons, food, every = cal.grade(estimates, findings)
    assert (weapons.group, weapons.n) == ('weapons', 2)
    assert weapons.bias == pytest.approx(1.0)  # 2x high and 2x low cancel
    assert weapons.spread == pytest.approx(2.0)  # but each misses by a factor of two
    assert weapons.hit_rate == 0
    assert food.bias == pytest.approx(1.0)
    assert food.spread == pytest.approx(1.0)
    assert food.hit_rate == 1
    assert every.n == 3
    assert every.spread == pytest.approx(2.0)
    assert every.hit_rate == pytest.approx(1 / 3)


def test_consistent_bias_shows_its_direction() -> None:
    estimates = [est(f'E000{i}', 30, 30) for i in range(1, 4)]
    findings = [fnd(f'E000{i}', 10, 10) for i in range(1, 4)]
    (weapons, _every) = cal.grade(estimates, findings)
    assert weapons.bias == pytest.approx(3.0)
    assert math.isclose(weapons.spread, 3.0)


def test_only_counted_findings_grade_and_the_latest_wins() -> None:
    estimates = [est('E0001', 10, 10), est('E0002', 10, 10), est('E0003', 0, 0)]
    findings = [
        fnd('E0001', 40, 40, date='2026-11-01'),
        fnd('E0001', 10, 10, date='2026-12-01'),
        fnd('E0002', 99, 99, verdict='SILENT'),
        fnd('E0003', 5, 5),
    ]
    grades = cal.grade(estimates, findings)
    assert [(g.group, g.n, g.bias) for g in grades] == [('weapons', 1, 1.0), ('all', 1, 1.0)]
    assert cal.grade(estimates, []) == []


# --- the files -----------------------------------------------------------------------------------


def test_append_and_load_round_trip(tmp_path: Path) -> None:
    path = tmp_path / 'e.jsonl'
    e = cal.Estimate(
        'E0001', 'd', 'arrow', 'q?', 4, 8, 'arrow', 'weapons', 'm', ('arrow-war',), {'k': 'v'}
    )
    cal.append(path, e)
    assert cal.load_estimates(path) == [e]
    assert cal.next_id([e]) == 'E0002'
    assert cal.next_id([]) == 'E0001'
    assert cal.load_estimates(tmp_path / 'missing.jsonl') == []


GOOD = {
    'id': 'E0001',
    'date': 'd',
    'item': 'x',
    'question': 'q',
    'low': 1,
    'high': 2,
    'per': 'item',
    'category': 'food',
    'method': 'm',
}


@pytest.mark.parametrize(
    ('change', 'complaint'),
    [
        ({'id': '7'}, 'id must look like'),
        ({'low': 3}, 'low/high'),
        ({'category': 'snacks'}, 'category must be'),
        ({'method': ' '}, 'question and method'),
        ({'rows': 'a,b'}, 'rows must be a list'),
    ],
)
def test_bad_estimates_are_refused(
    tmp_path: Path, change: dict[str, object], complaint: str
) -> None:
    path = tmp_path / 'e.jsonl'
    path.write_text(json.dumps({**GOOD, **change}) + '\n')
    with pytest.raises(ValueError, match=complaint):
        cal.load_estimates(path)


def test_duplicate_estimate_ids_are_refused(tmp_path: Path) -> None:
    path = tmp_path / 'e.jsonl'
    path.write_text(json.dumps(GOOD) + '\n' + json.dumps(GOOD) + '\n')
    with pytest.raises(ValueError, match='duplicate id E0001'):
        cal.load_estimates(path)


@pytest.mark.parametrize(
    ('raw', 'complaint'),
    [
        (
            {
                'estimate': 'E0009',
                'issue': 'https://github.com/EliAndrewC/diagram/issues/3',
                'date': 'd',
            },
            'no estimate',
        ),
        ({'estimate': 'E0001', 'issue': 'https://example.com/3', 'date': 'd'}, 'diagram issue URL'),
    ],
)
def test_bad_links_are_refused(tmp_path: Path, raw: dict[str, object], complaint: str) -> None:
    path = tmp_path / 'r.jsonl'
    path.write_text(json.dumps(raw) + '\n')
    with pytest.raises(ValueError, match=complaint):
        cal.load_links([est('E0001', 1, 1)], path)


FGOOD = {
    'estimate': 'E0001',
    'date': 'd',
    'low': 1,
    'high': 2,
    'source': 'https://x',
    'verdict': 'ATTESTED',
}


@pytest.mark.parametrize(
    ('change', 'complaint'),
    [
        ({'estimate': 'E0009'}, 'no estimate'),
        ({'verdict': 'PROBABLY'}, 'verdict must be'),
        ({'comparative': True}, 'comparative source cannot grade'),
        ({'source': 'my notes'}, 'question file URL'),
        ({'high': 0}, 'low/high'),
    ],
)
def test_bad_findings_are_refused(
    tmp_path: Path, change: dict[str, object], complaint: str
) -> None:
    path = tmp_path / 'f.jsonl'
    path.write_text(json.dumps({**FGOOD, **change}) + '\n')
    with pytest.raises(ValueError, match=complaint):
        cal.load_findings([est('E0001', 1, 1)], path)


def test_rewritten_catches_edits_and_deletions() -> None:
    assert cal.rewritten('a\nb\n', 'a\nb\nc\n') == []
    assert cal.rewritten('a\nb\n', 'a\nB\n') == ['line 2: b']
    assert cal.rewritten('a\nb\n', 'a\n') == ['line 2: b']


def test_committed_estimates_are_never_rewritten() -> None:
    """FR-004 at the standard: the working log only grows from what git HEAD holds."""
    rel = 'webapp/l7r/money/data/estimates.jsonl'
    try:
        committed = subprocess.run(
            ['git', '-C', str(ROOT), 'show', f'HEAD:{rel}'],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (
        OSError,
        subprocess.CalledProcessError,
    ):  # pragma: no cover - no git, or not yet committed
        pytest.skip('estimate log not in git HEAD')
    assert cal.rewritten(committed, cal.ESTIMATES.read_text()) == []


def test_real_logs_load() -> None:
    estimates = cal.load_estimates()
    links = cal.load_links(estimates)
    cal.load_findings(estimates)
    assert {lk.estimate for lk in links} == {e.id for e in estimates}, 'every estimate has an issue'


# --- command line --------------------------------------------------------------------------------


@pytest.fixture
def logs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for name in ('ESTIMATES', 'REQUESTS', 'FINDINGS', 'WITHDRAWN'):
        monkeypatch.setattr(cal, name, tmp_path / f'{name.lower()}.jsonl')
    monkeypatch.setattr('l7r.money.__main__._today', lambda: '2026-10-19')
    return tmp_path


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    assert main(list(argv)) == 0
    return capsys.readouterr().out


def test_cli_estimate_link_finding_calibration(
    logs: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = run(capsys, 'calibration')
    assert 'nothing graded yet' in out
    for n in range(3):
        out = run(
            capsys,
            'estimate',
            '--item',
            f'tsuba {n}',
            '--question',
            'a replacement handguard?',
            '--low',
            '3 bu',
            '--high',
            '6 bu',
            '--per',
            'item',
            '--category',
            'weapons',
            '--method',
            'iron + 2 skilled days',
            '--rows',
            'wage-skilled-day',
        )
    assert 'E0003: tsuba 2 = 3 bu to 6 bu per item [weapons] logged' in out
    saved = cal.load_estimates()[0]
    assert saved.model == {
        'snapshot': load().snapshot().date,
        'basket': 'standard',
        'koku_kg': 'sheet-2017',
        'wage': '2026-10-18',
        'laborer_koku_year': '3.32',
    }
    assert saved.date == '2026-10-19'
    assert saved.rows == ('wage-skilled-day',)
    assert 'NO ISSUE FILED' in run(capsys, 'estimates')
    issue = 'https://github.com/EliAndrewC/diagram/issues/9'
    assert 'linked E0001, E0002, E0003' in run(capsys, 'link', issue, 'E0001', 'E0002', 'E0003')
    for n in (1, 2, 3):
        run(
            capsys,
            'finding',
            f'E000{n}',
            '--low',
            '1 bu',
            '--high',
            '2 bu',
            '--source',
            'https://github.com/EliAndrewC/diagram/blob/main/q.html',
            '--verdict',
            'ATTESTED',
        )
    out = run(capsys, 'estimates')
    assert 'finding 1 bu to 2 bu (ATTESTED)' in out
    assert run(capsys, 'estimates', '--open') == ''
    out = run(capsys, 'calibration')
    assert '3 estimates logged (0 withdrawn), 3 graded by research' in out
    assert (
        'weapons: n=3, guesses run 3.00x high, typical miss 3.00x, research inside our range 0%'
        in out
    )
    assert '<- revise this recipe' in out


def test_cli_low_bias_reads_as_low(logs: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run(
        capsys,
        'estimate',
        '--item',
        'apple',
        '--question',
        'apples?',
        '--low',
        '1 sen',
        '--per',
        'apple',
        '--category',
        'food',
        '--method',
        'm',
    )
    run(capsys, 'link', 'https://github.com/EliAndrewC/diagram/issues/9', 'E0001')
    run(
        capsys,
        'finding',
        'E0001',
        '--low',
        '2 sen',
        '--source',
        'https://x',
        '--verdict',
        'ATTESTED',
    )
    out = run(capsys, 'calibration')
    assert 'food: n=1, guesses run 2.00x low' in out
    assert 'revise' not in out


def test_cli_refusals(logs: Path) -> None:
    with pytest.raises(SystemExit, match='no estimate E0042'):
        main(['link', 'https://github.com/EliAndrewC/diagram/issues/9', 'E0042'])
    with pytest.raises(SystemExit, match='no estimate E0042'):
        main(['finding', 'E0042', '--low', '1 sen', '--source', 'https://x', '--verdict', 'SILENT'])
    with pytest.raises(SystemExit, match='low is above high'):
        main(
            [
                'estimate',
                '--item',
                'x',
                '--question',
                'q',
                '--low',
                '2 sen',
                '--high',
                '1 sen',
                '--per',
                'item',
                '--category',
                'food',
                '--method',
                'm',
            ]
        )


def test_today_is_an_iso_date() -> None:
    from l7r.money.__main__ import _today

    assert len(_today()) == 10


def test_withdrawn_estimates_are_not_graded(logs: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for item in ('a', 'b'):
        run(
            capsys,
            'estimate',
            '--item',
            item,
            '--question',
            'q',
            '--low',
            '1 sen',
            '--per',
            'x',
            '--category',
            'food',
            '--method',
            'm',
        )
        run(
            capsys,
            'finding',
            'E0001' if item == 'a' else 'E0002',
            '--low',
            '2 sen',
            '--source',
            'https://x',
            '--verdict',
            'ATTESTED',
        )
    assert 'withdrew E0001: not from this model' in run(
        capsys, 'withdraw', '--reason', 'not from this model', 'E0001'
    )
    out = run(capsys, 'calibration')
    assert '2 estimates logged (1 withdrawn), 1 graded by research' in out
    assert 'food: n=1' in out
    assert 'E0001 2026-10-19 [food] a: WITHDRAWN' in run(capsys, 'estimates')
    assert 'E0001' not in run(capsys, 'estimates', '--open')
    with pytest.raises(SystemExit, match='no estimate E0042'):
        main(['withdraw', '--reason', 'r', 'E0042'])


def test_bad_withdrawals_are_refused(tmp_path: Path) -> None:
    path = tmp_path / 'w.jsonl'
    path.write_text(json.dumps({'estimate': 'E0009', 'date': 'd', 'reason': 'r'}) + '\n')
    with pytest.raises(ValueError, match='no estimate'):
        cal.load_withdrawn([est('E0001', 1, 1)], path)
    path.write_text(json.dumps({'estimate': 'E0001', 'date': 'd', 'reason': ' '}) + '\n')
    with pytest.raises(ValueError, match='needs a reason'):
        cal.load_withdrawn([est('E0001', 1, 1)], path)

"""Command line for the `/money` skill. Run from `webapp/`: `python3 -m l7r.money <command>`.

Every dollar figure names what it rests on (the basket snapshot and koku mass, or the wage), so
an answer pasted into a conversation carries its own basis.
"""

from __future__ import annotations

import argparse
import datetime
import sys
from collections.abc import Sequence
from typing import Protocol

from l7r.money import calibration as cal
from l7r.money import coins, ledger
from l7r.money.readings import (
    LABORER_KOKU_YEAR,
    Snapshot,
    Wage,
    big_deal_per_koku,
    laborer_days,
    load_snapshots,
    load_wages,
    ppp_per_koku,
    resolve_koku_kg,
)
from l7r.money.rules import load_rules, violations

__all__ = ['main']


def _say(text: str) -> None:
    sys.stdout.write(text + '\n')


class _Dated(Protocol):
    @property
    def date(self) -> str: ...


class _Basis:
    def __init__(self, args: argparse.Namespace) -> None:
        snapshots = load_snapshots()
        self.snapshot: Snapshot = _pick(snapshots, args.snapshot, 'snapshot')
        wage: Wage = _pick(load_wages(), args.wage_date, 'wage')
        if args.wage is not None:
            wage = Wage(wage.date, args.wage, wage.hours_per_year, 'given on the command line', '')
        self.wage = wage
        self.koku_kg, self.koku_label = resolve_koku_kg(args.koku_kg)
        self.ppp = ppp_per_koku(self.snapshot, self.koku_kg)
        self.big = big_deal_per_koku(self.wage)

    def lines(self) -> list[str]:
        return [
            f'  PPP basis: basket snapshot {self.snapshot.date}, '
            f'priced by {self.snapshot.priced_by}; '
            f'koku of rice = {self.koku_kg:.1f} kg [{self.koku_label}] '
            f'-> ${self.ppp:,.0f} per koku',
            f'  "Big deal" basis: ${self.wage.hourly:.2f}/hour '
            f'x {self.wage.hours_per_year:g} hours '
            f'({self.wage.date}) / {LABORER_KOKU_YEAR} koku per unskilled year '
            f'-> ${self.big:,.0f} per koku',
        ]

    def dollars(self, low: int, high: int | None = None) -> str:
        lo, hi = coins.koku(low), coins.koku(low if high is None else high)

        def span(per: float, places: int) -> str:
            a, b = f'${lo * per:,.{places}f}', f'${hi * per:,.{places}f}'
            return a if a == b else f'{a} to {b}'

        days = laborer_days(low), laborer_days(low if high is None else high)
        work = f'{days[0]:,.1f}' if days[0] == days[1] else f'{days[0]:,.1f} to {days[1]:,.1f}'
        return f'PPP {span(self.ppp, 2)}; "big deal" {span(self.big, 0)}; {work} laborer-days'


def _pick[T: _Dated](items: Sequence[T], date: str | None, what: str) -> T:
    if date is None:
        return items[-1]
    for item in items:
        if item.date == date:
            return item
    raise SystemExit(f'no {what} dated {date}; have {", ".join(i.date for i in items)}')


def _span(low: int, high: int) -> str:
    if low == high:
        return coins.everyday(low)
    return f'{coins.everyday(low)} to {coins.everyday(high)}'


def _convert(args: argparse.Namespace, basis: _Basis) -> None:
    sen = coins.parse(' '.join(args.amount))
    _say(f'{coins.fmt(sen)} = {coins.koku(sen):,.3f} koku = {sen:,} sen')
    _say(f'  {basis.dollars(sen)}')
    _say('\n'.join(basis.lines()))


def _dollars(args: argparse.Namespace, basis: _Basis) -> None:
    per = basis.big if args.big_deal else basis.ppp
    sen = round(args.dollars / per * 1000)
    kind = '"big deal"' if args.big_deal else 'PPP'
    _say(f'${args.dollars:,.2f} ({kind}) = {coins.fmt(sen)} ({coins.everyday(sen)})')
    _say('\n'.join(basis.lines()))


def _price(args: argparse.Namespace, basis: _Basis) -> None:
    rows = ledger.load()
    found = ledger.search(rows, args.words)
    if not found:
        _say(
            f'no ledger row matches {" ".join(args.words)!r}: '
            'derive from neighbors, label it a guess'
        )
        return
    for row in found:
        if row.source.startswith('derived:'):
            flag = ' (derived)'
        else:
            flag = '' if row.verified else ' (unverified lead)'
        if row.label == 'comparative':
            flag += ': a yardstick from another society, not a Rokugani price'
        elif not row.id:
            flag += '; source row: synthesize before answering'
        _say(f'{row.item}: {_span(row.low, row.high)} per {row.per}  [{row.label}{flag}]')
        _say(f'  {basis.dollars(row.low, row.high)}')
        _say(f'  source: {row.source}')
        if row.notes:
            _say(f'  notes: {row.notes}')
    _say('\n'.join(basis.lines()))


def _history(args: argparse.Namespace, basis: _Basis) -> None:
    for snap in load_snapshots():
        zeni = snap.zeni(basis.koku_kg)
        _say(
            f'{snap.date}: basket ${snap.dollars:,.2f} = {zeni:.2f} zeni -> '
            f'${ppp_per_koku(snap, basis.koku_kg):,.2f} per koku ({snap.priced_by})'
        )
    _say(f'  koku of rice = {basis.koku_kg:.1f} kg [{basis.koku_label}]')


def _check(args: argparse.Namespace, basis: _Basis) -> None:
    rows = ledger.load()
    rules = load_rules()
    if broken := violations(rules, rows):
        raise SystemExit('broken consistency rules:\n  ' + '\n  '.join(broken))
    leads = sum(not r.verified for r in rows)
    _say(
        f'ledger ok: {len(rows)} rows, {len(rules)} consistency rules hold, '
        f'{leads} rows still resting on leads or derivations'
    )


def _today() -> str:
    return datetime.date.today().isoformat()


def _estimate(args: argparse.Namespace, basis: _Basis) -> None:
    estimates = cal.load_estimates()
    est = cal.Estimate(
        id=cal.next_id(estimates),
        date=_today(),
        item=args.item,
        question=args.question,
        low=coins.parse(args.low),
        high=coins.parse(args.high or args.low),
        per=args.per,
        category=args.category,
        method=args.method,
        rows=tuple(r for r in (args.rows or '').split(',') if r),
        model={
            'snapshot': basis.snapshot.date,
            'koku_kg': basis.koku_label,
            'wage': basis.wage.date,
            'laborer_koku_year': f'{LABORER_KOKU_YEAR:g}',
        },
    )
    if est.low > est.high:
        raise SystemExit('low is above high')
    cal.append(cal.ESTIMATES, est)
    _say(f'{est.id}: {est.item} = {_span(est.low, est.high)} per {est.per} [{est.category}] logged')
    _say(f'  {basis.dollars(est.low, est.high)}')


def _link(args: argparse.Namespace, basis: _Basis) -> None:
    estimates = cal.load_estimates()
    known = {e.id for e in estimates}
    for eid in args.ids:
        if eid not in known:
            raise SystemExit(f'no estimate {eid}')
        cal.append(cal.REQUESTS, cal.Link(eid, args.issue, _today()))
    cal.load_links(estimates)
    _say(f'linked {", ".join(args.ids)} -> {args.issue}')


def _finding(args: argparse.Namespace, basis: _Basis) -> None:
    estimates = cal.load_estimates()
    if args.id not in {e.id for e in estimates}:
        raise SystemExit(f'no estimate {args.id}')
    finding = cal.Finding(
        args.id,
        _today(),
        coins.parse(args.low),
        coins.parse(args.high or args.low),
        args.source,
        args.verdict,
        args.notes,
    )
    cal.append(cal.FINDINGS, finding)
    cal.load_findings(estimates)
    _say(f'{args.id}: finding {_span(finding.low, finding.high)} ({finding.verdict}) recorded')


def _estimates(args: argparse.Namespace, basis: _Basis) -> None:
    estimates = cal.load_estimates()
    links = {lk.estimate: lk.issue for lk in cal.load_links(estimates)}
    found = {f.estimate: f for f in cal.load_findings(estimates)}
    for e in estimates:
        if args.open and e.id in found:
            continue
        state = (
            f'finding {_span(found[e.id].low, found[e.id].high)} ({found[e.id].verdict})'
            if e.id in found
            else f'awaiting {links.get(e.id, "NO ISSUE FILED")}'
        )
        _say(
            f'{e.id} {e.date} [{e.category}] {e.item}: {_span(e.low, e.high)} per {e.per}; {state}'
        )


def _calibration(args: argparse.Namespace, basis: _Basis) -> None:
    estimates = cal.load_estimates()
    findings = cal.load_findings(estimates)
    grades = cal.grade(estimates, findings)
    graded = {f.estimate for f in findings if f.counts}
    _say(f'{len(estimates)} estimates logged, {len(graded)} graded by research')
    if not grades:
        _say('  nothing graded yet: calibration needs findings (ATTESTED or ATTESTED ONLY FOR)')
        return
    for g in grades:
        direction = 'high' if g.bias >= 1 else 'low'
        factor = g.bias if g.bias >= 1 else 1 / g.bias
        flag = ''
        if g.group != 'all' and g.n >= 3 and (factor > 1.5 or g.spread > 2.0):
            flag = '  <- revise this recipe (calibration.md)'
        _say(
            f'  {g.group}: n={g.n}, guesses run {factor:.2f}x {direction}, typical miss '
            f'{g.spread:.2f}x, research inside our range {g.hit_rate:.0%}{flag}'
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='python3 -m l7r.money', description=__doc__)
    parser.add_argument(
        '--koku-kg', help='sheet-2017 (default), budgets-brown, budgets-polished, or a number of kg'
    )
    parser.add_argument('--snapshot', help='basket snapshot date (default: newest)')
    parser.add_argument('--wage-date', help='wage reading date (default: newest)')
    parser.add_argument('--wage', type=float, help='override the hourly wage, in dollars')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser(
        'convert', help='an amount of coin -> exact coins, koku, both dollar readings'
    )
    p.add_argument('amount', nargs='+')
    p.set_defaults(run=_convert)
    p = sub.add_parser('dollars', help='dollars -> coin')
    p.add_argument('dollars', type=float)
    p.add_argument('--big-deal', action='store_true', help='read the dollars as "big deal" dollars')
    p.set_defaults(run=_dollars)
    p = sub.add_parser('price', help='ledger rows matching every word')
    p.add_argument('words', nargs='+')
    p.set_defaults(run=_price)
    sub.add_parser('history', help='dollars per koku for every snapshot').set_defaults(run=_history)
    sub.add_parser('check', help='validate the ledger').set_defaults(run=_check)
    p = sub.add_parser('estimate', help='log a new estimate (feature 220)')
    p.add_argument('--item', required=True)
    p.add_argument('--question', required=True, help="the GM's question, as asked")
    p.add_argument('--low', required=True, help='an amount, e.g. "4 sen"')
    p.add_argument('--high', help='an amount (default: same as low)')
    p.add_argument('--per', required=True)
    p.add_argument('--category', required=True, choices=cal.CATEGORIES)
    p.add_argument('--method', required=True, help='how the figure was derived')
    p.add_argument('--rows', help='comma-separated ledger row ids it used')
    p.set_defaults(run=_estimate)
    p = sub.add_parser('link', help='record the diagram issue that asks for estimates research')
    p.add_argument('issue')
    p.add_argument('ids', nargs='+')
    p.set_defaults(run=_link)
    p = sub.add_parser('finding', help='record what the research showed for an estimate')
    p.add_argument('id')
    p.add_argument('--low', required=True)
    p.add_argument('--high')
    p.add_argument('--source', required=True, help='the diagram question file URL')
    p.add_argument('--verdict', required=True, choices=cal.VERDICTS)
    p.add_argument('--notes', default='')
    p.set_defaults(run=_finding)
    p = sub.add_parser('estimates', help='list logged estimates and their status')
    p.add_argument('--open', action='store_true', help='only those without a finding')
    p.set_defaults(run=_estimates)
    sub.add_parser('calibration', help='how well our estimates match the research').set_defaults(
        run=_calibration
    )
    args = parser.parse_args(argv)
    args.run(args, _Basis(args))
    return 0


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main())

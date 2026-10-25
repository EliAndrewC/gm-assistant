"""Command line for the `/money` skill. Run from `webapp/`: `python3 -m l7r.money <command>`.

Every dollar figure names what it rests on (the basket, its price snapshot and the koku mass, or
the wage), so an answer pasted into a conversation carries its own basis. The two readings are
GOODS dollars (what a sum buys) and WAGE dollars (how much it matters; "big deal" until 222).
"""

from __future__ import annotations

import argparse
import datetime
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from l7r.money import basket as bk
from l7r.money import bls, coins, conversions, ledger
from l7r.money import calibration as cal
from l7r.money.readings import (
    LABORER_KOKU_YEAR,
    Wage,
    laborer_days,
    load_wages,
    resolve_koku_kg,
    wage_dollars_per_koku,
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
        self.model = bk.load()
        self.basket = self.model.basket(args.basket)
        self.snapshot = self.model.snapshot(args.snapshot)
        wage: Wage = _pick(load_wages(), args.wage_date, 'wage')
        if args.wage is not None:
            wage = Wage(wage.date, args.wage, wage.hours_per_year, 'given on the command line', '')
        self.wage = wage
        self.koku_kg, self.koku_label = resolve_koku_kg(args.koku_kg)
        self.reading = bk.reading(self.model, self.basket, self.snapshot, self.koku_kg)
        self.ppp = self.reading.per_koku
        self.big = wage_dollars_per_koku(self.wage)

    def lines(self) -> list[str]:
        left = self.reading.left_out
        unpriced = f'; unpriced at this date, so left out: {", ".join(left)}' if left else ''
        return [
            f'  Goods-dollar basis: {self.basket.name} basket at the {self.snapshot.date} '
            f'snapshot (priced by {self.snapshot.priced_by}){unpriced}; '
            f'koku of rice = {self.koku_kg:.1f} kg [{self.koku_label}] '
            f'-> ${self.ppp:,.0f} per koku',
            f'  Wage-dollar basis: ${self.wage.hourly:.2f}/hour '
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
        return f'goods {span(self.ppp, 2)}; wage {span(self.big, 0)}; {work} laborer-days'


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
    per = basis.big if args.wage_dollars else basis.ppp
    sen = round(args.dollars / per * 1000)
    kind = 'wage dollars' if args.wage_dollars else 'goods dollars'
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
    swings = ledger.load_swings()
    for swing in dict.fromkeys(s for r in found if (s := ledger.swing_for(r, swings))):
        _say(f'across periods ({swing.cls}: {swing.verdict}): {swing.note}')
        _say(f'  source: {swing.source}')
    _say('\n'.join(basis.lines()))


def _history(args: argparse.Namespace, basis: _Basis) -> None:
    for snap in basis.model.snapshots:
        r = bk.reading(basis.model, basis.basket, snap, basis.koku_kg)
        zeni = r.silver * 100 / (basis.koku_kg * basis.model.rice_ref)
        left = f'; left out: {", ".join(r.left_out)}' if r.left_out else ''
        _say(
            f'{snap.date}: basket ${r.dollars:,.2f} = {zeni:.2f} zeni -> '
            f'${r.per_koku:,.2f} per koku ({snap.priced_by}){left}'
        )
    _say(
        f'  {basis.basket.name} basket; koku of rice = {basis.koku_kg:.1f} kg [{basis.koku_label}]'
    )


def _baskets(args: argparse.Namespace, basis: _Basis) -> None:
    for b in basis.model.baskets.values():
        r = bk.reading(basis.model, b, basis.snapshot, basis.koku_kg)
        left = f'; left out: {", ".join(r.left_out)}' if r.left_out else ''
        _say(f'{b.id}: ${r.per_koku:,.2f} per koku ({b.name}){left}')
    _say(f'  snapshot {basis.snapshot.date}; koku of rice = {basis.koku_kg:.1f} kg')


def _reprice(args: argparse.Namespace, basis: _Basis) -> None:
    series = {}
    if not args.offline:  # pragma: no cover - the HTTP boundary; tests pass --offline
        series = {s: bls.latest(bls.fetch(s))[1] for s in bls.SERIES}
    path = bk.reprice(basis.model, args.date, series)
    _say(f'wrote {path.name}: fill each blank price and link, then run `check`')


def _crosscheck(args: argparse.Namespace, basis: _Basis) -> None:
    csvs = {s: bls.fetch(s) for s in bls.SERIES}  # pragma: no cover - the HTTP boundary
    _say('\n'.join(bls.crosscheck(basis.snapshot, csvs)))  # pragma: no cover


def _era(args: argparse.Namespace, basis: _Basis) -> None:
    era = basis.model.era(args.era)
    c = bk.convert(
        basis.model,
        era,
        args.amount,
        args.unit,
        basis.basket,
        basis.snapshot,
        basis.koku_kg,
        basis.wage.day,
    )
    _say(f'{args.amount:g} {args.unit} ({era.title}) = {c.silver_g:,.3f} g of silver')
    _say(
        f'  goods ${c.goods_dollars:,.2f}; wage ${c.wage_dollars:,.2f}; '
        f'in Rokugan {conversions.rokugani(c.rokugan_sen)}'
    )
    left = f' (left out: {", ".join(c.left_out)})' if c.left_out else ''
    _say(
        f'  basket: {basis.basket.name} at {basis.snapshot.date}, priced there on '
        f'{c.coverage}{left}'
    )
    _say(
        f"  wage: a laborer's {era.wage_g_per_day:g} g of silver a day there, against "
        f'${basis.wage.day:,.2f} a US day ({basis.wage.date})'
    )
    if note := era.coins[args.unit].note:
        _say(f'  coin: {note}')
    _say(f'  confidence: {era.confidence}')


def _export(args: argparse.Namespace, basis: _Basis) -> None:
    data = conversions.table(basis.model, basis.basket, basis.snapshot, basis.koku_kg, basis.wage)
    path = conversions.write(data, Path(args.out) if args.out else conversions.TABLE)
    _say(f'wrote {path.name}: {len(data["eras"])} eras')


def _check(args: argparse.Namespace, basis: _Basis) -> None:
    rows = ledger.load()
    swings = ledger.load_swings()
    rules = load_rules()
    if broken := violations(rules, rows):
        raise SystemExit('broken consistency rules:\n  ' + '\n  '.join(broken))
    if bad := bk.problems(basis.model):
        raise SystemExit('baskets, snapshots and eras:\n  ' + '\n  '.join(bad))
    leads = sum(not r.verified for r in rows)
    _say(
        f'ledger ok: {len(rows)} rows, {len(rules)} consistency rules hold, '
        f'{leads} rows still resting on leads or derivations; {len(swings)} swing notes; '
        f'{len(basis.model.baskets)} baskets, {len(basis.model.snapshots)} snapshots and '
        f'{len(basis.model.eras)} eras ok'
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
            'basket': basis.basket.id,
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


def _withdraw(args: argparse.Namespace, basis: _Basis) -> None:
    estimates = cal.load_estimates()
    known = {e.id for e in estimates}
    for eid in args.ids:
        if eid not in known:
            raise SystemExit(f'no estimate {eid}')
        cal.append(cal.WITHDRAWN, cal.Withdrawal(eid, _today(), args.reason))
    _say(f'withdrew {", ".join(args.ids)}: {args.reason}')


def _estimates(args: argparse.Namespace, basis: _Basis) -> None:
    estimates = cal.load_estimates()
    links = {lk.estimate: lk.issue for lk in cal.load_links(estimates)}
    found = {f.estimate: f for f in cal.load_findings(estimates)}
    gone = {w.estimate for w in cal.load_withdrawn(estimates)}
    for e in estimates:
        if args.open and (e.id in found or e.id in gone):
            continue
        if e.id in gone:
            _say(f'{e.id} {e.date} [{e.category}] {e.item}: WITHDRAWN')
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
    gone = {w.estimate for w in cal.load_withdrawn(estimates)}
    grades = cal.grade(estimates, findings, gone)
    graded = {f.estimate for f in findings if f.counts} - gone
    _say(
        f'{len(estimates)} estimates logged ({len(gone)} withdrawn), '
        f'{len(graded)} graded by research'
    )
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
    parser.add_argument('--snapshot', help='price snapshot date (default: newest)')
    parser.add_argument('--basket', help='basket id (default: standard); `baskets` lists them')
    parser.add_argument('--wage-date', help='wage reading date (default: newest)')
    parser.add_argument('--wage', type=float, help='override the hourly wage, in dollars')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser(
        'convert', help='an amount of coin -> exact coins, koku, goods and wage dollars'
    )
    p.add_argument('amount', nargs='+')
    p.set_defaults(run=_convert)
    p = sub.add_parser('dollars', help='dollars -> coin')
    p.add_argument('dollars', type=float)
    p.add_argument(
        '--wage-dollars', action='store_true', help='read the dollars as wage dollars, not goods'
    )
    p.set_defaults(run=_dollars)
    p = sub.add_parser('price', help='ledger rows matching every word')
    p.add_argument('words', nargs='+')
    p.set_defaults(run=_price)
    sub.add_parser('history', help='dollars per koku for every snapshot').set_defaults(run=_history)
    sub.add_parser('baskets', help='dollars per koku for every basket').set_defaults(run=_baskets)
    p = sub.add_parser('reprice', help='start the next dated price snapshot')
    p.add_argument('date', help='YYYY-MM')
    p.add_argument('--offline', action='store_true', help='leave BLS-tied prices blank too')
    p.set_defaults(run=_reprice)
    sub.add_parser(
        'crosscheck', help="the snapshot's rice and beans against BLS averages"
    ).set_defaults(run=_crosscheck)
    p = sub.add_parser('era', help="an era's money -> goods dollars, wage dollars, Rokugani coin")
    p.add_argument('amount', type=float)
    p.add_argument('unit', help='a coin of the era, such as mon, monme, ryo or yen')
    p.add_argument('--era', required=True, help='an era id, such as kyoto-1745')
    p.set_defaults(run=_era)
    p = sub.add_parser('export', help='write the conversion table diagram reads')
    p.add_argument('--out', help='path (default: data/conversions.json)')
    p.set_defaults(run=_export)
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
    p = sub.add_parser('withdraw', help='mark estimates never to be graded, with the reason')
    p.add_argument('--reason', required=True)
    p.add_argument('ids', nargs='+')
    p.set_defaults(run=_withdraw)
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

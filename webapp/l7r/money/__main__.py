"""Command line for the `/money` skill. Run from `webapp/`: `python3 -m l7r.money <command>`.

Every dollar figure names what it rests on (the basket snapshot and koku mass, or the wage), so
an answer pasted into a conversation carries its own basis.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import Protocol

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


def _span(row: ledger.Row) -> str:
    if row.low == row.high:
        return coins.everyday(row.low)
    return f'{coins.everyday(row.low)} to {coins.everyday(row.high)}'


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
        flag = '' if row.verified else ' (unverified lead)'
        if row.label == 'comparative':
            flag += ': a yardstick from another society, not a Rokugani price'
        _say(f'{row.item}: {_span(row)} per {row.per}  [{row.label}{flag}]')
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
    leads = sum(not r.verified for r in rows)
    _say(f'ledger ok: {len(rows)} rows, {leads} still resting on leads')


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='python3 -m l7r.money', description=__doc__)
    parser.add_argument('--koku-kg', help='sheet-2017 (default), forty-gallons, or a number of kg')
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
    args = parser.parse_args(argv)
    args.run(args, _Basis(args))
    return 0


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main())

"""Baskets, price snapshots, eras and the conversion table (feature 222)."""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

from l7r.money import basket as bk
from l7r.money import bls, conversions
from l7r.money.__main__ import main
from l7r.money.readings import KOKU_KG, load_wages

KG = KOKU_KG['sheet-2017']
FIXTURES = Path(__file__).parent / 'fixtures' / 'money'


@pytest.fixture
def model() -> bk.Model:
    return bk.load()


@pytest.fixture
def data(tmp_path: Path) -> Path:
    """A writable copy of the real data directory."""
    shutil.copytree(bk.DATA, tmp_path / 'data')
    return tmp_path / 'data'


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    assert main(list(argv)) == 0
    return capsys.readouterr().out


# --- the standard basket ---------------------------------------------------------------------


def test_standard_basket_is_the_default_and_carries_the_needs(model: bk.Model) -> None:
    """FR-002 / FR-008: salt, fuel and housing are in the standard basket; no luxury is."""
    std = model.basket()
    assert std.id == bk.STANDARD
    assert {'salt', 'fuel', 'housing'} <= set(std.quantities)
    assert not {'pepper', 'sake', 'tea', 'tobacco'} & set(std.quantities)
    assert 'housing' not in model.basket('standard-no-housing').quantities
    assert set(model.basket('bassino-ma-a').quantities) == set(std.quantities) - {
        'salt',
        'fuel',
        'housing',
    }


def test_real_data_has_no_problems(model: bk.Model) -> None:
    """At the standard: every committed snapshot option is priced and linked, every era price
    labeled and sourced (a `reprice` file left half-filled fails here, and so the gate)."""
    assert bk.problems(model) == []


def test_the_reference_eras_new_goods_say_what_is_guessed(model: bk.Model) -> None:
    """diagram#13: Kyoto's salt and firewood are attested (only a koku of salt's weight is guessed);
    no Kyoto or Osaka rent was found, so housing stays a borrowed guess."""
    ref = model.reference
    assert ref.id == 'kyoto-1745'
    assert model.rice_ref == pytest.approx(1.49 * 1.725 / 3.11, abs=1e-4)
    assert ref.coins['monme'].silver_g == 1.725
    for good, label in (('salt', 'guess'), ('fuel', 'historical'), ('housing', 'guess')):
        assert ref.goods[good].label == label
        assert ref.goods[good].note


def test_housing_is_the_largest_lever(model: bk.Model) -> None:
    """research.md: housing nearly doubles the 2026 koku; the variant shows it without."""
    snap = model.snapshot('2026-10')
    with_h = bk.reading(model, model.basket(), snap, KG).whole
    without = bk.reading(model, model.basket('standard-no-housing'), snap, KG).whole
    assert 1.6 < with_h / without < 2.0


# --- readings ------------------------------------------------------------------------------------


def test_reading_takes_substitutes_quantities_and_custom_goods(model: bk.Model) -> None:
    snap, std = model.snapshot('2026-10'), model.basket()
    base = bk.reading(model, std, snap, KG)
    calrose = bk.reading(model, std, snap, KG, choices={'rice': 1})
    assert calrose.dollars > base.dollars  # the default is the cheapest pack (GM 2026-10-24)
    bls = bk.reading(model, std, snap, KG, choices={'rice': 2})
    assert bk.reading(model, std, snap, KG, choices={'rice': 99}).dollars == bls.dollars
    off = bk.reading(model, std, snap, KG, quantities={'fish': 0})
    assert off.dollars == pytest.approx(base.dollars - 3.5 * 19.45)
    assert off.left_out == ()
    sake = bk.Custom('Sake', 'liter', 10, 2.0, 12.0)
    plus = bk.reading(model, std, snap, KG, custom=[sake])
    assert plus.dollars == pytest.approx(base.dollars + 120)
    assert plus.silver == pytest.approx(base.silver + 20)
    half = bk.reading(model, std, snap, KG, custom=[bk.Custom('Tea', 'kg', 1, None, 9.0)])
    assert half.left_out == ('Tea',)
    assert bk.reading(model, bk.Basket('x', 'x', '', {}), snap, KG).per_koku == 0.0


def test_wage_dates_are_checked(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit, match='no wage dated 1999; have 2026-10-18'):
        main(['--wage-date', '1999', 'convert', '1 bu'])


def test_snapshot_price_and_lookups(model: bk.Model) -> None:
    snap = model.snapshot('2017-04')
    assert snap.price('rice') == 2.09
    assert snap.price('salt') is None
    assert snap.price('rice', -3) == 2.09
    with pytest.raises(SystemExit, match="no era 'nope'; have beijing-1500, beijing-1615,"):
        model.era('nope')


# --- era conversion ----------------------------------------------------------------------------


def test_twenty_mon_in_kyoto(model: bk.Model) -> None:
    """User Story 4: 20 mon converts three ways, over the whole basket, in the reference era."""
    day = load_wages()[-1].day
    c = bk.convert(
        model,
        model.era('kyoto-1745'),
        20,
        'mon',
        model.basket(),
        model.snapshot('2026-10'),
        KG,
        day,
    )
    assert c.silver_g == pytest.approx(20 * 1.725 / 72.6, rel=1e-3)
    assert c.wage_dollars == pytest.approx(c.silver_g / model.reference.wage_g_per_day * day)
    assert c.coverage == 'the whole basket'
    # With Kyoto 1745-54 alone, Kyoto is Rokugan: its price level is 1 by either mean.
    ref = model.reference_only()
    snap = model.snapshot('2026-10')
    k = bk.convert(
        model,
        model.era('kyoto-1745'),
        20,
        'mon',
        model.basket(),
        snap,
        KG,
        day,
        weights=ref,
    )
    whole = bk.reading(model, model.basket(), snap, KG, weights=ref)
    assert k.rokugan_sen == pytest.approx(k.silver_g * 1000 / (KG * model.rice_ref))
    assert k.goods_dollars == pytest.approx(k.silver_g / whole.koku_silver * whole.geometric)
    assert k.goods_dollars_high == pytest.approx(k.silver_g * whole.dollars / whole.silver)


def test_a_partly_priced_era_says_so(model: bk.Model) -> None:
    """User Story 4 scenario 2: Tokyo 1882-86 has no salt, fuel or housing price."""
    day = load_wages()[-1].day
    c = bk.convert(
        model,
        model.era('tokyo-1882'),
        1,
        'yen',
        model.basket(),
        model.snapshot('2026-10'),
        KG,
        day,
    )
    assert c.coverage == '9 of 12 goods'
    assert c.left_out == ('Salt', 'Fuel', 'Housing')
    # dearer than Kyoto by Bassino & Ma's own basket ratio (277 against 326 g: cheaper, in fact)
    a = model.basket('bassino-ma-a')
    t = bk.convert(
        model,
        model.era('tokyo-1882'),
        1,
        'yen',
        a,
        model.snapshot('2026-10'),
        KG,
        day,
        mean='arithmetic',
        weights=model.reference_only(),
    )
    assert t.rokugan_sen == pytest.approx(25 * 325.816 / 277.4 * 1000 / (KG * 1.49), rel=0.01)


def test_rice_alone_and_refusals(model: bk.Model) -> None:
    day = load_wages()[-1].day
    rice = bk.Basket('r', 'Rice', '', {'rice': 1, 'salt': 0})
    era, snap = model.era('tokyo-1882'), model.snapshot('2026-10')
    rice_era = bk.Era('x', 'X', '1', False, '', era.coins, {'rice': era.goods['rice']}, 4.5, '')
    c = bk.convert(model, rice_era, 1, 'yen', model.basket(), snap, KG, day)
    assert c.coverage == 'rice alone'
    assert bk.convert(model, era, 1, 'yen', rice, snap, KG, day).coverage == 'the whole basket'
    with pytest.raises(SystemExit, match="has no coin 'mon'; have yen, sen, rin"):
        bk.convert(model, era, 1, 'mon', rice, snap, KG, day)
    with pytest.raises(SystemExit, match='prices none of basket'):
        bk.convert(model, era, 1, 'yen', bk.Basket('s', 'S', '', {'salt': 1}), snap, KG, day)


# --- the conversion table ------------------------------------------------------------------------


def test_committed_table_is_current(model: bk.Model) -> None:
    """FR-013: data/conversions.json is generated; regenerate with `python3 -m l7r.money export`."""
    wage = load_wages()[-1]
    fresh = conversions.table(model, model.basket(), model.snapshot(), KG, wage)
    assert json.loads(conversions.TABLE.read_text()) == json.loads(json.dumps(fresh)), (
        'data/conversions.json is stale: run `python3 -m l7r.money export` from webapp/'
    )
    kyoto = fresh['eras']['kyoto-1745']
    assert kyoto['basket_coverage'] == 'the whole basket'
    assert set(kyoto['units']) == {'monme', 'mon', 'kanmon', 'ryo', 'bu', 'shu'}
    assert fresh['eras']['tokyo-1882']['goods_left_out'] == ['Salt', 'Fuel', 'Housing']


def test_every_era_carries_the_coins_diagram_marks(model: bk.Model) -> None:
    """diagram marks amounts by `data-coin`; a coin its era lacks is an error on diagram's side."""
    for era in model.eras.values():
        if 'monme' in era.coins:
            assert {'monme', 'mon', 'kanmon', 'ryo', 'bu', 'shu'} <= set(era.coins), era.id
        elif 'tael' in era.coins:
            assert {'tael', 'cash'} <= set(era.coins), era.id
    for era_id in ('canton-1835', 'beijing-1900'):
        assert 'dollar' in model.era(era_id).coins


def test_goods_dollars_agree_with_the_rokugani_coin_in_every_era(model: bk.Model) -> None:
    """An era's grams are valued at Rokugan's whole-basket rate, so a partly priced era's dollars
    are the koku's headline dollars at its Rokugani sum, never rice dollars alone."""
    snap, day = model.snapshot('2026-10'), load_wages()[-1].day
    per_koku = bk.reading(model, model.basket(), snap, KG).per_koku
    for era in model.eras.values():
        for unit in era.coins:
            c = bk.convert(model, era, 1, unit, model.basket(), snap, KG, day)
            assert c.goods_dollars == pytest.approx(c.rokugan_sen / 1000 * per_koku), (era.id, unit)


@pytest.mark.parametrize(
    ('sen', 'text'),
    [(4.17, '4.2 sen'), (0.04, '0.0 sen'), (130.6, 'about 1 bu 3 zeni'), (1000, '1 koku')],
)
def test_rokugani_names_the_coins(sen: float, text: str) -> None:
    assert conversions.rokugani(sen) == text


# --- problems --------------------------------------------------------------------------------


def test_problems_catch_each_defect(data: Path) -> None:
    def edit(rel: str, change: object) -> None:
        path = data / rel
        raw = json.loads(path.read_text())
        change(raw)  # type: ignore[operator]
        path.write_text(json.dumps(raw))

    edit('baskets/standard.json', lambda r: r['goods'].update({'pepper': 1, 'rice': -1}))
    edit(
        'snapshots/2026-10.json',
        lambda r: r['goods'].update(
            {'ghost': [{'priced_as': 'g', 'dollars_per_unit': None, 'link': ''}]}
        ),
    )
    edit(
        'eras/tokyo-1882.json',
        lambda r: (
            r['goods'].update({'ghost': {'silver_g': 1, 'label': 'attested', 'source': ''}}),
            r.update({'coins': {}}),
        ),
    )
    found = bk.problems(bk.load(data))
    for complaint in (
        "basket standard: unknown good 'pepper'",
        'basket standard: negative quantity of rice',
        "snapshot 2026-10: unknown good 'ghost'",
        'snapshot 2026-10: ghost (g) unpriced',
        'snapshot 2026-10: ghost (g) has no link',
        "era tokyo-1882: unknown good 'ghost'",
        "era tokyo-1882: ghost label 'attested' not in",
        'era tokyo-1882: ghost has no source',
        'era tokyo-1882: no coins',
    ):
        assert any(complaint in p for p in found), complaint


def test_problems_need_a_standard_basket_and_one_reference(data: Path) -> None:
    (data / 'baskets' / 'standard.json').unlink()
    raw = json.loads((data / 'eras' / 'tokyo-1882.json').read_text())
    (data / 'eras' / 'tokyo-1882.json').write_text(json.dumps({**raw, 'reference': True}))
    found = bk.problems(bk.load(data))
    assert "no 'standard' basket" in found
    assert any('exactly one era must be the reference' in p for p in found)
    ref = json.loads((data / 'eras' / 'kyoto-1745.json').read_text())
    del ref['goods']['rice']
    (data / 'eras' / 'kyoto-1745.json').write_text(json.dumps(ref))
    (data / 'eras' / 'tokyo-1882.json').write_text(json.dumps(raw))
    assert 'the reference era kyoto-1745 has no rice price' in bk.problems(bk.load(data))


def test_no_snapshots_is_loud(data: Path) -> None:
    shutil.rmtree(data / 'snapshots')
    (data / 'snapshots').mkdir()
    with pytest.raises(FileNotFoundError):
        bk.load(data)


# --- reprice -------------------------------------------------------------------------------------


def test_reprice_starts_a_blank_snapshot(data: Path) -> None:
    """User Story 2: every good of every basket, blank, and `check` refuses it until filled; an
    option tied to a BLS series is filled from it."""
    model = bk.load(data)
    path = bk.reprice(model, '2027-10', {'APU0000701312': 1.2}, data)
    raw = json.loads(path.read_text())
    assert set(raw['goods']) == {g for b in model.baskets.values() for g in b.quantities}
    rice = raw['goods']['rice']
    assert [o['dollars_per_unit'] for o in rice] == [None, None, round(1.2 * 2.20462, 3)]
    assert rice[2]['link'] == 'https://fred.stlouisfed.org/series/APU0000701312'
    assert raw['goods']['beans'][0]['dollars_per_unit'] is None  # its series was not fetched
    assert raw['goods']['beans'][0]['link'] == ''
    assert any('2027-10: salt' in p and 'unpriced' in p for p in bk.problems(bk.load(data)))
    with pytest.raises(SystemExit, match='never edited once committed'):
        bk.reprice(model, '2027-10', data=data)


def test_reprice_adds_a_good_the_newest_snapshot_lacks(data: Path) -> None:
    raw = json.loads((data / 'snapshots' / '2026-10.json').read_text())
    del raw['goods']['salt']
    (data / 'snapshots' / '2026-10.json').write_text(json.dumps(raw))
    path = bk.reprice(bk.load(data), '2027-01', data=data)
    assert json.loads(path.read_text())['goods']['salt'] == [
        {'priced_as': '', 'dollars_per_unit': None, 'link': ''}
    ]


# --- BLS -------------------------------------------------------------------------------------


def _fred() -> dict[str, str]:
    return {s: (FIXTURES / f'fred-{s}.csv').read_text() for s in bls.SERIES}


def test_latest_reads_a_saved_fred_file() -> None:
    assert bls.latest(_fred()['APU0000701312']) == ('2026-09', 1.118)
    assert bls.latest('observation_date,X\n2026-01-01,1.0\n2026-02-01,.\n') == ('2026-01', 1.0)
    with pytest.raises(ValueError, match='no observations'):
        bls.latest('observation_date,X\n')


def test_crosscheck_flags_a_price_far_from_the_average(model: bk.Model) -> None:
    lines = bls.crosscheck(model.snapshot('2026-10'), _fred())
    rice = [ln for ln in lines if ln.startswith('rice: Hinode')][0]
    assert '1.01x the BLS average' in rice
    assert 'check this price' not in rice
    adzuki = [ln for ln in lines if ln.startswith('beans: Adzuki')][0]
    assert 'check this price' in adzuki
    assert not any('US city average' in ln for ln in lines)  # the series' own option is skipped


# --- command line --------------------------------------------------------------------------------


def test_cli_baskets_era_and_export(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    out = run(capsys, 'baskets')
    assert 'standard: $' in out
    assert 'standard-no-housing: $' in out
    out = run(capsys, 'era', '20', 'mon', '--era', 'kyoto-1745')
    assert '20 mon (Kyoto 1745-1754) = 0.475 g of silver' in out
    assert '(whole basket $3.32); wage $37.92; in Rokugan 3.8 sen' in out
    assert 'coin: 72.6 mon to the monme' in out
    out = run(capsys, 'era', '1', 'yen', '--era', 'tokyo-1882')
    assert 'priced there on 9 of 12 goods (left out: Salt, Fuel, Housing)' in out
    assert 'coin:' not in out
    out = run(capsys, 'export', '--out', str(tmp_path / 'c.json'))
    assert f'wrote c.json: {len(bk.load().eras)} eras' in out
    assert json.loads((tmp_path / 'c.json').read_text()) == json.loads(
        conversions.TABLE.read_text()
    )


def test_cli_reprice_offline(
    capsys: pytest.CaptureFixture[str], data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bk, 'DATA', data)
    monkeypatch.setattr(bk.reprice, '__defaults__', (None, data))
    out = run(capsys, 'reprice', '2027-10', '--offline')
    assert 'wrote 2027-10.json' in out
    assert (data / 'snapshots' / '2027-10.json').exists()


def test_cli_check_fails_on_basket_problems(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bk, 'problems', lambda m: ['snapshot 2027-10: salt unpriced'])
    with pytest.raises(SystemExit, match='baskets, snapshots and eras:\n  snapshot 2027-10'):
        main(['check'])


def test_era_files_are_what_the_build_script_writes() -> None:
    """The eras are written by specs/222-money-basket-and-section/measure/eras.py, where each
    figure's arithmetic and why live; a hand edit to a file would leave the script stale."""
    script = (
        Path(__file__).resolve().parents[2] / 'specs/222-money-basket-and-section/measure/eras.py'
    )
    spec = importlib.util.spec_from_file_location('money_eras_build', script)
    assert spec
    assert spec.loader
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    eras = bk.DATA / 'eras'
    on_disk = {p.stem for p in eras.glob('*.json')}
    assert on_disk - set(build.ERAS) == build.HAND, (
        'an era file the script does not write: add it to measure/eras.py (or to HAND)'
    )
    for era_id, era in build.ERAS.items():
        assert (eras / f'{era_id}.json').read_text() == build.text(era), (
            f'{era_id}.json differs from measure/eras.py: edit the script and run it, from the '
            'clone root: python3 specs/222-money-basket-and-section/measure/eras.py'
        )


# --- feature 223: the index over goods, two readings, eras averaged in rice ----------------------


def test_reference_only_weights_reproduce_feature_222s_prices(model: bk.Model) -> None:
    """US4 acceptance 1: Kyoto 1745-54 alone at 1 gives back its own prices."""
    prices = model.prices(model.reference_only())
    for good, price in model.reference.goods.items():
        assert prices[good] == pytest.approx(price.silver_g), good
    assert model.prices()['rice'] == pytest.approx(model.rice_ref)  # rice is the anchor, always


def test_a_borrowed_price_is_not_counted_twice(model: bk.Model) -> None:
    """diagram#17 / 0249: Kyoto 1745's fish is a Meiji ratio, so beside Tokyo 1882 it drops out;
    it stands only when nothing else prices fish."""
    assert model.rests_on('fish') == ('beijing-1615', 'beijing-1820', 'canton-1835', 'tokyo-1882')
    assert model.rests_on('fish', model.reference_only()) == ('kyoto-1745',)
    assert model.rests_on('housing') == ('edo-1818', 'kyoto-1745')


def test_an_excluded_price_never_counts(model: bk.Model) -> None:
    """GM 2026-10-25: Tokyo 1882's linen and kerosene are not pre-modern prices. They drop out of
    the cross-era mean, and unlike a borrowed price they do not stand in when nothing else is
    weighted; the era's own conversion still uses them."""
    tokyo = model.eras['tokyo-1882']
    assert tokyo.goods['cloth'].excluded
    assert tokyo.goods['lamp-oil'].excluded
    assert 'tokyo-1882' not in model.rests_on('cloth')
    assert 'tokyo-1882' in model.rests_on('soybeans')
    only = {e: float(e == 'tokyo-1882') for e in model.eras}
    assert model.rests_on('cloth', only) == ()
    assert 'cloth' not in model.prices(only)


def test_era_weights_fall_back_to_the_reference(model: bk.Model) -> None:
    zero = {e: 0.0 for e in model.eras}
    assert model.weights(zero) == model.reference_only()
    assert model.weights({'kyoto-1745': -2})['kyoto-1745'] == 0.0
    assert model.weights()['osaka-1700'] == 1.0


def test_the_whole_basket_is_the_spending_weighted_arithmetic_mean(
    model: bk.Model,
) -> None:
    """The GM's household approach ($D/N) and the spending-weighted average are one number."""
    snap = model.snapshot('2026-10')
    r = bk.reading(model, model.basket(), snap, KG)
    assert r.whole == pytest.approx(r.arithmetic)
    assert r.whole == pytest.approx(r.dollars / r.koku_cost)
    assert sum(w for _, w in r.weighted) == pytest.approx(1)
    rice = next(ln for ln in r.lines if ln.good == 'rice')
    assert r.alone(rice) == pytest.approx(KG * 1.26)  # 151.5 kg at today's default rice price
    assert r.per_koku == r.geometric < r.arithmetic  # the central reading sits below the whole
    eq = bk.reading(model, model.basket(), snap, KG, equal=True)
    assert all(w == pytest.approx(1 / 12) for _, w in eq.weighted)
    assert eq.whole == pytest.approx(r.whole)  # equal weights move the average, not $D/N
    assert bk.reading(model, model.basket(), snap, KG, mean='arithmetic').per_koku == r.arithmetic
    assert bk.reading(model, bk.Basket('x', 'x', '', {}), snap, KG).whole == 0.0
    with pytest.raises(SystemExit, match="no mean 'median'; have geometric, arithmetic"):
        bk.reading(model, model.basket(), snap, KG, mean='median')


def test_era_conversion_follows_the_mean(model: bk.Model) -> None:
    """FR-007: goods_dollars is the central reading, goods_dollars_high the whole basket's."""
    snap, day = model.snapshot('2026-10'), load_wages()[-1].day
    era = model.era('edo-1830')
    geo = bk.convert(model, era, 1, 'monme', model.basket(), snap, KG, day)
    ari = bk.convert(model, era, 1, 'monme', model.basket(), snap, KG, day, mean='arithmetic')
    assert ari.goods_dollars == pytest.approx(ari.goods_dollars_high)
    assert geo.goods_dollars_high == pytest.approx(ari.goods_dollars_high)
    assert geo.goods_dollars < geo.goods_dollars_high


def test_problems_catch_bad_era_weights_and_no_complete_basket(data: Path) -> None:
    (data / 'era-weights.json').write_text(json.dumps({'weights': {'nope': 1, 'osaka-1700': -1}}))
    raw = json.loads((data / 'baskets' / 'standard.json').read_text())
    (data / 'baskets' / 'standard.json').write_text(json.dumps({**raw, 'complete': False}))
    found = bk.problems(bk.load(data))
    assert "era-weights: unknown era 'nope'" in found
    assert 'era-weights: negative weight for osaka-1700' in found
    assert 'no basket is marked complete (the whole-basket reading needs one)' in found
    (data / 'era-weights.json').unlink()
    assert bk.load(data).era_weights == {}


def test_cli_mean_and_weights(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, '--mean', 'arithmetic', '--equal-weights', 'convert', '1 koku')
    assert '(equal-weighted arithmetic mean over goods)' in out
    out = run(capsys, '--reference-only', 'baskets')
    assert '$874.87 for the whole basket (Standard)' in out

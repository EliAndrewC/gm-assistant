"""money.js's `compute` against basket.reading (features 222 FR-016, 223 FR-006): the browser and
the server must give the same koku for the same link. Runs the real script under node."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from l7r.money import basket as bk
from l7r.money import web
from l7r.money.readings import KOKU_KG, load_wages

SCRIPT = Path(__file__).parents[1] / 'l7r' / 'static' / 'js' / 'money.js'
KG = KOKU_KG['sheet-2017']

STATES: list[dict[str, str]] = [
    {},
    {'q_housing': '0'},
    {'x_rice': '2', 'x_cloth': '1', 'q_fish': '0'},
    {'b': 'bassino-ma-a'},
    {'b': 'bassino-ma-a', 'q_housing': '3.31', 'q_salt': '10'},
    {'b': 'standard-no-housing', 'q_rice': '0.5'},
    {'m': 'arithmetic'},
    {'eq': '1', 'q_fish': '0'},
    {'w_kyoto-1745': '0', 'w_canton-1835': '3', 'x_rice': '1'},
    {**{f'w_{e}': '0' for e in bk.load().eras}},
]


SIG3 = [6.6004, 0.041234, 1234.5, 100.2, 99.94, 12345.6, 0.5]


def _js_state(state: web.State) -> dict[str, Any]:
    return {
        'basket': state.basket,
        'snapshot': state.snapshot,
        'q': dict(state.quantities),
        'x': dict(state.choices),
        'mean': state.mean,
        'equal': state.equal,
        'w': dict(state.weights),
        'whole': state.whole,
    }


@pytest.mark.skipif(shutil.which('node') is None, reason='node is not installed')
def test_browser_and_server_agree() -> None:
    model = bk.load()
    data = web.page_data(model, KG, load_wages()[-1])
    states = [web.parse_state(model, params) for params in STATES]
    program = (
        f'const {{compute, computeWhole, drivers, sig3}} = require({json.dumps(str(SCRIPT))});'
        f'const data = {json.dumps(data)};'
        f'const states = {json.dumps([_js_state(s) for s in states])};'
        f'const figures = {json.dumps(SIG3)};'
        'process.stdout.write(JSON.stringify({sig3: figures.map(sig3), readings: states.map(s => {'
        'const r = compute(data, s); r.drivers = drivers(r); r.whole = computeWhole(data, s);'
        'return r; })}));'
    )
    out = json.loads(
        subprocess.run(['node', '-e', program], capture_output=True, check=True, text=True).stdout
    )
    assert out['sig3'] == [web.sig3(x) for x in SIG3]
    for state, js in zip(states, out['readings'], strict=True):
        py = web.state_reading(model, state, KG)
        assert js['dollars'] == pytest.approx(py.dollars)
        assert js['silver'] == pytest.approx(py.silver)
        assert js['per_koku'] == pytest.approx(py.per_koku)
        assert js['arithmetic'] == pytest.approx(py.arithmetic)
        assert js['geometric'] == pytest.approx(py.geometric)
        assert js['koku_cost'] == pytest.approx(py.koku_cost)
        whole = web.whole_reading(model, state, KG)
        assert js['whole']['arithmetic'] == pytest.approx(whole.arithmetic)
        assert js['whole']['dollars'] == pytest.approx(whole.dollars)
        assert js['left_out'] == list(py.left_out)
        assert js['drivers'] == web.drivers(py)

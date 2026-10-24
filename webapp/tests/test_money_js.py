"""money.js's `compute` against basket.reading (feature 221, FR-016): the browser and the server
must give the same koku for the same link. Runs the real script under node."""

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
    {'b': 'bassino-ma-a', 's': '2017-04'},
    {'b': 'bassino-ma-a', 'q_housing': '3.31', 'q_salt': '10'},
    {'s': '2017-04', 'c1': 'Sake|liter|20|2|12', 'c2': 'Tea|kg|1||9'},
    {'b': 'standard-no-housing', 'q_rice': '0.5'},
]


def _js_state(state: web.State) -> dict[str, Any]:
    return {
        'basket': state.basket,
        'snapshot': state.snapshot,
        'q': dict(state.quantities),
        'x': dict(state.choices),
        'custom': [
            {'name': c.name, 'qty': c.quantity, 'silver': c.silver_g, 'dollars': c.dollars}
            for c in state.custom
            if c is not None
        ],
    }


@pytest.mark.skipif(shutil.which('node') is None, reason='node is not installed')
def test_browser_and_server_agree() -> None:
    model = bk.load()
    data = web.page_data(model, KG, load_wages()[-1])
    states = [web.parse_state(model, params) for params in STATES]
    program = (
        f'const {{compute, drivers}} = require({json.dumps(str(SCRIPT))});'
        f'const data = {json.dumps(data)};'
        f'const states = {json.dumps([_js_state(s) for s in states])};'
        'process.stdout.write(JSON.stringify(states.map(s => {'
        'const r = compute(data, s); r.drivers = drivers(r); return r; })));'
    )
    out = json.loads(
        subprocess.run(['node', '-e', program], capture_output=True, check=True, text=True).stdout
    )
    for state, js in zip(states, out, strict=True):
        py = web.state_reading(model, state, KG)
        assert js['dollars'] == pytest.approx(py.dollars)
        assert js['silver'] == pytest.approx(py.silver)
        assert js['per_koku'] == pytest.approx(py.per_koku)
        assert js['left_out'] == list(py.left_out)
        assert js['drivers'] == web.drivers(py)

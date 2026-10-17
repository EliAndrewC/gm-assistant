"""The Discord bot ships to a box running Python 3.12, not this repository's 3.14.

`scripts/deploy_mention_bot.sh` copies `l7r/mention` and `l7r/lookup` to the
GM's Lightsail box, whose interpreter is the Ubuntu system Python (3.12.3,
measured 2026-10-17). Code that only parses on 3.14 - PEP 758's unparenthesized
`except A, B:`, which `ruff format` writes on its own when targeting py314 -
would crash-loop the bot on import while every gate here stays green. Measured
the same day: `ruff format` rewrote `except (OSError, ValueError):` in
l7r/lookup/ledger.py into the 3.14-only form. pyproject.toml pins both packages
to py312 for ruff; this test is the guard that does not depend on that config.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

WEBAPP = Path(__file__).resolve().parent.parent
BOX_PYTHON = (3, 12)
SHIPPED = sorted(
    p
    for package in ('l7r/mention', 'l7r/lookup')
    for p in (WEBAPP / package).rglob('*.py')
    if '__pycache__' not in p.parts
)


def test_the_shipped_packages_exist() -> None:
    assert len(SHIPPED) > 20


@pytest.mark.parametrize('path', SHIPPED, ids=lambda p: str(p.relative_to(WEBAPP)))
def test_parses_on_the_box_python(path: Path) -> None:
    ast.parse(path.read_text(encoding='utf-8'), str(path), feature_version=BOX_PYTHON)

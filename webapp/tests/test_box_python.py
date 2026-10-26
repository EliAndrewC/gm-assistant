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
import re
from pathlib import Path

import pytest

WEBAPP = Path(__file__).resolve().parent.parent
BOX_PYTHON = (3, 12)
DEPLOY = WEBAPP.parent / 'scripts' / 'deploy_mention_bot.sh'
# What the deploy script copies, read from the script itself (never a second list kept here).
COPIED = re.findall(r'cp (?:-r )?"\$REPO/webapp/(l7r/[\w/.]+)"', DEPLOY.read_text(encoding='utf-8'))
SHIPPED = sorted(
    p
    for item in COPIED
    for p in ([WEBAPP / item] if item.endswith('.py') else (WEBAPP / item).rglob('*.py'))
    if '__pycache__' not in p.parts
)


def _module(path: Path) -> str:
    return '.'.join(path.relative_to(WEBAPP).with_suffix('').parts).removesuffix('.__init__')


def test_the_shipped_packages_exist() -> None:
    assert len(SHIPPED) > 20


@pytest.mark.parametrize('path', SHIPPED, ids=lambda p: str(p.relative_to(WEBAPP)))
def test_parses_on_the_box_python(path: Path) -> None:
    ast.parse(path.read_text(encoding='utf-8'), str(path), feature_version=BOX_PYTHON)


def test_the_box_has_every_l7r_module_it_imports() -> None:
    """2026-10-26: bots.py began importing l7r.inifile, which the deploy did not copy - the bot
    would have crash-looped on the box on its next deploy with every gate here green. Module-level
    imports only: a function-level import (bake.py's l7r.app) runs here, not on the box."""
    assert 'l7r/mention' in COPIED
    assert 'l7r/lookup' in COPIED
    shipped = {_module(p) for p in SHIPPED}
    missing = []
    for path in SHIPPED:
        for node in ast.parse(path.read_text(encoding='utf-8')).body:
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else []
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            for name in names:
                if name.startswith('l7r.') and not any(
                    name == m or name.startswith(m + '.') or m.startswith(name + '.')
                    for m in shipped
                ):
                    missing.append(f'{path.relative_to(WEBAPP)} imports {name}')
    assert missing == [], (
        f'not copied by scripts/deploy_mention_bot.sh, so the bot cannot import it: {missing}. '
        'Add a cp line for it next to the l7r/mention one.'
    )

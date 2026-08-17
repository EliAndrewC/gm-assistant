"""Guard: the shared library must never import a tier generator.

`hamletgen` (and `villagegen`, `towngen`, `citygen` when they exist) import `sitegen`. The reverse
is forbidden, and this test is why it stays forbidden rather than merely discouraged.

A cycle here would not fail loudly - Python resolves plenty of them - it would just make the SHARED
library depend on whichever tier happened to be written first, which is precisely the coupling this
package was created to avoid. By the time anyone noticed, the second tier generator would already
be importing hamlet assumptions through the back door.
"""

from __future__ import annotations

import ast
from pathlib import Path

TIER_GENERATORS = {"hamletgen", "villagegen", "towngen", "citygen", "capitalgen"}
SITEGEN = Path(__file__).resolve().parents[2] / "l7r" / "diagram" / "sitegen"


def _imported_modules(tree: ast.AST) -> list[str]:
    """Every module an import statement could reach - INCLUDING the names in a `from X import Y`.

    That last part is the whole subtlety, and this guard was written without it and duly passed
    while `from l7r.diagram import hamletgen` sat in a sitegen module: for an `ImportFrom`, the
    tier's name is in `node.names`, not in `node.module`. Both forms are how a cycle would actually
    get written, so both are collected. Found by proving this test RED before trusting it.
    """
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.append(node.module)
            out.extend(f'{node.module or ""}.{a.name}' for a in node.names)
    return out


def test_sitegen_never_imports_a_tier_generator() -> None:
    offenders: list[str] = []
    files = sorted(SITEGEN.rglob('*.py'))
    assert files, f'no sitegen modules found under {SITEGEN} - this guard would pass vacuously'
    for path in files:
        for module in _imported_modules(ast.parse(path.read_text())):
            if TIER_GENERATORS & set(module.split('.')):
                offenders.append(f'{path.name} imports {module}')
    assert not offenders, (
        'sitegen imports a TIER GENERATOR, which inverts the dependency the shared library exists '
        f'to establish: {offenders}. Whatever is needed either belongs in the tier generator, or '
        'should be MOVED down into sitegen (never copied). See l7r/diagram/sitegen/__init__.py.'
    )

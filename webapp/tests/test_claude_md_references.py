"""Error messages that send a session to "CLAUDE.md 'some phrase'" must find that phrase there.

Why: hooks and guards end their block messages with a pointer such as CLAUDE.md 'Session clones'.
When CLAUDE.md was trimmed on 2026-10-17 two of those pointers stopped resolving, and nothing would
have said so - a session following the tip would have found nothing. The references are read from
the sources, never listed here.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REF = re.compile(r"""CLAUDE\.md,? (?:section )?(?:'([^']+)'|"([^"]+)")""")


def sources() -> list[Path]:
    files = sorted((ROOT / 'scripts').glob('*.sh')) + sorted((ROOT / 'webapp').rglob('*.py'))
    skip = {'env', '.venv', 'node_modules'}
    return [p for p in files if not p.name.startswith('test') and not skip & set(p.parts)]


def test_some_references_exist() -> None:
    assert any(REF.search(p.read_text()) for p in sources())


def test_every_claude_md_reference_resolves() -> None:
    text = (ROOT / 'CLAUDE.md').read_text()
    missing = sorted(
        f'{p.relative_to(ROOT)}: {m}'
        for p in sources()
        for m in (a or b for a, b in REF.findall(p.read_text()))
        if m not in text
    )
    assert not missing, f'these messages point at CLAUDE.md phrases that no longer exist: {missing}'

"""Every INI file here is read with ConfigObj (`l7r.inifile.read_ini`), never configparser.

Why: development-secrets.ini writes values in quotes (`api_key = "AIza..."`). ConfigObj, which
chargen uses for that file, strips them; configparser keeps them. Twice a configparser read sent a
Gemini key to Google with its quotes and got `API_KEY_INVALID` for a key that worked everywhere
else (feature 218's bot, and feature 228's shrine builder on 2026-10-26, which cost a wrong
diagnosis and a needless workaround). configparser also lowercases keys and rejects the top-level
keys development-defaults.ini opens with. webapp/CLAUDE.md said "use ConfigObj" all along; this
test is what makes it hold.

Matches IMPORTS (parsed, not grepped), so a comment or docstring naming configparser is fine. The
files come from `git ls-files`, so a new module is checked the moment it is tracked.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

from l7r.inifile import read_ini

REPO_ROOT = Path(__file__).resolve().parents[2]


def tracked_python() -> list[Path]:
    out = subprocess.run(
        ['git', '-C', str(REPO_ROOT), 'ls-files', '*.py'],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [REPO_ROOT / line for line in out.splitlines() if line]


def imports_configparser(source: str) -> list[int]:
    lines = []
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Import)
            and any(a.name.split('.')[0] == 'configparser' for a in node.names)
            or isinstance(node, ast.ImportFrom)
            and (node.module or '').split('.')[0] == 'configparser'
        ):
            lines.append(node.lineno)
    return lines


def test_the_check_fires() -> None:
    assert imports_configparser('import configparser\n') == [1]
    assert imports_configparser('def f():\n    from configparser import ConfigParser\n') == [2]
    assert imports_configparser('"""configparser keeps quotes"""\n# import configparser\n') == []


def test_no_module_reads_ini_with_configparser() -> None:
    files = tracked_python()
    assert len(files) > 100, 'git ls-files found too few files; the census would pass vacuously'
    offenders = [
        f'{path.relative_to(REPO_ROOT)}:{line}'
        for path in files
        if path.exists()
        for line in imports_configparser(path.read_text(encoding='utf-8'))
    ]
    assert offenders == [], (
        'Read INI files with l7r.inifile.read_ini (ConfigObj), not configparser: it keeps '
        'the quotes development-secrets.ini writes around values (a quoted API key reaches Google '
        'with its quotes and is rejected as invalid), lowercases keys, and rejects the top-level '
        f'keys of development-defaults.ini. Offending imports: {offenders}'
    )


# --- the reader ---------------------------------------------------------------------------------


def test_read_ini_strips_quotes_and_keeps_case_and_percent(tmp_path: Path) -> None:
    path = tmp_path / 'x.ini'
    path.write_text(
        'top = level\n[empty]\n[s]\nKey = "AIza-1"\nsingle = \'two\'\n'
        'cookie = a%20b\nlisted = "a, b"\n',
        encoding='utf-8',
    )
    assert read_ini(path) == {
        '': {'top': 'level'},
        'empty': {},
        's': {'Key': 'AIza-1', 'single': 'two', 'cookie': 'a%20b', 'listed': 'a, b'},
    }


def test_read_ini_missing_file_is_empty(tmp_path: Path) -> None:
    assert read_ini(tmp_path / 'absent.ini') == {}


def test_read_ini_refuses_an_unquoted_comma(tmp_path: Path) -> None:
    path = tmp_path / 'x.ini'
    path.write_text('[x]\ncookie = a, b\n', encoding='utf-8')
    with pytest.raises(ValueError, match='written in quotes, e.g. cookie = "a, b"'):
        read_ini(path)

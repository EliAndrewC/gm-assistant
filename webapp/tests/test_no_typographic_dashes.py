"""Guard against em-dashes (U+2014) and en-dashes (U+2013) anywhere in the project.

Per CLAUDE.md, the project uses ASCII hyphens (-) only. This test walks the
repo and fails if any typographic dash sneaks back in via a future edit.

The literal characters are constructed via `chr()` here so the test source
itself does not contain them and thus does not trip its own guard.
"""

import os
from pathlib import Path

import pytest

EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)

REPO_ROOT = Path(__file__).resolve().parents[2]

# File extensions worth scanning - anything that ships as content, code, docs, or config.
EXTENSIONS = {
    '.md',
    '.py',
    '.html',
    '.jinja',
    '.j2',
    '.txt',
    '.css',
    '.js',
    '.jsonl',
    '.json',
}

# Directories to prune during the walk.
SKIP_DIRS = {
    '.git',
    '__pycache__',
    '.venv',
    'venv',
    'env',
    'node_modules',
    '.cache',
    '.next',
    'dist',
    'build',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache',
}

# Files to skip entirely. This test file is in the list because it must
# mention the characters by name in its docstring above.
SKIP_FILES = {Path(__file__).resolve()}

SOURCE_OPEN = '<!-- SOURCE: GM NOTES - DO NOT MODIFY -->'
SOURCE_CLOSE = '<!-- END SOURCE -->'


def _strip_source_blocks(text: str) -> str:
    """Remove content between SOURCE: GM NOTES markers.

    The GM's original writing inside those markers is frozen and may legitimately
    contain typographic dashes if the GM wrote them that way. The test should not
    fail on those.
    """
    out_parts = []
    cursor = 0
    while True:
        start = text.find(SOURCE_OPEN, cursor)
        if start == -1:
            out_parts.append(text[cursor:])
            break
        out_parts.append(text[cursor:start])
        end = text.find(SOURCE_CLOSE, start)
        if end == -1:
            # Unclosed SOURCE block - treat rest of file as protected.
            break
        cursor = end + len(SOURCE_CLOSE)
    return ''.join(out_parts)


def _scan_repo() -> list[tuple[Path, int, str, str]]:
    """Return (path, line_number, char_name, line_text) for every offending line."""
    findings: list[tuple[Path, int, str, str]] = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1]
            if ext not in EXTENSIONS:
                continue
            path = Path(dirpath) / fn
            if path.resolve() in SKIP_FILES:
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except (UnicodeDecodeError, PermissionError):
                continue
            if EM_DASH not in text and EN_DASH not in text:
                continue
            scrubbed = _strip_source_blocks(text)
            for lineno, line in enumerate(scrubbed.splitlines(), start=1):
                if EM_DASH in line:
                    findings.append((path, lineno, 'em-dash (U+2014)', line))
                if EN_DASH in line:
                    findings.append((path, lineno, 'en-dash (U+2013)', line))
    return findings


def test_no_typographic_dashes_in_repo() -> None:
    """Fail if any em-dash or en-dash appears in tracked content files."""
    findings = _scan_repo()
    if not findings:
        return
    # Format a useful error message: up to 20 examples + total count.
    lines = [f'Found {len(findings)} typographic dash occurrence(s):']
    for path, lineno, char_name, line_text in findings[:20]:
        rel = path.relative_to(REPO_ROOT)
        snippet = line_text.strip()[:120]
        lines.append(f'  {rel}:{lineno} [{char_name}]: {snippet}')
    if len(findings) > 20:
        lines.append(f'  ... and {len(findings) - 20} more')
    lines.append('')
    lines.append('Project policy (CLAUDE.md): hyphens only. Replace with - (U+002D).')
    pytest.fail('\n'.join(lines))

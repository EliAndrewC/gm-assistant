"""Which source sections the glossary has read, and which have changed since.

The glossary is built by reading `l7r.md` and the rules section by section. A
refresh should reread only what moved, so every section a session has reviewed
is recorded in `reviewed.json` with a hash of its text at the time. A section
whose hash no longer matches - or that has never been reviewed - is stale.

    python3 -m l7r.lookup.sources stale              # what needs reading
    python3 -m l7r.lookup.sources mark FILE [PREFIX] # record sections as read

Recording is per SECTION rather than per glossary entry because many sections
hold nothing a player would look up (a budget table, a long story); those still
need to count as read, or they would be reported as stale forever.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

REVIEWED = Path(__file__).resolve().parent / 'reviewed.json'

#: The GM's `l7r` repository: `setting/l7r.md` and `rules/*.md` are read from it.
#: Bind-mounted in the dev container; `L7R_REPO` overrides it.
REPO = Path(os.environ.get('L7R_REPO', '/host-l7r-repo'))

_HEADING = re.compile(r'^(#{1,4})\s+(.+?)\s*$')


@dataclass(frozen=True)
class Section:
    file: str
    heading: str
    text: str

    @property
    def sha(self) -> str:
        return digest(self.text)


def digest(text: str) -> str:
    """A short, whitespace-insensitive hash: re-wrapping a paragraph is not a change."""
    return hashlib.sha256(' '.join(text.split()).encode()).hexdigest()[:12]


def split(text: str, file: str) -> list[Section]:
    """`text` cut at headings (levels 1-4), each section named by its heading path.

    A path like `The Wasp Bounty Hunters Campaign > Bounties` keeps two
    same-named headings in different chapters apart; a repeat inside one chapter
    gets ` #2`. Text before the first heading is the `(preamble)` section. A
    fenced code block is not scanned for headings, so a `#` comment inside one
    does not cut a section."""
    sections: list[Section] = []
    path: list[tuple[int, str]] = []
    heading = '(preamble)'
    lines: list[str] = []
    seen: dict[str, int] = {}
    fenced = False

    def close() -> None:
        # A heading with nothing under it before the next heading (a chapter title
        # followed straight by its first subsection) has nothing to read.
        content = lines[1:] if heading != '(preamble)' else lines
        if '\n'.join(content).strip():
            sections.append(Section(file, heading, '\n'.join(lines).strip()))

    for raw in text.splitlines():
        if raw.lstrip().startswith('```'):
            fenced = not fenced
        match = None if fenced else _HEADING.match(raw)
        if match is None:
            lines.append(raw)
            continue
        close()
        level, title = len(match.group(1)), match.group(2)
        path = [p for p in path if p[0] < level] + [(level, title)]
        name = ' > '.join(t for _, t in path)
        seen[name] = seen.get(name, 0) + 1
        heading = name if seen[name] == 1 else f'{name} #{seen[name]}'
        lines = [raw]
    close()
    return sections


def corpus(repo: Path = REPO) -> list[Section]:
    """Every section of every source file, `setting/l7r.md` first, then the rules."""
    files = [repo / 'setting' / 'l7r.md', *sorted((repo / 'rules').glob('*.md'))]
    out: list[Section] = []
    for path in files:
        out.extend(split(path.read_text(encoding='utf-8'), str(path.relative_to(repo))))
    return out


def load_reviewed(path: Path = REVIEWED) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    data: dict[str, dict[str, str]] = json.loads(path.read_text(encoding='utf-8'))
    return data


def save_reviewed(reviewed: dict[str, dict[str, str]], path: Path = REVIEWED) -> None:
    ordered = {f: dict(sorted(reviewed[f].items())) for f in sorted(reviewed)}
    path.write_text(json.dumps(ordered, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')


def stale(sections: Iterable[Section], reviewed: dict[str, dict[str, str]]) -> list[Section]:
    """The sections never reviewed, or reviewed when their text was different."""
    return [s for s in sections if reviewed.get(s.file, {}).get(s.heading) != s.sha]


def mark(
    sections: Iterable[Section],
    reviewed: dict[str, dict[str, str]],
    file: str,
    prefix: str = '',
) -> list[Section]:
    """Record every section of `file` whose heading starts with `prefix` as read.

    Returns what was marked, so the caller can say so; marking nothing is almost
    always a typo in the prefix, and the CLI treats it as an error."""
    marked = [s for s in sections if s.file == file and s.heading.startswith(prefix)]
    for s in marked:
        reviewed.setdefault(file, {})[s.heading] = s.sha
    return marked


def main(
    argv: list[str],
    *,
    load_corpus: Callable[[], list[Section]] = corpus,
    reviewed_path: Path = REVIEWED,
    out: Callable[[str], None] = print,
) -> int:
    sections = load_corpus()
    reviewed = load_reviewed(reviewed_path)
    if argv[:1] == ['stale']:
        pending = stale(sections, reviewed)
        for s in pending:
            out(f'{s.file}  {s.heading}  ({len(s.text.split())} words)')
        words = sum(len(s.text.split()) for s in pending)
        out(f'{len(pending)} of {len(sections)} sections stale ({words} words to read)')
        return 0
    if argv[:1] == ['mark'] and len(argv) in (2, 3):
        marked = mark(sections, reviewed, argv[1], argv[2] if len(argv) == 3 else '')
        if not marked:
            out(f'no section of {argv[1]} starts with {argv[2:]!r}; nothing marked')
            return 1
        save_reviewed(reviewed, reviewed_path)
        out(f'marked {len(marked)} section(s) of {argv[1]} as reviewed')
        return 0
    out('usage: python3 -m l7r.lookup.sources stale | mark FILE [HEADING-PREFIX]')
    return 2


if __name__ == '__main__':  # pragma: no cover - the CLI entry point
    raise SystemExit(main(sys.argv[1:]))

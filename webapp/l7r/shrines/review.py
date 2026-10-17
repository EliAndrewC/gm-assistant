"""Inputs for the `shrine-text-review` subagent (spec FR-039): one file per wizard section.

    python3 -m l7r.shrines.review OUT_DIR

writes OUT_DIR/<group>.txt with the section's PLAYER-FACING text only (labels, prompts, notes,
option text, appeals and every wording replacement - never a price line). Each review call then
launches the `shrine-text-review` agent by type with only "review OUT_DIR/<group>.txt" as its
prompt: the definition body is the subagent's system prompt, the only part that caches across
calls (docs/subagent-caching.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

from l7r.shrines.catalog import Catalog, Group, load_catalog
from l7r.shrines.design import moot_note

__all__ = ['main', 'section_text']


def _worded(owner: object, indent: str) -> list[str]:
    wording: dict[str, dict[str, str]] = getattr(owner, 'wording')  # noqa: B009
    return [
        f'{indent}[{name} wording] {field}: {text}'
        for name, fields in wording.items()
        for field, text in fields.items()
    ]


def section_text(catalog: Catalog, group: Group) -> str:
    lines = [f'Section "{group.key}": {group.label}', f'  intro: {group.intro}']
    lines += _worded(group, '    ')
    for category in group.categories:
        lines += [
            '',
            f'STEP {category.key} - label: {category.label}',
            f'  prompt: {category.prompt}',
        ]
        if category.decides:
            lines.append(f'  decides: {category.decides}')
        note = moot_note(catalog, category)
        if note:
            lines.append(f'  appears only when: {note}')
        lines += _worded(category, '    ')
        for option in category.options:
            term = f' [{option.ja} {option.romaji}]'.rstrip() if option.ja or option.romaji else ''
            lines.append(f'  OPTION {option.key} - label: {option.label}{term}')
            if option.when:
                rules = '; '.join(
                    f'{c.key} {"not " if c.negate else ""}in {sorted(c.options)}'
                    for c in option.when
                )
                lines.append(f'    offered only when: {rules}')
            lines.append(f'    text: {option.text}')
            if option.appeal:
                lines.append(f'    appeal: {option.appeal}')
            lines += _worded(option, '      ')
    return '\n'.join(lines) + '\n'


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        sys.stderr.write('usage: python3 -m l7r.shrines.review OUT_DIR\n')
        return 2
    out = Path(args[0])
    out.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()
    for group in catalog.groups:
        (out / f'{group.key}.txt').write_text(section_text(catalog, group), encoding='utf-8')
        sys.stdout.write(f'{out / group.key}.txt\n')
    return 0


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())

"""Name pool reader for the Names section.

Reads the two JSONL pools maintained by `/.claude/skills/name/`:
- pool-male.jsonl
- pool-female.jsonl

Each line is a JSON object: {name, gender, format, explanation, notes, peasant}.
"""

from __future__ import annotations

import json
import logging
import random as _random
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = ('name', 'gender', 'format', 'explanation')


def _slugify(text: str) -> str:
    """Lowercase + alphanumeric-only slug, with non-word runs collapsed to hyphens."""
    out: list[str] = []
    last_was_dash = True
    for ch in text.lower():
        if ch.isalnum():
            out.append(ch)
            last_was_dash = False
        elif not last_was_dash:
            out.append('-')
            last_was_dash = True
    return ''.join(out).strip('-')


@dataclass(frozen=True, slots=True)
class GeneratedName:
    """One name from the pool, with its format-derived explanation."""

    name: str
    gender: str
    format: int
    explanation: str
    peasant: bool
    notes: str

    @property
    def slug(self) -> str:
        """Stable URL slug for this entry, used by the picked-pick anchor.

        Format: <gender>-<name>. Distinct genders disambiguate any name that
        happens to appear in both pools. The format/peasant axes are not part
        of the slug because the GM picks names by *meaning*, not by which
        traditional naming format was used - showing the first hit is fine.
        """
        return f'{self.gender}-{_slugify(self.name)}'


def find_name_by_slug(names: list[GeneratedName], slug: str) -> GeneratedName | None:
    """Return the first GeneratedName whose slug matches, or None."""
    for name in names:
        if name.slug == slug:
            return name
    return None


def random_name(
    names: list[GeneratedName],
    rng: _random.Random | None = None,
) -> GeneratedName | None:
    """Pick one name uniformly at random. Returns None if the list is empty."""
    if not names:
        return None
    chooser = rng if rng is not None else _random
    return chooser.choice(names)


def load_names(pool_dir: Path) -> list[GeneratedName]:
    """Load all names from <pool_dir>/pool-male.jsonl and pool-female.jsonl.

    Returns a list sorted by name. Lines missing required fields are skipped
    with a logged warning.
    """
    if not pool_dir.exists() or not pool_dir.is_dir():
        return []

    names: list[GeneratedName] = []
    for filename in ('pool-male.jsonl', 'pool-female.jsonl'):
        path = pool_dir / filename
        if not path.exists():
            continue
        names.extend(_load_jsonl(path))
    names.sort(key=lambda n: (n.gender, n.name))
    return names


def _load_jsonl(path: Path) -> list[GeneratedName]:
    """Parse one JSONL file. Skip and log bad lines."""
    result: list[GeneratedName] = []
    try:
        text = path.read_text(encoding='utf-8')
    except OSError:
        logger.warning('names %s: could not read file', path)
        return result

    for line_no, raw in enumerate(text.splitlines(), 1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning('names %s:%d: JSON parse error (%s)', path, line_no, exc)
            continue
        missing = [f for f in _REQUIRED_FIELDS if f not in entry]
        if missing:
            logger.warning('names %s:%d: missing %s, skipping', path, line_no, missing)
            continue
        result.append(
            GeneratedName(
                name=str(entry['name']),
                gender=str(entry['gender']),
                format=int(entry['format']),
                explanation=str(entry['explanation']),
                peasant=bool(entry.get('peasant', False)),
                notes=str(entry.get('notes', '')),
            )
        )
    return result

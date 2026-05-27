"""Relic pool reader.

Parses markdown files at <pool_dir>/<fortune>/*.md into Relic dataclasses.
Each file has YAML frontmatter delimited by `---` lines and a prose body.

Files missing required frontmatter fields are skipped with a warning rather
than crashing the loader — see Constitution Principle X.7 (no swallowed
exceptions, but graceful degradation on bad data is the right call here).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)$', re.DOTALL)

_REQUIRED_FIELDS = (
    'name',
    'japanese_romaji',
    'japanese_kanji',
    'fortune',
    'clan',
    'temple',
    'named_entity',
    'relic_type',
)


@dataclass(frozen=True, slots=True)
class Relic:
    """One relic, loaded from a pool markdown file."""

    slug: str
    name: str
    japanese_romaji: str
    japanese_kanji: str
    fortune: str
    clan: str
    temple: str
    named_entity: str
    relic_type: str
    description: str


def load_relics(pool_dir: Path) -> list[Relic]:
    """Load all relics from <pool_dir>/<fortune>/*.md.

    Returns a list sorted by slug. Files missing required frontmatter fields
    or with unparseable YAML are skipped with a logged warning.
    """
    if not pool_dir.exists() or not pool_dir.is_dir():
        return []

    relics: list[Relic] = []
    for fortune_dir in sorted(pool_dir.iterdir()):
        if not fortune_dir.is_dir():
            continue
        for md_path in sorted(fortune_dir.glob('*.md')):
            relic = _load_one(md_path)
            if relic is not None:
                relics.append(relic)

    relics.sort(key=lambda r: r.slug)
    return relics


def _load_one(md_path: Path) -> Relic | None:
    """Parse one markdown file. Returns None if the file is unusable."""
    try:
        text = md_path.read_text(encoding='utf-8')
    except OSError:
        logger.warning('relic %s: could not read file', md_path)
        return None

    match = _FRONTMATTER_RE.match(text)
    if match is None:
        logger.warning('relic %s: no frontmatter found, skipping', md_path)
        return None

    frontmatter_raw, body = match.groups()
    try:
        frontmatter: dict[str, Any] = yaml.safe_load(frontmatter_raw) or {}
    except yaml.YAMLError as exc:
        logger.warning('relic %s: YAML parse error (%s), skipping', md_path, exc)
        return None

    missing = [f for f in _REQUIRED_FIELDS if f not in frontmatter]
    if missing:
        logger.warning('relic %s: missing required fields %s, skipping', md_path, missing)
        return None

    return Relic(
        slug=md_path.stem,
        name=str(frontmatter['name']),
        japanese_romaji=str(frontmatter['japanese_romaji']),
        japanese_kanji=str(frontmatter['japanese_kanji']),
        fortune=str(frontmatter['fortune']),
        clan=str(frontmatter['clan']),
        temple=str(frontmatter['temple']),
        named_entity=str(frontmatter['named_entity']),
        relic_type=str(frontmatter['relic_type']),
        description=body.strip(),
    )

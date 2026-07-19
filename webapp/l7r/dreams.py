"""Dream-scene pool reader for the public Dreams gallery.

Parses the PUBLIC dream-scene markdown files at `<pool_dir>/*.md` into
`DreamScene` dataclasses, mirroring `l7r.pool` (relics). Each file has YAML
frontmatter delimited by `---` lines and a markdown body.

Spoiler boundary (feature FR-007): this loader reads ONLY the single pool
directory it is given. It never globs subdirectories and never walks to a
sibling `pool-local/` tier, so the live-campaign spoiler scenes cannot reach
the public site. Files missing required frontmatter are skipped with a logged
warning (graceful degradation, as in `l7r.pool`).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from markdown_it import MarkdownIt

logger = logging.getLogger(__name__)

_FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)$', re.DOTALL)

_REQUIRED_FIELDS = ('name', 'title', 'sender')

# CommonMark plus tables, with raw-HTML passthrough DISABLED. The scene bodies
# are trusted GM/dev-authored markdown, but keeping `html=False` means any
# stray angle-bracket text is escaped rather than injected - defense in depth.
_MD = MarkdownIt('commonmark', {'html': False}).enable('table')


def render_markdown(text: str) -> str:
    """Render trusted markdown to HTML; raw HTML in the source is escaped."""
    return str(_MD.render(text))


@dataclass(frozen=True, slots=True)
class DreamScene:
    """One public, worked example scene, loaded from a pool markdown file."""

    slug: str
    name: str
    title: str
    sender: str
    sender_type: str
    summary: str
    body_html: str


def load_dream_scenes(pool_dir: Path) -> list[DreamScene]:
    """Load all scenes directly under `pool_dir`, sorted by title.

    Only files at the top level of `pool_dir` are read; subdirectories and
    sibling directories (notably `pool-local/`) are never traversed. Malformed
    files are skipped with a logged warning.
    """
    if not pool_dir.exists() or not pool_dir.is_dir():
        return []

    scenes: list[DreamScene] = []
    for md_path in sorted(pool_dir.glob('*.md')):
        if md_path.name == 'README.md':
            continue  # pool documentation, not a scene
        scene = _load_one(md_path)
        if scene is not None:
            scenes.append(scene)

    scenes.sort(key=lambda s: s.title)
    return scenes


def find_scene_by_slug(scenes: list[DreamScene], slug: str) -> DreamScene | None:
    """Return the scene with this slug, or None."""
    for scene in scenes:
        if scene.slug == slug:
            return scene
    return None


def _load_one(md_path: Path) -> DreamScene | None:
    """Parse one scene file. Returns None (with a warning) if unusable."""
    try:
        text = md_path.read_text(encoding='utf-8')
    except OSError:
        logger.warning('dream scene %s: could not read file', md_path)
        return None

    match = _FRONTMATTER_RE.match(text)
    if match is None:
        logger.warning('dream scene %s: no frontmatter found, skipping', md_path)
        return None

    frontmatter_raw, body_raw = match.groups()
    try:
        frontmatter: dict[str, Any] = yaml.safe_load(frontmatter_raw) or {}
    except yaml.YAMLError as exc:
        logger.warning('dream scene %s: YAML parse error (%s), skipping', md_path, exc)
        return None

    missing = [f for f in _REQUIRED_FIELDS if f not in frontmatter]
    if missing:
        logger.warning('dream scene %s: missing required fields %s, skipping', md_path, missing)
        return None

    body = body_raw.strip()
    if not body:
        logger.warning('dream scene %s: empty body, skipping', md_path)
        return None

    # The scene's `title` frontmatter is shown in the page hero, so drop a
    # leading `# ...` line from the body to avoid a duplicate top heading.
    body = re.sub(r'^#\s+[^\n]*\n+', '', body, count=1)

    explicit_summary = str(frontmatter.get('summary', '') or '').strip()
    return DreamScene(
        slug=md_path.stem,
        name=str(frontmatter['name']),
        title=str(frontmatter['title']),
        sender=str(frontmatter['sender']),
        sender_type=str(frontmatter.get('sender_type', 'fortune') or 'fortune'),
        summary=explicit_summary or _first_sentence(body),
        body_html=render_markdown(body),
    )


def _first_sentence(body: str) -> str:
    """First sentence of the first prose paragraph, skipping markdown headings.

    Used as the gallery-card descriptor when a scene has no explicit `summary`.
    Returns the whole paragraph if it has no sentence terminator, or an empty
    string if the body is only headings.
    """
    for para in re.split(r'\n\s*\n', body):
        para = para.strip()
        if not para or para.startswith('#'):
            continue
        for i, ch in enumerate(para):
            if ch == '.' and (i + 1 >= len(para) or para[i + 1] in ' \n'):
                return para[: i + 1]
        return para
    return ''

"""Toolkit section registry — the single source of truth for nav items.

Adding a new top-level section (e.g., names becoming functional in Phase 1.5)
is a one-line edit here plus the route + template work.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Section:
    """One top-level section of the L7R Toolkit."""

    slug: str
    label: str
    path: str
    enabled: bool


SECTIONS: tuple[Section, ...] = (
    Section(slug='chargen', label='Characters', path='/chargen', enabled=True),
    Section(slug='relics', label='Relics', path='/relics', enabled=True),
    Section(slug='names', label='Names', path='/names', enabled=True),
)


def find_section_by_slug(slug: str) -> Section | None:
    """Return the Section matching the given slug, or None."""
    for section in SECTIONS:
        if section.slug == slug:
            return section
    return None

"""Fortune and clan lookup registries — module-level constants.

These are not loaded from files; they encode the canonical Rokugani
cosmology that the rest of the app refers to. Changes here are deliberate
setting changes, not data updates.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Fortune:
    """One Fortune of the Rokugani pantheon.

    `category` is 'major' (the seven Major Fortunes) or 'minor' (every other
    venerated Fortune — Inari, Koshin, and so on). The category drives the
    relics page's filter grouping: each individual Fortune is its own filter,
    and "Minor Fortunes" is a meta-filter spanning all minor entries.
    """

    slug: str
    name: str
    domain: str
    kanji: str
    category: str  # 'major' or 'minor'


FORTUNES: dict[str, Fortune] = {
    'benten': Fortune('benten', 'Benten', 'Fortune of romantic love', '弁天', 'major'),
    'bishamon': Fortune('bishamon', 'Bishamon', 'Fortune of strength', '毘沙門', 'major'),
    'daikoku': Fortune('daikoku', 'Daikoku', 'Fortune of wealth', '大黒', 'major'),
    'ebisu': Fortune('ebisu', 'Ebisu', 'Fortune of honest work', '恵比寿', 'major'),
    'fukurokujin': Fortune(
        'fukurokujin', 'Fukurokujin', 'Fortune of wisdom and mercy', '福禄寿', 'major'
    ),
    'hotei': Fortune('hotei', 'Hotei', 'Fortune of contentment', '布袋', 'major'),
    'jurojin': Fortune('jurojin', 'Jurojin', 'Fortune of longevity', '寿老人', 'major'),
    # Minor Fortunes — venerated in their own right but outside the canonical
    # seven. Listed after the majors so dict-iteration order on the relics
    # page renders them in a coherent block beneath the major sections.
    'inari': Fortune('inari', 'Inari', 'Fortune of rice and foxes', '稲荷', 'minor'),
}


def fortunes_in_category(category: str) -> dict[str, Fortune]:
    """Return the subset of FORTUNES with the given category ('major' or 'minor')."""
    return {slug: f for slug, f in FORTUNES.items() if f.category == category}


CLANS: dict[str, str] = {
    'any': 'Anywhere',
    'crab': 'Crab',
    'crane': 'Crane',
    'dragon': 'Dragon',
    'fox': 'Fox',
    'lion': 'Lion',
    'mantis': 'Mantis',
    'phoenix': 'Phoenix',
    'scorpion': 'Scorpion',
    'sparrow': 'Sparrow',
    'unicorn': 'Unicorn',
    'wasp': 'Wasp',
    'dragonfly': 'Dragonfly',
    'hare': 'Hare',
}


def clan_label(slug: str) -> str:
    """Return the display label for a clan slug, falling back to the slug itself."""
    return CLANS.get(slug, slug.capitalize())

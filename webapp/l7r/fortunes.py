"""Fortune and clan lookup registries — module-level constants.

These are not loaded from files; they encode the canonical Rokugani
cosmology that the rest of the app refers to. Changes here are deliberate
setting changes, not data updates.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Fortune:
    """One of the seven Major Fortunes."""

    slug: str
    name: str
    domain: str
    kanji: str


FORTUNES: dict[str, Fortune] = {
    'benten': Fortune('benten', 'Benten', 'Fortune of romantic love', '弁天'),
    'bishamon': Fortune('bishamon', 'Bishamon', 'Fortune of strength', '毘沙門'),
    'daikoku': Fortune('daikoku', 'Daikoku', 'Fortune of wealth', '大黒'),
    'ebisu': Fortune('ebisu', 'Ebisu', 'Fortune of honest work', '恵比寿'),
    'fukurokujin': Fortune('fukurokujin', 'Fukurokujin', 'Fortune of wisdom and mercy', '福禄寿'),
    'hotei': Fortune('hotei', 'Hotei', 'Fortune of contentment', '布袋'),
    'jurojin': Fortune('jurojin', 'Jurojin', 'Fortune of longevity', '寿老人'),
}


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

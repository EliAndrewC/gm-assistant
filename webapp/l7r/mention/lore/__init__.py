"""Campaign lore: what the GM Assistant knows about THIS setting.

Feature 205. Around a hundred categories drawn from `l7r.md`, each ten replies,
each annoyed first and factual second. The Character Sheet has no lore of his own
- he praises the GM Assistant and tells a Rokugan-set story instead.

See `CLAUDE.md` here for which file holds what, and `topics.py` for the
resolution order, which is the part that has to be right.
"""

from __future__ import annotations

from l7r.mention.lore.gm_clans import CLANS
from l7r.mention.lore.gm_moto import MOTO
from l7r.mention.lore.gm_people import PEOPLE
from l7r.mention.lore.gm_religion import RELIGION
from l7r.mention.lore.gm_setting import SETTING
from l7r.mention.lore.gm_world import WORLD
from l7r.mention.lore.sheet import IMPERIAL_FAMILIES, LORE_STORIES
from l7r.mention.lore.topics import LORE_ORDER, NAMED_SWORDS, SHEET_SILENT_ON

#: Every lore pool the GM Assistant has, in one table.
GM: dict[str, tuple[str, ...]] = {**SETTING, **RELIGION, **MOTO, **WORLD, **PEOPLE, **CLANS}

#: The Character Sheet's only lore-adjacent pools: the Imperial families, which
#: he answers in his own right, and the story he tells about everything else.
SHEET: dict[str, tuple[str, ...]] = {'imperial_families': IMPERIAL_FAMILIES}

__all__ = [
    'GM',
    'LORE_ORDER',
    'LORE_STORIES',
    'NAMED_SWORDS',
    'SHEET',
    'SHEET_SILENT_ON',
]

"""Place and lineage names already in use in the campaign (GM 2026-08-27).

Two sources, both local once the OP roster cache is warm - so this needs no
cache of its own and inherits the roster's refresh rules:

1. **Obsidian Portal tags.** A character is tagged with where they live:
   ``Nagahara province``, ``Hayakawa county``, ``Hoshigaoka village``, and a
   hamlet-dweller would carry ``<name> hamlet``; domains appear as
   ``Reiji domain``. Read from ``opcache/characters.json``.
2. **The chargen configuration.** ``[locations]`` in
   ``development-defaults.ini`` assigns each house its provinces, so a
   province that no character mentions yet is still taken.

``used_place_names()`` returns ``{scale: names}`` with the type word
stripped (``Nagahara``), and ``normalize`` is how a pool entry is compared
against it (case, spaces and hyphens ignored - ``Mizu-no-sato`` vs
``Mizu no Sato``). EXCLUSION IS PER SCALE: a village named Owari does not
retire Owari as a province name - the pool's own notes say multiple Owaris
appear in nearly every domain, and the GM's request was scale-specific
("exclude any province which is already in that configuration"). Flip
``SCALES`` handling in the caller if cross-scale exclusion is ever wanted.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

from chargen import opcache

SCALES = ('domain', 'province', 'county', 'village', 'hamlet')
_TAG_RE = re.compile(r'^\s*(.+?)\s+(domain|province|county|village|hamlet)\s*$', re.IGNORECASE)


def normalize(name: str) -> str:
    return re.sub(r'[^a-z0-9]', '', name.lower())


def from_tags(cache: Mapping[str, opcache.JsonObj]) -> dict[str, set[str]]:
    """``{scale: {name, ...}}`` from every cached character's tags."""
    out: dict[str, set[str]] = {s: set() for s in SCALES}
    for entry in cache.values():
        for tag in opcache._as_tags(entry.get('tags')):
            m = _TAG_RE.match(tag)
            if m:
                out[m.group(2).lower()].add(m.group(1))
    return out


def from_config(config: Mapping[str, object]) -> dict[str, set[str]]:
    """Provinces (and capitals, as towns are not a scale here - domains only)
    every house holds in ``[locations]``."""
    out: dict[str, set[str]] = {s: set() for s in SCALES}
    locations = config.get('locations')
    if isinstance(locations, Mapping):
        for house in locations.values():
            if not isinstance(house, Mapping):
                continue
            provinces = house.get('provinces')
            if isinstance(provinces, str):
                provinces = [provinces]
            for p in provinces if isinstance(provinces, list) else []:
                m = _TAG_RE.match(str(p))
                out[m.group(2).lower() if m else 'province'].add(m.group(1) if m else str(p))
    return out


_LINEAGE_TAG_RE = re.compile(r'^\s*(.+?)\s+lineage\s*$', re.IGNORECASE)


def lineage_names(
    cache: Mapping[str, opcache.JsonObj], config: Mapping[str, object]
) -> frozenset[str]:
    """Family, house and lineage names: OP ``<Name> Lineage`` tags plus every
    key of the chargen ``[family]``, ``[house]`` and ``[provincial_lineages]``
    sections (``obana`` -> ``Obana``). A GIVEN name that collides with one of
    these is excluded too (GM 2026-08-27: ``name()`` produced Obana, a Reiji
    lineage)."""
    names: set[str] = set()
    for entry in cache.values():
        for tag in opcache._as_tags(entry.get('tags')):
            m = _LINEAGE_TAG_RE.match(tag)
            if m:
                names.add(m.group(1))
    for section in ('family', 'house', 'provincial_lineages'):
        groups = config.get(section)
        if not isinstance(groups, Mapping):
            continue
        for group_name, group in groups.items():
            names.add(str(group_name).capitalize())
            if isinstance(group, Mapping):
                names.update(str(k).capitalize() for k in group)
    return frozenset(names)


def used_lineage_names(
    path: Path = opcache._CACHE_PATH, config: Mapping[str, object] | None = None
) -> frozenset[str]:
    return lineage_names(
        opcache.load_cache(path), config if config is not None else _chargen_config()
    )


def _chargen_config() -> Mapping[str, object]:
    from chargen import config

    return dict(config)


def used_place_names(
    path: Path = opcache._CACHE_PATH, config: Mapping[str, object] | None = None
) -> dict[str, frozenset[str]]:
    """Names in use per scale, both sources merged."""
    tags = from_tags(opcache.load_cache(path))
    cfg = from_config(config if config is not None else _chargen_config())
    return {s: frozenset(tags[s] | cfg[s]) for s in SCALES}

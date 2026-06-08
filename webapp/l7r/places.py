"""Places pool reader for the Places section.

Reads pool.jsonl from /.claude/skills/place-names/, parses entries into Place
dataclasses, and exposes filter + random-selection helpers. The pool covers
four scales (province, town, village, hamlet) and entries may apply to more
than one scale via the multi-valued place_types field.

The emit-time notes (canonical short explanations for each community-type
suffix) are stored here as a constant dict, mirroring the SKILL.md content,
so templates can render them without hardcoding text in HTML.
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = ('name', 'kanji', 'meaning', 'place_types', 'commonality')

PLACE_TYPES: tuple[str, ...] = ('province', 'town', 'village', 'hamlet')
COMMONALITIES: tuple[str, ...] = ('very_common', 'common', 'uncommon', 'rare', 'unique')
REGIONAL_CONTEXTS: tuple[str, ...] = (
    'mountain_bordering',
    'coastal',
    'riverine',
    'forested',
    'plains',
    'valley',
    'road_corridor',
)

# Canonical emit-time notes per community-type suffix. Mirrors the SKILL.md
# "Emit-time notes per suffix" section. Update both together.
SUFFIX_EMIT_NOTES: dict[str, str] = {
    '-mura': (
        'The generic word for village. The -mura suffix is dropped when '
        'referring to the village district as a whole: a village named X-mura '
        'sits in the X district, which also contains the surrounding hamlets. '
        'This drop-the-suffix convention applies to most community-type '
        'suffixes but is most prominent with -mura because -mura is by far the '
        'most common.'
    ),
    '-sato': (
        'Means home village or native place. A slightly poetic register, used '
        'for older long-settled villages with a strong sense of lineage. Often '
        'used by country monks in birth records when emphasizing that a '
        'peasant was born to the village rather than having moved there.'
    ),
    '-no-sato': (
        'Means home village or native place (the -no- is the possessive '
        'particle). A slightly poetic register, used for older long-settled '
        'villages with a strong sense of lineage. Often used by country monks '
        'in birth records when emphasizing that a peasant was born to the '
        'village rather than having moved there.'
    ),
    '-shou': (
        'Means manor estate. A village wholly under one samurai or merchant '
        "family's rent. The rent collector typically lives in or near the "
        'village, and the village headsman answers to the manor steward as '
        'much as to the county magistrate.'
    ),
    '-shuku': (
        'Means post-station or inn village. Exists as a lodging stop on a clan '
        'road or (where treaty permits) an Imperial road. Includes at least '
        'one inn, a smithy, and stabling, with a higher percentage of the '
        'population making their living from travelers than from farming. The '
        'Imperial Road through Minami province has no -shuku villages by '
        'treaty; on clan roads such villages are common.'
    ),
    '-gou': (
        'Means rural district. A village with an older, semi-administrative '
        'identity, old enough to appear by name in the oldest tax rolls of the '
        'domain. The suffix is more common in formal documents than in '
        'conversation.'
    ),
    '-ji': (
        'Means temple village. Grew up around a temple, which usually predates '
        "the village by generations. The temple's senior monk often holds "
        'informal authority alongside the headsman, and the country monk for '
        'the village district is generally drawn from this temple.'
    ),
    '-dera': (
        'Means temple village (a softer reading of the same character as -ji). '
        'Grew up around a temple, which usually predates the village by '
        "generations. The temple's senior monk often holds informal authority "
        'alongside the headsman.'
    ),
    '-bashi': (
        'Means bridge village. Exists because the bridge does; without the '
        'bridge, the village would not be where it is. Bridge maintenance is a '
        'recurring village expense, often subsidized by the county magistrate '
        'or by a merchant family with cargo interests.'
    ),
    '-tsuji': (
        'Means crossroads village. A small village at a road junction, '
        'typically with one inn, one shrine, and a handful of merchant stalls '
        'on travel days. Small in population but disproportionately visible to '
        'passers-through.'
    ),
    '-watashi': (
        'Means ford or ferry village. Built around a river crossing without a '
        'bridge. In flood season the ferry stops running and the village can '
        'be cut off from the road; the ferryman is a significant local figure '
        'and often a de facto co-headsman.'
    ),
    '-guchi': (
        'Means mouth or entrance village. Sits at the mouth of a valley or '
        'entrance to a forest road. Often the last settled place before '
        "wilderness or mountain country; may host travelers' shrines and small "
        'inns.'
    ),
    '-ichi': (
        'Means market village or market town. Designated as the weekly market '
        'site for a cluster of neighboring village districts. At village '
        'scale, the population multiplies several times over on market day; at '
        'town scale, the market is a permanent fixture and the local economy '
        'is built around it.'
    ),
    '-tono': (
        "Means lord's residence village. Rare as a true village-name suffix. "
        "Exists specifically to support a noble's hunting lodge, fishing "
        "manor, or seasonal residence. Its economy is bent around the lord's "
        'seasonal visits, and the village headsman often doubles as the lodge '
        'steward in the off-season.'
    ),
    '-seki': (
        'Means barrier or checkpoint village. Built around a samurai '
        'checkpoint on a clan road. The checkpoint precedes the village and '
        'the village exists to feed and house the bushi posted there. Carries '
        'more administrative weight than an ordinary village.'
    ),
    '-yashiki': (
        'Means manor estate village (emphasising the buildings rather than the '
        "lord). Used for retainers' or merchants' country estates rather than "
        "great lords' residences."
    ),
    '-machi': (
        'Means town-block or town district. The standard suffix for an '
        'organized town with multiple neighborhoods. Distinguishes a town from '
        'a village in formal records; not used at village or hamlet scale.'
    ),
}

# Geographic feature endings: present as a suffix in the pool but typically do
# not require an emit-time note (their meaning is self-evident from kanji).
# Stored here for completeness so the template can show a short tag instead.
GEOGRAPHIC_ENDING_LABELS: dict[str, str] = {
    '-kawa': 'river',
    '-gawa': 'river',
    '-tani': 'valley',
    '-ya': 'valley',
    '-sawa': 'marsh or mountain stream',
    '-zawa': 'marsh or mountain stream',
    '-hara': 'plain or open field',
    '-wara': 'plain or open field',
    '-no': 'field or plain',
    '-yama': 'mountain',
    '-san': 'mountain',
    '-oka': 'hill',
    '-mori': 'forest',
    '-hayashi': 'grove or woods',
    '-bayashi': 'grove or woods',
    '-ike': 'pond',
    '-hama': 'beach or shore',
    '-ura': 'bay or inlet',
    '-saki': 'cape or promontory',
    '-misaki': 'cape or promontory',
    '-shima': 'island',
    '-jima': 'island',
}

# Weighted distribution of village suffixes for random-append, drawn from the
# SKILL.md "Pool proportions" subsection. Used when the user wants to roll a
# random village name and the pool entry is a bare-element name (suffix is
# None) that needs a village-marker appended. Weights are integers (parts).
VILLAGE_SUFFIX_WEIGHTS: dict[str, int] = {
    '-mura': 45,
    '-no-sato': 12,
    '-shou': 8,
    '-shuku': 6,
    '-gou': 4,
    '-ji': 3,
    '-bashi': 2,
    '-tsuji': 2,
    '-watashi': 1,
    '-guchi': 1,
    '-ichi': 1,
    '-tono': 1,
    '-seki': 1,
    '-yashiki': 1,
}


@dataclass(frozen=True, slots=True)
class Place:
    """One place name from the pool."""

    slug: str
    name: str
    kanji: str
    meaning: str
    place_types: tuple[str, ...]
    commonality: str
    regional: tuple[str, ...] = field(default_factory=tuple)
    suffix: str | None = None
    notes: str = ''

    @property
    def is_multi_scale(self) -> bool:
        """True when the entry is usable at more than one scale."""
        return len(self.place_types) > 1

    @property
    def is_bare_element(self) -> bool:
        """True when the entry has no community-type or geographic-feature suffix."""
        return self.suffix is None

    @property
    def suffix_note(self) -> str:
        """Canonical emit-time note for the suffix, or empty string if none."""
        if self.suffix is None:
            return ''
        return SUFFIX_EMIT_NOTES.get(self.suffix, '')

    @property
    def suffix_label(self) -> str:
        """Short label for the suffix (one of: community-type explanation or
        geographic feature tag); empty when there is no suffix.

        Used by the index card to show what kind of place the entry is, without
        the full emit-time note.
        """
        if self.suffix is None:
            return ''
        if self.suffix in SUFFIX_EMIT_NOTES:
            # The first sentence of the emit-time note is the meaning gloss.
            note = SUFFIX_EMIT_NOTES[self.suffix]
            return note.split('.', 1)[0]
        if self.suffix in GEOGRAPHIC_ENDING_LABELS:
            return f'ends in {self.suffix} ({GEOGRAPHIC_ENDING_LABELS[self.suffix]})'
        return ''


def _slugify(name: str) -> str:
    """Convert a place name to a URL-safe slug.

    Lowercases and replaces non-alphanumeric runs with single hyphens, then
    strips leading and trailing hyphens. "Yuhimura" -> "yuhimura",
    "Aki-no-mori" -> "aki-no-mori", "Mori-tono" -> "mori-tono".
    """
    out: list[str] = []
    last_was_dash = True
    for ch in name.lower():
        if ch.isalnum():
            out.append(ch)
            last_was_dash = False
        elif not last_was_dash:
            out.append('-')
            last_was_dash = True
    slug = ''.join(out)
    return slug.strip('-')


def load_places(pool_path: Path) -> list[Place]:
    """Load all places from pool.jsonl. Returns a list sorted by name.

    pool_path may be either the pool.jsonl file directly or a directory
    containing pool.jsonl. Lines missing required fields are skipped with a
    logged warning.
    """
    if pool_path.is_dir():
        pool_path = pool_path / 'pool.jsonl'
    if not pool_path.exists():
        return []

    try:
        text = pool_path.read_text(encoding='utf-8')
    except OSError:
        logger.warning('places %s: could not read file', pool_path)
        return []

    places: list[Place] = []
    seen_slugs: set[str] = set()
    for line_no, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            entry = json.loads(stripped)
        except json.JSONDecodeError as exc:
            logger.warning('places %s:%d: JSON parse error (%s)', pool_path, line_no, exc)
            continue
        missing = [f for f in _REQUIRED_FIELDS if f not in entry]
        if missing:
            logger.warning('places %s:%d: missing %s, skipping', pool_path, line_no, missing)
            continue
        place = _build_place(entry)
        if place.slug in seen_slugs:
            logger.warning(
                'places %s:%d: duplicate slug %s, skipping',
                pool_path,
                line_no,
                place.slug,
            )
            continue
        seen_slugs.add(place.slug)
        places.append(place)
    places.sort(key=lambda p: p.name.lower())
    return places


def _build_place(entry: dict[str, object]) -> Place:
    """Build a Place from a parsed JSONL entry dict."""
    name = str(entry['name'])
    place_types_raw = entry.get('place_types', [])
    if not isinstance(place_types_raw, list):
        place_types_raw = []
    regional_raw = entry.get('regional', [])
    if not isinstance(regional_raw, list):
        regional_raw = []
    suffix_raw = entry.get('suffix')
    return Place(
        slug=_slugify(name),
        name=name,
        kanji=str(entry['kanji']),
        meaning=str(entry['meaning']),
        place_types=tuple(str(t) for t in place_types_raw),
        commonality=str(entry['commonality']),
        regional=tuple(str(r) for r in regional_raw),
        suffix=str(suffix_raw) if suffix_raw else None,
        notes=str(entry.get('notes', '') or ''),
    )


def find_place_by_slug(places: list[Place], slug: str) -> Place | None:
    """Return the place matching the given slug, or None."""
    for place in places:
        if place.slug == slug:
            return place
    return None


def filter_places(
    places: list[Place],
    *,
    place_type: str | None = None,
    commonality: str | None = None,
    regional: str | None = None,
    suffix: str | None = None,
) -> list[Place]:
    """Filter a list of places by any combination of axes.

    Each axis is single-valued. Passing None for an axis leaves it unfiltered.
    The special value 'none' for suffix matches entries with no suffix.
    """
    result = list(places)
    if place_type is not None:
        result = [p for p in result if place_type in p.place_types]
    if commonality is not None:
        result = [p for p in result if p.commonality == commonality]
    if regional is not None:
        result = [p for p in result if regional in p.regional]
    if suffix is not None:
        if suffix == 'none':
            result = [p for p in result if p.suffix is None]
        else:
            result = [p for p in result if p.suffix == suffix]
    return result


def random_place(
    places: list[Place],
    rng: random.Random | None = None,
) -> Place | None:
    """Pick one place uniformly at random. Returns None if the list is empty."""
    if not places:
        return None
    chooser = rng if rng is not None else random
    return chooser.choice(places)


def random_village_suffix(rng: random.Random | None = None) -> str:
    """Pick a village community-type suffix weighted by SKILL.md proportions.

    Used when surfacing a bare-element name as a village: the bare element is
    paired with a random suffix to produce a complete village name.
    """
    chooser = rng if rng is not None else random
    suffixes = list(VILLAGE_SUFFIX_WEIGHTS.keys())
    weights = list(VILLAGE_SUFFIX_WEIGHTS.values())
    return chooser.choices(suffixes, weights=weights, k=1)[0]


def villageify(place: Place, rng: random.Random | None = None) -> tuple[str, str]:
    """Pair a bare-element place with a random village suffix.

    Returns (combined_name, chosen_suffix). For non-bare entries, returns the
    entry's own name unchanged with its existing suffix. The combined name
    uses a hyphen between the bare element and the suffix.
    """
    if not place.is_bare_element:
        return place.name, place.suffix or ''
    chosen = random_village_suffix(rng)
    return f'{place.name}{chosen}', chosen


def scale_description(place: Place, scale: str) -> str:
    """Render a copy-paste description of a place at a specific scale.

    Used by the detail page to produce a sentence the GM can drop into prep
    notes. The scale must be one of place.place_types; behavior for other
    scales is to fall back to the entry's primary scale (first in the list).
    """
    if scale not in place.place_types and place.place_types:
        scale = place.place_types[0]

    base = f"{place.name} ({place.kanji}, '{place.meaning}')"
    scale_phrase = {
        'province': 'a province',
        'town': 'a county town',
        'village': 'a village',
        'hamlet': 'a hamlet',
    }.get(scale, f'a {scale}')
    sentence = f'{base} is {scale_phrase}.'
    if place.suffix_note:
        sentence += f' {place.suffix_note}'
    if place.notes:
        sentence += f' {place.notes}'
    return sentence

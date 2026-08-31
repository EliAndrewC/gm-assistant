"""Every lore pattern, in RESOLUTION ORDER. The order is the correctness story.

Four routing rules the GM asked for all claim overlapping strings, and without a
precedence between them each one silently deletes another:

  - `Moto` is a Unicorn FAMILY. Family-to-clan routing (FR-016) would swallow all
    fourteen Moto categories the GM approved in message 2.
  - `Kuni` is a Crab family. It would swallow `kuni_yori` and `kuni_isamu`.
  - `Akodo no Damasu` is name-shaped, so the named-person dismissal (FR-007) would
    claim the very house the GM asked for by name (FR-017).
  - `Damasu` alone is claimed by both the DOMAIN (a place) and the HOUSE.

So: **named individuals, then rich specific topics, then Imperial families, then
houses, then clans, then the dismissal.** First match wins, exactly as in
`smalltalk.topics`.

The symptom of getting this wrong is a category that stops being reachable, which
reading the file will never show you - so it is pinned by tests rather than by
care. If you add a category here, add it to the right TIER, not to the end.
"""

from __future__ import annotations

#: The nine named swords in `l7r.md`. FR-006: famous swords are ONE category, but
#: naming any individual sword must reach it - the GM's example was Shitsuten.
NAMED_SWORDS = (
    'Amatsukami no Ken',
    'Ohari',
    'Seishinsho',
    'Kishin no Ketsui',
    'Akuzuki',
    'Kasai Tsume',
    'Shitsuten',
    'Seiginryu',
    'Tamashikari',
)

#: FR-016, from the population table in `l7r.md`: naming any Great Family is the
#: same as naming its clan. *"if the Asako family is mentioned then that is the
#: same as if the Phoenix clan was mentioned."*
CLAN_FAMILIES: dict[str, tuple[str, ...]] = {
    'lion': ('Akodo', 'Matsu', 'Ikoma', 'Kitsu'),
    'crab': ('Hida', 'Yasuki', 'Kaiu', 'Kuni', 'Hiruma'),
    'crane': ('Doji', 'Daidoji', 'Kakita', 'Asahina'),
    'scorpion': ('Bayushi', 'Shosuro', 'Soshi', 'Yogo'),
    'unicorn': ('Shinjo', 'Otaku', 'Moto', 'Ide', 'Iuchi'),
    'dragon': ('Togashi', 'Mirumoto', 'Agasha', 'Kitsuki'),
    'phoenix': ('Shiba', 'Isawa', 'Asako'),
}

#: The four Imperial families. FR-018 - the one lore category BOTH bots answer.
IMPERIAL_FAMILIES = ('Seppun', 'Hantei', 'Otomo', 'Miya')


def _alternation(words: tuple[str, ...]) -> str:
    return '|'.join(w.replace(' ', r'\s+') for w in words)


def _clan_pattern(clan: str) -> str:
    """A clan is reached by its own name or by any of its families (FR-016)."""
    return rf'\b({clan}|{_alternation(CLAN_FAMILIES[clan])})\b'


# --------------------------------------------------------------------------
# TIER 1 - named individuals. Before families, or `Kuni` eats `Kuni Yori`.
# --------------------------------------------------------------------------
INDIVIDUALS: tuple[tuple[str, str], ...] = (
    ('kitsu_okura', r'\bkitsu\s+okura\b|\bokura\b'),
    ('soshi_saibankan', r'\bsoshi\s+saibankan\b|\bsaibankan\b'),
    ('grand_abbot_benshi', r'\bbenshi\b'),
    ('akodo_toturi', r'\btoturi\b'),
    ('moto_khuyag', r'\bkhuyag\b|\bdeath detector'),
    ('kuni_yori', r'\bkuni\s+yori\b'),
    ('kuni_isamu', r'\bkuni\s+isamu\b|\bforgotten tomb\b'),
    ('moto_gaheris', r'\bgaheris\b|\bkhan of khans\b'),
)

# --------------------------------------------------------------------------
# TIER 2 - rich specific topics. Before clans, or `Moto` and `Isawa` vanish.
# --------------------------------------------------------------------------
TOPICS: tuple[tuple[str, str], ...] = (
    # -- the Gods of Death, each separate at the GM's instruction (FR-005) --
    ('king_yan', r'\bking yan\b|\bking of hell\b'),
    ('enma', r'\benma\b(?!-)'),
    ('wei_tin', r'\bwei\s*tin\b|\blord of ghosts\b'),
    ('gods_of_death', r'\bgods? of death\b|\bbloodstorm\b|\blamentation\b|\bretirement\b'),
    ('emma_o', r'\bemma-?o\b|\bpeaceful repose\b'),
    # -- the Moto, all of it, before the Unicorn clan can claim the word ----
    ('the_yassa', r'\byassa\b'),
    ('moto_etiquette', r'\bmoto etiquette\b'),
    ('moto_tribal_structure', r'\bmoto trib|\bmoto clan structure\b'),
    ('moto_language', r'\bmoto language\b'),
    ('moto_rank', r'\bmoto rank\b'),
    ('vindicator_moto', r'\bvindicator\b'),
    ('dark_moto', r'\bdark moto\b'),
    ('bodi_kaikhan', r'\bbodi kaikhan\b'),
    ('medin_al_salaat', r'\bmedin al ?salaat\b'),
    ('burning_sands', r'\bburning sands\b'),
    ('horse_culture', r'\bhorse culture\b|\bwild horse\b|\bstable horse\b|\bhay\b'),
    ('unicorn_history', r'\bunicorn history\b|\bki-?rin\b'),
    ('the_moto', r'\bmoto\b'),
    # -- villains and metaplot ---------------------------------------------
    ('iuchibans_lieutenants', r'\bjama\b|\byajinden\b|\bkyoso\b|\bkohaku\b|\bjama musume\b'),
    ('iuchiban', r'\biuchiban\b'),
    ('the_gozoku', r'\bgozoku\b'),
    ('hantei_16', r'\bhantei the (16th|sixteenth)\b|\bhantei 16\b'),
    ('the_nameless_one', r'\bnameless one\b'),
    ('connection_damage', r'\bconnection damage\b'),
    # -- relics and swords. FR-006: any named sword reaches the one category -
    ('famous_swords', rf'\bfamous swords?\b|\b({_alternation(NAMED_SWORDS)})\b'),
    ('armor_of_fools_regret', r"\barmor of fool'?s regret\b"),
    ('candle_of_tears', r'\bcandle of tears\b'),
    ('yamaoroshi', r'\byamaoroshi\b'),
    ('temple_relics', r'\btemple relics?\b|\brelic seekers?\b|\brelics?\b'),
    # -- campaigns and their places ----------------------------------------
    ('order_of_lord_moon', r'\border of lord moon\b|\blord moon\b'),
    ('karmic_inquisitors', r'\bkarmic inquisitor'),
    ('first_toshi_ranbo', r'\btoshi ranbo\b'),
    ('peasant_campaign', r'\bpeasant campaign\b'),
    ('hidden_way', r'\bhidden way\b'),
    ('wasp_bounty_hunters', r'\bwasp\b|\btsuruchi\b'),
    ('damasu_domain', r'\bdamasu (domain|lands|provinces|county)\b'),
    ('chai_sedo', r'\bchai sedo\b|\bimperial gardens?\b'),
    ('first_imperial_legion', r'\b(1st|first) imperial legion\b|\bimperial legions?\b'),
    ('hikobayashi_county', r'\bhikobayashi\b'),
    ('gateway_outsider_keep', r'\bgateway\b|\boutsider keep\b'),
    # -- geography. The GM asked to keep these ------------------------------
    ('kaiu_wall', r'\bkaiu wall\b|\bthe wall\b'),
    ('isawa_woodlands', r'\bisawa woodlands?\b'),
    ('drowned_merchant_river', r'\bdrowned merchant\b'),
    # -- religion and cosmology ---------------------------------------------
    ('ryoshun', r'\bryoshun\b'),
    ('lord_moons_court', r'\bheavenly court\b'),
    ('between_places', r'\bbetween places?\b'),
    ('maho_bloodspeakers', r'\bmaho\b|\bbloodspeaker|\btsukai\b'),
    ('shugenja', r'\bshugenja\b'),
    ('bentens_blessing', r"\bbenten'?s blessing\b"),
    ('benten', r'\bbenten\b'),
    ('bishamon', r'\bbishamon\b'),
    ('daikoku', r'\bdaikoku\b'),
    ('koshin', r'\bkoshin\b'),
    ('jikoju', r'\bjikoju\b'),
    ('vows_and_oaths', r'\bvows?\b|\boaths?\b'),
    ('temple_finances', r'\btemple finances?\b'),
    ('temple_organization', r'\btemples?\b|\bmonaster'),
    ('food_purity', r'\bfood purity\b'),
    ('soothsaying', r'\bsoothsay'),
    ('omens_and_portents', r'\bomens?\b|\bportents?\b'),
    # -- calendar ------------------------------------------------------------
    ('obon', r'\bobon\b|\bbon festival\b'),
    ('sexagenary_cycle', r'\bsexagenary\b'),
    ('twelve_hours', r'\btwelve hours\b|\bhour of the\b'),
    ('twelve_months', r'\btwelve months\b|\bmutsuki\b|\bkisaragi\b|\byayoi\b|\bshiwasu\b'),
    ('festivals', r'\bfestivals?\b'),
    # -- setting mechanics ---------------------------------------------------
    ('village_headsman', r'\bvillage headsm[ae]n\b|\bheadsm[ae]n\b'),
    ('median_domain', r'\bmedian domain\b'),
    ('accordances_of_rank', r'\baccordances? of rank\b|\bdoctrine of three steps\b'),
    ('samurai_lineages', r'\blineages?\b'),
    ('experience_levels', r'\bexperience levels?\b'),
    ('imperial_budget', r'\bimperial budget\b'),
    ('rent_and_taxes', r'\brent\b|\btaxes\b|\btax\b'),
    ('castes', r'\bcastes?\b|\bheimin\b|\bhinin\b|\bburakumin\b'),
    ('money_koku', r'\bkoku\b|\bzeni\b|\bbu\b(?!\w)'),
    ('merchant_families', r'\bmerchant famil'),
    ('ashigaru', r'\bashigaru\b'),
    ('crime_and_punishment', r'\bcrime\b|\bpunishment\b'),
    # -- the six Ministries --------------------------------------------------
    ('ministry_of_rites', r'\bministry of rites\b'),
    ('ministry_of_revenue', r'\bministry of revenue\b'),
    ('ministry_of_retainers', r'\bministry of retainers\b'),
    ('ministry_of_war', r'\bministry of war\b'),
    ('ministry_of_works', r'\bministry of works\b'),
    ('ministry_of_justice', r'\bministry of justice\b'),
    # -- being merely an assistant. GM Assistant only (FR-021) --------------
    (
        'merely_an_assistant',
        r'\b(speak to|talk to|see) (your|the) (manager|supervisor|boss)\b'
        r'|\bwho(\'s| is) in charge\b|\b(just|only|merely) an? assistant\b'
        r'|\byour manager\b|\byour boss\b',
    ),
)

# --------------------------------------------------------------------------
# TIER 3 - the Imperial families, before the Great Clans.
# --------------------------------------------------------------------------
IMPERIAL: tuple[tuple[str, str], ...] = (
    ('imperial_families', rf'\b({_alternation(IMPERIAL_FAMILIES)}|imperial famil\w+)\b'),
)

# --------------------------------------------------------------------------
# TIER 4 - houses. Before clans (`Akodo no Damasu` contains `Akodo`) and before
# the dismissal (it is name-shaped).
# --------------------------------------------------------------------------
_FAMILIES = '|'.join(family.lower() for families in CLAN_FAMILIES.values() for family in families)

HOUSES: tuple[tuple[str, str], ...] = (
    ('damasu', r'\bdamasu\b'),
    # `Family no House` with NO given name after it. Derived from the family
    # list rather than written as `\w+ no \w+`, which matched "there is no way".
    (
        'famous_houses',
        rf'\b({_FAMILIES})\s+no\s+\w+\b|\b(akito|tsume|ryusei|karo house)\b|\bhouses?\b',
    ),
)

# --------------------------------------------------------------------------
# A PERSON with no category: a family name followed by a GIVEN name. Runs
# before HOUSES and CLANS, because `Akodo no Damasu Sei` is a person while
# `Akodo no Damasu` is a house, and `Shinjo Jotsu` is a person the GM cut
# rather than the Unicorn Clan. The pattern requires a trailing word, so it
# cannot claim the bare house form - that is the whole discriminator.
# --------------------------------------------------------------------------
PERSON: tuple[tuple[str, str], ...] = (
    # A family name followed by a GIVEN name. The negative lookahead keeps
    # "Matsu family", "Kuni lands" and "Doji house" out of here - those are
    # references to the family or its holdings, not to a person, and they belong
    # to the clan and house tiers.
    (
        'nobody_important',
        rf'\b({_FAMILIES})\s+(no\s+\w+\s+)?'
        r'(?!family|families|clan|house|houses|lands|domain|domains|province|provinces|'
        r'samurai|bushi|daimyo|courtier|magistrate|army|armies|school)\w{3,}\b',
    ),
)

# --------------------------------------------------------------------------
# TIER 5 - the seven Great Clans, reached by clan name or any family name.
# --------------------------------------------------------------------------
CLANS: tuple[tuple[str, str], ...] = tuple(
    (f'clan_{clan}', _clan_pattern(clan)) for clan in CLAN_FAMILIES
)

#: The whole thing, in order. `rules` walks this and takes the first hit.
#:
#: An earlier draft ended with a catch-all `[A-Z][a-z]{2,} [A-Z][a-z]{2,}` for the
#: dismissal. It would have eaten "Good Bot" and every other two-word phrase,
#: because patterns are compiled case-insensitively and the capitals bought
#: nothing. Anchoring on the family list instead makes `Shinjo Jotsu` a person and
#: leaves `good bot` alone.
LORE_ORDER: tuple[tuple[str, str], ...] = INDIVIDUALS + TOPICS + IMPERIAL + PERSON + HOUSES + CLANS

#: What tells the Character Sheet a LORE question was asked, without giving him
#: anything to say about it (FR-009). Everything except the Imperial families,
#: which he answers in his own right (FR-018), and the assistant joke, which is
#: not his (FR-021).
SHEET_SILENT_ON = frozenset(
    key for key, _ in LORE_ORDER if key not in {'imperial_families', 'merely_an_assistant'}
)

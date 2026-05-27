import os

from chargen import config, __here__ as HERE

__all__ = [
    'HERE',
    'NAMES',
    'USED_NAMES',
    'XP_DIST',
    'TRAITS',
    'ADVANTAGES_AND_DISADVANTAGES',
    'GENDER_TRAITS',
    'SAMURAI TRAITS',
    'MINISTRIES',
]


NAMES = {}
"""
This is how we store gender-organized names and their meanings, e.g.
    {
        'male': {
            'Akio': 'This name represents "bright man" and is often chosen by those who are naturally charismatic or who are expected to become influential leaders.',
        ...
        },
        'female': {...}
    }
"""
for _gender in ['male', 'female']:
    with open(os.path.join(HERE, f'{_gender}_names.txt')) as f:
        name_lines = [line.strip() for line in f if line.strip()]
        NAMES[_gender] = {
            line.split()[0]: line.split(' - ', 1)[1] if line.split()[1] == '-' else line
            for line in name_lines
        }

USED_NAMES = set()
"""
This is updated with the personal names (e.g. 'Gohei' instead of 'Matsu Gohei')
of all of the characters already in Obsidian Portal.
"""

HOUSE_NAMES = set()
"""
Different campaigns involve different houses, and this pulls those from 
"""
for _family in config['family'].values():
    HOUSE_NAMES.update(name.title() for name in _family.keys())

XP_DIST = [0.80, 0.65, 0.50, 0.35, 0.20, 0.18, 0.16, 0.14, 0.12, 0.10]
"""
See the gen_xp() function in character.py for an explanation of the experience
distribution which this represents.
"""

TRAITS = {
    'thin / fat': (0.10, 0.05),
    'short / tall': (0.05, 0.05),
    'big nose / big ears': (0.02, 0.02),
    'boisterous / soft-spoken': (0.05, 0.05),
    'missing tooth / missing finger / missing eye / missing ear': (0.02, 0.02, 0.02, 0.02),
    'dour / scowling / furrowed / frowny / squinty': (0.02, 0.02, 0.02, 0.02, 0.02),
    'jolly / happy / lighthearted / mirthful / upbeat': (0.02, 0.02, 0.02, 0.02, 0.02),
    'quick to speak / pauses before speaking': (0.05, 0.05),
    'deferential / outspoken': (0.10, 0.05),
    'speaks quickly / speaks slowly': (0.02, 0.02),
    'constantly clearing throat / constantly sniffling / takes deep breaths / heavy sighs / clucks tongue / clicks tongue / says "hmmmmm" before speaking': (
        0.02,
        0.02,
        0.02,
        0.02,
        0.02,
        0.02,
        0.02,
    ),
    'visibly torn and sewn clothing / visibly patched clothing / visibly stained clothing / frayed seams and hems / frayed collar / faded clothes': (
        0.02,
        0.02,
        0.02,
        0.02,
        0.02,
        0.02,
    ),
    'military posture / slouches': (0.05, 0.05),
    'intense expression / thoughtful expression': (0.05, 0.05),
    'dry wheezing laugh / barking laugh / silent shaking laugh / nasal snort': (
        0.02,
        0.02,
        0.02,
        0.02,
    ),
    'monotone voice / gravelly voice / breathy voice': (0.02, 0.02, 0.02),
    'eyes darting / always turning to the side': (0.05, 0.05),
    'embittered / skeptical / trusting': (0.05, 0.05, 0.05),
    'speaks about dreams / speaks about omens': (0.05, 0.05),
    'having an affair / unrequited love / pining for a deceased lover / estranged from spouse': (
        0.05,
        0.05,
        0.05,
        0.05,
    ),
    'tattooed': 0.05,
    'garishly dressed': 0.05,
    'pensive': 0.05,
    'scarred': 0.05,
    'hairy arms': 0.05,
    'twitchy': 0.05,
    'sweaty': 0.05,
    'unusual haircut': 0.05,
    'annoyed': 0.05,
    'squinty': 0.05,
    'flinching': 0.05,
    'dark circles under eyes': 0.05,
    'wears charms and amulets': 0.05,
    'always looking up': 0.05,
    'interrupting': 0.10,
    'ambitious': 0.10,
    'judgmental': 0.05,
    'paranoid': 0.05,
    'contemptuous': 0.05,
    'superstitious': 0.10,
    'drums fingers absentmindedly': 0.05,
    'repeats your last word or phrase': 0.05,
    'spiritually insightful': 0.05,
    'indebted to a rival': 0.05,
    'favor-seeking': 0.05,
    'caught between two masters': 0.05,
    'personally hated by an enemy': 0.05,
    'feuding with family': 0.05,
    'black sheep': 0.05,
    'gossipy': 0.20,
    'waiting for a relative to die': 0.10,
    'chronically apologetic': 0.10,
    'religiously unorthodox': 0.10,
    'muses to themselves out loud': 0.05,
    'raising an acknowledged bastard child': 0.05,
}
"""
When randomly generating traits, we iterate through this list; the keys are the
traits and the values are the percentage of NPCs with that trait.  Some of these
are advantages/disadvantages and others are general descriptions.

Some traits are mutually exclusive with one anopther, so in those cases we
represent it as e.g.

    'thin / fat': (0.10, 0.05)

which means that there's a 10% chance of thin and a 5% chance of fat.  This
is implemented via the gen_traits() method in character.py
"""

ADVANTAGES_AND_DISADVANTAGES = {
    'Poor / Wealthy': (0.20, 0.20),
    'Vain / Unkempt': (0.10, 0.05),
    'Virtue / Unconventional': (0.10, 0.05),
    'Short Temper': 0.10,
    'Long Temper': 0.10,
    'Contrary': 0.15,
    'Good Reputation': 0.10,
    'Bad Reputation': 0.05,
    'Imperial Favor': 0.05,
    'Kind Eye': 0.10,
    'Jealousy': 0.05,
    'Permanent Wound': 0.10,
    'Dark Secret': 0.01,
    'Driven': 0.02,
    'Emotional': 0.05,
    'Geneologist': 0.05,
    'Humble': 0.05,
    'Transparent': 0.05,
    'Thoughtless': 0.05,
}
"""These are the same as any other traits, but with rules-based mechanical effects."""

SAMURAI_TRAITS = {
    'collector': 0.05,
    'sword-calloused / ghost grip / silk-handed': (0.10, 0.10, 0.10),
    'ink-stained cuticles': 0.05,
    "archer's thumb": 0.05,
    'in debt to peasant merchants': 0.05,
    'hides hands in sleeves': 0.05,
    'sympathetic to family rivals': 0.05,
    'seeking a lost heirloom': 0.05,
    'haunted by a failed duty': 0.05,
    "resentful about another's promotion": 0.05,
    'always asking whether something is official or on behalf of a superior': 0.05,
    'keeping a deathbed secret': 0.05,
    'incense-scented / purfumed / overly purfumed / smells of horse': (0.10, 0.10, 0.05, 0.05),
}
"""Some traits are only valid for samurai, and not monks or peasants."""

COLLECTABLES = [
    {
        'name': 'arrows from famous battles',
        'art': 'a single ornate arrow in her hands brightly colored fletching',
    },
    {'name': 'tsuba (sword guards)', 'art': 'ornate sword guards worn as pendants'},
    {'name': 'whetstones', 'art': 'fine whetstones of varying color tucked into the obi'},
    {'name': 'tea cups and sake cups', 'art': 'a delicate porcelain cup carried carefully in hand'},
    {'name': 'cicada husks', 'art': 'translucent cicada shells pinned to the kimono'},
    {'name': 'signed poetry scrolls', 'art': 'a calligraphy scroll case slung over one shoulder'},
    {'name': 'tea caddies', 'art': 'a small lacquered tea caddy held reverently'},
    {'name': 'bird feathers', 'art': 'colorful feathers tucked into the hair and clothing'},
    {'name': 'samples of dirt', 'art': 'small cloth pouches of earth hanging from the obi'},
    {'name': 'dried wildflowers', 'art': 'pressed dried wildflowers adorning the lapel'},
    {'name': 'river stones', 'art': 'smooth river stones worn as ornaments on a cord'},
    {'name': 'cricket cages', 'art': 'a small hand-carved bamboo cricket cage at the hip'},
    {'name': 'prayer beads found on the road', 'art': 'a necklace of mismatched prayer beads'},
    {'name': 'wax seal impressions', 'art': 'scraps of wax-sealed paper tucked into the obi'},
]
"""
When a character has the 'collector' trait, one of these items is randomly
selected as the specific thing they collect.  The 'name' is used in the
character description and the 'art' is the visual detail for the image prompt.
"""

GENDER_TRAITS = {
    'male': {
        'balding': 0.20,
        'bearded / long beard / bushy beard / mustachioed': (0.10, 0.02, 0.02, 0.05),
    },
    'female': {'pregnant': 0.15, 'jewelried': 0.10, 'fine makeup / inexpert makeup': (0.10, 0.05)},
}
"""
Some traits are gender-specific, e.g. 'mustachioed' or 'pregnant'.  This uses
the same format as TRAITS above, indexed by gender.
"""

CLAN_COLORS = {
    'Crab': 'dark blue and light gray',
    'Crane': 'light blue and white / silver',
    'Dragon': 'gold and dark green',
    'Lion': 'yellow and brown',
    'Phoenix': 'red and orange',
    'Scorpion': 'black and dark red',
    'Unicorn': 'purple and white with gold trim',
    'Imperial': 'dark green with gold trim and fine chrysanthemum embroidery',
    'Sparrow': 'dun brown and black',
    'Fox': 'green and silver',
    'Wasp': 'black and gold',
    'Dragonfly': 'blue, brown, and gold',
    'Hare': 'red and white',
}
"""
This is not yet used, but art.py will eventually make use of this when making
art prompts for NPCs.
"""

MINISTRIES = [
    'Ministry of Rites',
    'Ministry of Retainers',
    'Ministry of Revenue',
    'Ministry of War',
    'Ministry of Works',
    'Ministry of Justice',
]
"""
The six ministries of the Rokugan imperial bureaucracy. Each ministry has
specific responsibilities and is led by a Minister and Deputy Minister at
the imperial level, with Provincial and Deputy Provincial Ministers in
the provinces.
"""

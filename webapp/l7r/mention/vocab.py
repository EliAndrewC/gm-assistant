"""Words that mean the message is about the game (FR-010).

Deciding which unmatched pool to answer from: a message containing any of these
gets the game-flavored pool, everything else gets the generic one.

WHY THIS IS A LITERAL LIST AND NOT DERIVED AT RUNTIME. The skills are already
canonical elsewhere - `l7r.repl.rolls.skills` reads them from
`/host-l7r-repo/rules/02-skills.md` - and this project's standing rule is to
derive a list rather than maintain one, because a list updated from memory drifts
(measured 2026-08-30, when a hand-kept roster of secret config sections let three
credentials leak). It is a literal here anyway, for a reason that overrides it:

    THE DEPLOYED BOT HAS NEITHER FILE. `scripts/deploy_mention_bot.sh` ships
    `l7r/mention/*.py` and two config stanzas to a Lightsail box. The rules
    repository is not there, and neither is the rest of `l7r`. Importing the
    canonical source would make the bot un-deployable, and reading the markdown
    at runtime would make it crash on a box where that path does not exist.

So the rule is kept, one step removed: `tests/test_mention.py` asserts this list
still contains every skill `skills.load_skills()` reports, and that test runs in
the repository, where both files exist. Drift is caught at gate time rather than
being impossible - the best available version of the guarantee given that the
artifact has to be self-contained.
"""

from __future__ import annotations

import re

#: The 20 canonical L7R skills. Cross-checked against the rules file by a test.
SKILLS = (
    'acting',
    'attack',
    'bragging',
    'commerce',
    'culture',
    'etiquette',
    'heraldry',
    'history',
    'interrogation',
    'intimidation',
    'investigation',
    'law',
    'manipulation',
    'parry',
    'precepts',
    'sincerity',
    'sneaking',
    'strategy',
    'tact',
    'underworld',
)

#: Setting and table vocabulary. The GM's examples were the skill names and
#: *"the word samurai"*; these are the rest of the words that mean a message is
#: about the game rather than about the weather.
SETTING_WORDS = (
    'ashigaru',
    'bushi',
    'bushido',
    'clan',
    'courtier',
    'crab',
    'crane',
    'daimyo',
    'dojo',
    'dragon',
    'duel',
    'emerald',
    'emperor',
    'geisha',
    'gempuku',
    'hantei',
    'heimin',
    'honor',
    'imperial',
    'katana',
    'kharmic',
    'koku',
    'lion',
    'magistrate',
    'maho',
    'monk',
    'nezumi',
    'ninja',
    'oni',
    'phoenix',
    'ronin',
    'rokugan',
    'rokugani',
    'samurai',
    'scorpion',
    'seppuku',
    'shadowlands',
    'shugenja',
    'sensei',
    'shiro',
    'taint',
    'tetsubo',
    'unicorn',
    'wakizashi',
    'yojimbo',
)

#: Tabletop vocabulary. A message about dice is about the game even with no
#: Rokugani word in it.
TABLE_WORDS = (
    'campaign',
    'character',
    'crit',
    'dice',
    'die',
    'dungeon',
    'gm',
    'initiative',
    'npc',
    'party',
    'ring',
    'roleplay',
    'roll',
    'rolled',
    'session',
    'skill',
    'stat',
    'tabletop',
    'trait',
    'void',
    'wound',
    'xp',
)

GAME_WORDS = frozenset(SKILLS + SETTING_WORDS + TABLE_WORDS)

_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")


def is_about_the_game(text: str) -> bool:
    """True if the message uses any vocabulary from the table or the setting."""
    return any(word.lower() in GAME_WORDS for word in _WORD.findall(text or ''))

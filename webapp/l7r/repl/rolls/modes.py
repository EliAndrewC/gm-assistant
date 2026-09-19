"""What each skill's roll MAY be, so `annotate()` stops asking what it already knows.

Feature 207. Until now every roll was asked the same question - open, contested,
discard, or open with a bonus - and for most skills most of those answers are
impossible. The GM (2026-09-19): *"some rolls are always open rolls ... the
pontificate school knack may only be made as an open roll. Athletics is also always
open no matter what. Many other rolls can only be made contested. For example,
manipulation is always a contested roll, and therefore there is literally no other
option that should be selectable."*

EVERY NAME IN THE VOCABULARY HAS EXACTLY ONE MODE, and
`tests/test_rolls_modes.py` reads the rules file and fails when one has none. That
is deliberate: a skill added to the rules is a DECISION about how it is rolled, and
a silent default would make the decision for the GM. Rows here state that decision,
which is why this table is written out rather than derived.
"""

from __future__ import annotations

from typing import Literal

Mode = Literal[
    'exempt',
    'automatic',
    'always_open',
    'default_open',
    'contested_required',
    'contested_maybe_unopposed',
    'hidden',
    'full_menu',
]

#: Never annotated at all (feature 202): presumed to be introductions.
EXEMPT = ('etiquette',)

#: Feature 208: takes effect by itself and is never offered by `annotate()` - *"they
#: do not even need to be annotated. They can just automatically begin their
#: effect."* Written bare, in sequence (`rules.WRITTEN_BARE` is derived from this).
AUTOMATIC = ('oppose knowledge', 'oppose social')

#: May ONLY be open. Pontificate's own rule says so - *"when making an uncontested
#: roll"* (`rules/05-school_knacks.md`) - and the GM ruled the same for athletics.
ALWAYS_OPEN = ('athletics', 'pontificate')

#: *"almost always rolled open, but which can technically be rolled contested"* -
#: someone arguing the point with an NPC. Open arrives SELECTED and can be undone.
#: Investigation joined on the GM's second message: *"it is rare for a player to
#: roll investigation in a conversation and not have it be open."*
DEFAULT_OPEN = (
    'bragging',
    'intimidation',
    'culture',
    'heraldry',
    'history',
    'underworld',
    'investigation',
)

#: Always contested AND always against a real number: *"Even if the person doesn't
#: have tact, even if they are completely overwhelmed and outclassed, there is always
#: a roll registered because the amount that you exceed the manipulation roll by
#: their tact roll affects the outcome."*
CONTESTED_REQUIRED = ('manipulation',)

#: Always contested, but often with nobody on the other side: *"a sneaking roll to
#: blend into a crowd is always rolled contested against the investigation of anyone
#: who can possibly observe you. However, in many cases, there is no specific NPC who
#: is actually watching."* The rules were clarified to say so the same day.
CONTESTED_MAYBE_UNOPPOSED = ('sneaking',)

#: Contested against a roll the players must never see. Interrogation since feature
#: 206; acting because *"the NPC might see through their disguise and then not
#: reveal that."* The public line carries an OUTCOME instead of the other side.
HIDDEN = ('interrogation', 'acting')

#: Everything else keeps the o/c/d/ob question. Sincerity and tact are here ON
#: PURPOSE though they sit in the fixed pairings: *"while it is true that
#: interrogation always contests sincerity, some sincerity rolls are open. Similarly
#: ... some tact rolls are open."* The combat skills and the remaining knacks are
#: here because nothing was ruled about them.
FULL_MENU = (
    'sincerity',
    'tact',
    'law',
    'precepts',
    'strategy',
    'commerce',
    'attack',
    'parry',
    'commune',
    'counterattack',
    'feint',
    'iaijutsu',
    'lunge',
    'presence',
    'spellcasting',
)

_GROUPS: tuple[tuple[Mode, tuple[str, ...]], ...] = (
    ('exempt', EXEMPT),
    ('automatic', AUTOMATIC),
    ('always_open', ALWAYS_OPEN),
    ('default_open', DEFAULT_OPEN),
    ('contested_required', CONTESTED_REQUIRED),
    ('contested_maybe_unopposed', CONTESTED_MAYBE_UNOPPOSED),
    ('hidden', HIDDEN),
    ('full_menu', FULL_MENU),
)

#: skill -> mode. DERIVED from the groups above, so a skill is listed once.
MODES: dict[str, Mode] = {skill: mode for mode, skills in _GROUPS for skill in skills}

#: What a hidden-opposition roll GOT the players, when the GM says nothing else.
#: The interrogation default is written whether the NPC was truthful, lied well, or
#: was never rolled for - *"it can be difficult to tell whether the result that you
#: are getting is because someone is being honest or because they are faking
#: sincerity"* - so the record must not tell them apart either. The GM's wording
#: for both was "something like"; each is one constant.
DEFAULT_OUTCOME = {
    'interrogation': 'nothing hidden detected',
    'acting': 'no signs of the persona being seen through',
}

#: What someone gets who is not actively rolling against a manipulation: *"that is
#: kind of the default value that someone gets if they are not actively making a
#: roll to contest something."* Choosing it presumes a tact of ZERO.
UNROLLED_TOTAL = 15

#: Feature 209. How an NPC may APPEAR after an intimidation roll, mildest first. The
#: GM (2026-09-19): *"someone can either be stoic, unsettled, rattled, or shaken."*
#: The words are the GM's; the rules name three hidden thresholds and no states,
#: which makes four. There is NO default among them: the thresholds are set per scene
#: and never told to the players, so the number cannot say which one it was.
APPEARANCES = ('stoic', 'unsettled', 'rattled', 'shaken')


def mode_of(skill: str) -> Mode:
    """The mode of `skill`. An unknown name gets the full menu - asking everything
    is the safe failure, and the vocabulary test is what keeps this from hiding a
    skill the table forgot."""
    return MODES.get(skill.lower(), 'full_menu')


def default_outcome(skill: str) -> str:
    """The outcome written for a hidden-opposition roll the GM said nothing about."""
    return DEFAULT_OUTCOME.get(skill.lower(), '')

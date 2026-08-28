"""The canonical L7R skill vocabulary.

The list is READ from the rules rather than copied into this file. The GM's rules
repository is the canonical statement of every mechanic (`CLAUDE.md`: a question
about how a skill works is answered there, by grep, before anything is built on
it), and a copied list is a second source that goes stale silently - a skill
renamed in the rules would leave this module confidently wrong with nothing
failing.

Players abbreviate. The corpus has `24 eti` and `22 eti` alongside the full
`38 Etiquette @3`, so a prefix that matches exactly one skill resolves to it. A
prefix that matches several is REPORTED, never guessed - the same discipline the
`@N` threshold uses in `parse.py`, and for the same reason: a wrong skill silently
attributes a roll to the wrong line in the GM's notes, which is worse than no line
at all.
"""

from __future__ import annotations

import re
from pathlib import Path

#: The rules repository, bind-mounted from the host. See `/gm-assistant/README.md`.
RULES_PATH = Path('/host-l7r-repo/rules/02-skills.md')

#: Combat skills, which live in a different rules file (`03-combat.md`): "All
#: characters begin with two advanced skills at 1: attack (which uses Fire) and
#: parry (which uses Air)." They are listed there in prose rather than in a
#: bulleted Skill List, so they are named here instead of parsed.
COMBAT_SKILLS: tuple[str, ...] = ('attack', 'parry')

_SECTION = re.compile(r'^## Skill List$(.*?)^## ', re.M | re.S)
_BULLET = re.compile(r'^- ([A-Za-z][A-Za-z ]*?)\s*$', re.M)


class UnknownSkill(ValueError):
    """The word is not a skill, or not enough of one to be sure."""


class AmbiguousSkill(ValueError):
    """A prefix that matches more than one skill. Carries the candidates."""

    def __init__(self, word: str, candidates: tuple[str, ...]) -> None:
        self.word = word
        self.candidates = candidates
        super().__init__(
            f'{word!r} could be any of: {", ".join(candidates)}. '
            'Name it in full - guessing would file the roll under the wrong skill.'
        )


def load_skills(path: Path = RULES_PATH) -> tuple[str, ...]:
    """Every skill name, lowercased, in rules order, with the combat skills appended.

    Reads the "## Skill List" section of the rules. The section lists basic skills
    in lower case and advanced ones capitalized; the distinction is a rules concept
    that does not matter here, so everything is lowercased for matching.
    """
    text = path.read_text(encoding='utf-8')
    section = _SECTION.search(text)
    if section is None:
        raise UnknownSkill(f'no "## Skill List" section in {path}')
    found = tuple(m.group(1).strip().lower() for m in _BULLET.finditer(section.group(1)))
    if not found:
        raise UnknownSkill(f'the "## Skill List" section of {path} lists no skills')
    return found + COMBAT_SKILLS


def match_skill(word: str, vocabulary: tuple[str, ...]) -> str:
    """Resolve a player's spelling to a canonical skill name.

    Exact match wins outright, so a skill that is a prefix of another (none today,
    but the rules may grow one) can always be named. Otherwise a prefix must be
    unambiguous.

    Raises `UnknownSkill` when nothing matches and `AmbiguousSkill` when several do.
    """
    candidate = word.strip().lower()
    if not candidate:
        raise UnknownSkill('empty skill name')
    if candidate in vocabulary:
        return candidate
    hits = tuple(s for s in vocabulary if s.startswith(candidate))
    if len(hits) == 1:
        return hits[0]
    if hits:
        raise AmbiguousSkill(word, hits)
    raise UnknownSkill(f'{word!r} is not a skill in the rules')


def is_skill(word: str, vocabulary: tuple[str, ...]) -> bool:
    """True when `word` resolves to exactly one skill.

    The parser's guard: a number is only a roll when a skill name sits next to it.
    Ambiguous and unknown both answer False here - neither is something to record.
    """
    try:
        match_skill(word, vocabulary)
    except UnknownSkill, AmbiguousSkill:
        return False
    return True

"""Name-similarity rules shared by the chargen engine and the ``/name`` skill.

ONE implementation (feature 200, FR-006): the skill's ``similarity.py`` is a shim
that re-exports these. Two rules live here:

- ``is_too_similar`` - the LOOSE campaign-wide rule: a candidate is rejected if
  it is within edit distance 1 of a used name, or one is a prefix of the other
  (Chiyo/Chiyoko).
- ``set_conflict`` - the STRICT within-set rule (GM 2026-07-20): names introduced
  together must not share a first letter, rhyme, or be within one letter.
"""

from __future__ import annotations

from collections.abc import Iterable

#: Minimum shared trailing run for two names to count as rhyming. The "-ko"
#: case gets its own, higher threshold - see :func:`rhymes` for why.
RHYME_MIN_TAIL = 3
KO_RHYME_MIN_TAIL = 4


def edit_distance(a: str, b: str) -> int:
    """Levenshtein edit distance between two strings, case-insensitive."""
    a, b = a.lower(), b.lower()
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
    return prev[-1]


def is_too_similar(candidate: str, existing_names: Iterable[str]) -> bool:
    """True if ``candidate`` is too close to ANY of ``existing_names``.

    Criteria: exact match; edit distance of 1 (one letter changed, added or
    removed); or one name is a longer version of the other (Chiyo/Chiyoko).
    """
    c = candidate.lower()
    for name in existing_names:
        n = name.lower()
        if c == n or edit_distance(c, n) <= 1 or c.startswith(n) or n.startswith(c):
            return True
    return False


def rhymes(a: str, b: str) -> bool:
    """Heuristic rhyme check for romanized names.

    Two names count as rhyming when they share a trailing run of 3+ letters
    (Hitomi/Naomi). In romaji that captures the final syllable-plus-vowel
    cluster, which is what makes two Japanese names land on the same beat when
    spoken. A 2-letter shared tail (Kazuki/Hideki) is below the confusion
    threshold - most names end in one of a handful of standard suffixes, so 2
    letters would reject nearly everything.

    THE "-ko" EXCEPTION (GM rule, 2026-07-25). When BOTH names end in "ko",
    the threshold rises to 4. "-ko" is by far the most common ending for
    female given names, so at a 3-letter tail the entire "-ko" space collapses
    into just five rhyme classes - "-ako", "-eko", "-iko", "-oko", "-uko" -
    and every "-ko" name conflicts with every other one sharing its preceding
    vowel. In practice that rejected roughly a fifth of the female pool per
    name already chosen, and a set with five women in it could exhaust the
    100-name pool outright (observed 2026-07-25: zero candidates remained for
    a sixth). Requiring 4 letters forces the shared tail past the vowel to the
    consonant opening the penultimate syllable - i.e. the last TWO syllables
    must match, not merely the "ko". So Yuriko/Mariko and Michiko/Sachiko
    still rhyme, while Yuriko/Reiko and Haruko/Yasuko no longer do.

    This is purely a relaxation: it can only ever turn a True into a False, so
    no set of names that was valid under the old rule becomes invalid.
    """
    a, b = a.lower(), b.lower()
    i = 0
    while i < min(len(a), len(b)) and a[-1 - i] == b[-1 - i]:
        i += 1
    both_end_in_ko = a.endswith('ko') and b.endswith('ko')
    return i >= (KO_RHYME_MIN_TAIL if both_end_in_ko else RHYME_MIN_TAIL)


def set_conflict(a: str, b: str) -> bool:
    """True if two names are too similar to coexist in ONE generated set.

    GM rule (2026-07-20): when a batch of characters is generated together (a
    team of NPCs, a family, several names from one request), players confuse
    similar names at the table - Tolkien's Sauron/Saruman problem. Within a
    set, two names conflict if ANY of: same first letter; they rhyme; within
    edit distance 1 or one extends the other.

    Deliberately stricter than :func:`is_too_similar`, which guards a candidate
    against the WHOLE campaign cast: applied campaign-wide, the first-letter
    rule would exhaust the alphabet in two dozen NPCs.
    """
    if a[:1].lower() == b[:1].lower():
        return True
    return is_too_similar(a, [b]) or rhymes(a, b)

#!/usr/bin/env python3
"""Name similarity checker for filtering out names too close to existing campaign names."""


def edit_distance(a, b):
    """Compute Levenshtein edit distance between two strings."""
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


def is_too_similar(candidate, existing_names):
    """Check if a candidate name is too similar to any existing name.

    Criteria:
    - Edit distance of 1 (differ by a single letter change/add/remove)
    - One name is a longer version of another (substring at start)
    """
    c = candidate.lower()
    for name in existing_names:
        n = name.lower()
        if c == n:
            return True
        if edit_distance(c, n) <= 1:
            return True
        # One is a prefix of the other (e.g., Chiyo/Chiyoko)
        if c.startswith(n) or n.startswith(c):
            return True
    return False


def rhymes(a, b):
    """Heuristic rhyme check for romanized names.

    Two names count as rhyming when they share a trailing run of 3+ letters
    (Hitomi/Naomi, Haruko/Yasuko). In romaji that captures the final
    syllable-plus-vowel cluster, which is what makes two Japanese names land
    on the same beat when spoken. A 2-letter shared tail (Kazuki/Hideki) is
    below the confusion threshold - most female names end in one of a handful
    of standard suffixes, so 2 letters would reject nearly everything.
    """
    a, b = a.lower(), b.lower()
    i = 0
    while i < min(len(a), len(b)) and a[-1 - i] == b[-1 - i]:
        i += 1
    return i >= 3


def set_conflict(a, b):
    """Check whether two names are too similar to coexist in ONE generated set.

    GM rule (2026-07-20): when a batch of characters is generated together
    (a team of NPCs, a family, multiple names from one request), players
    confuse similar names at the table - Tolkien's Sauron/Saruman problem.
    Within a set, two names conflict if ANY of:
    - they start with the same letter
    - they rhyme (see rhymes())
    - they are within edit distance 1 of each other, or one extends the other

    This is deliberately stricter than is_too_similar(), which guards a
    candidate against the WHOLE campaign cast: applied campaign-wide, the
    first-letter rule would exhaust the alphabet in two dozen NPCs. The set
    rule only applies among names introduced together.
    """
    a_l, b_l = a.lower(), b.lower()
    if a_l[0] == b_l[0]:
        return True
    if is_too_similar(a, [b]):
        return True
    return rhymes(a, b)


if __name__ == "__main__":
    # Quick test
    test_names = ["Chiyo", "Akari"]
    print(f"Chiyo vs Chiyoko: {is_too_similar('Chiyoko', test_names)}")  # True
    print(f"Akemi vs Akari: {is_too_similar('Akemi', test_names)}")  # False (edit dist 2)
    print(f"Chiyu vs Chiyo: {is_too_similar('Chiyu', test_names)}")  # True (edit dist 1)
    print(f"Haruka vs Akari: {is_too_similar('Haruka', test_names)}")  # False
    print(f"Naomi vs Hitomi rhyme: {rhymes('Naomi', 'Hitomi')}")  # True
    print(f"Kaito vs Kenji set-conflict: {set_conflict('Kaito', 'Kenji')}")  # True (same initial)

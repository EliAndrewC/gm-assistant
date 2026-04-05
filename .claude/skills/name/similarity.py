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


if __name__ == "__main__":
    # Quick test
    test_names = ["Chiyo", "Akari"]
    print(f"Chiyo vs Chiyoko: {is_too_similar('Chiyoko', test_names)}")  # True
    print(f"Akemi vs Akari: {is_too_similar('Akemi', test_names)}")  # False (edit dist 2)
    print(f"Chiyu vs Chiyo: {is_too_similar('Chiyu', test_names)}")  # True (edit dist 1)
    print(f"Haruka vs Akari: {is_too_similar('Haruka', test_names)}")  # False

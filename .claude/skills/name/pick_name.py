#!/usr/bin/env python3
"""Pick names from the pre-generated pool, filtering out names too similar to campaign names.

Usage:
    python3 pick_name.py [args...]

    Args can be separate tokens or concatenated shorthand:
      Gender:  male, female, m, f
      Caste:   peasant, p
      Count:   any number, or x<N> (e.g. x3)

    Concatenated forms work: pf3, 3mp, fm, x5p, etc.
    Order doesn't matter. If gender is omitted, picks randomly.
    If peasant is not specified, picks from the full pool.
    If count is omitted, picks 1.
"""

import json
import os
import random
import sys

from similarity import is_too_similar

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
MALE_POOL = os.path.join(SKILL_DIR, "pool-male.jsonl")
FEMALE_POOL = os.path.join(SKILL_DIR, "pool-female.jsonl")
CAMPAIGN_NAMES = os.path.join(SKILL_DIR, "campaign-names.txt")


def load_pool(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_campaign_names():
    if not os.path.exists(CAMPAIGN_NAMES):
        return []
    with open(CAMPAIGN_NAMES) as f:
        return [line.strip() for line in f if line.strip()]


def pick(gender, count, peasant=False):
    campaign_names = load_campaign_names()

    results = []
    for _ in range(count):
        # Determine gender for this name
        if gender is None:
            g = random.choice(["male", "female"])
        else:
            g = gender

        pool_path = MALE_POOL if g == "male" else FEMALE_POOL
        pool = load_pool(pool_path)

        # Filter to peasant-suitable names if requested
        if peasant:
            pool = [e for e in pool if e.get("peasant", False)]

        if not pool:
            label = f"peasant {g}" if peasant else g
            print(json.dumps({"error": f"No {label} names in pool. Run pool generation first."}))
            continue

        # Filter out names too similar to campaign names or already-picked names
        picked_names = [r["name"] for r in results]
        all_excluded = campaign_names + picked_names

        valid = [entry for entry in pool if not is_too_similar(entry["name"], all_excluded)]

        if not valid:
            print(json.dumps({"error": f"No valid {g} names remain after similarity filtering."}))
            continue

        # Pick randomly
        chosen = random.choice(valid)
        results.append(chosen)

    # Output results
    for i, r in enumerate(results):
        if i > 0:
            print("\n---\n")
        print(f"**{r['name']}** — {r['explanation']}")
        if r.get("notes"):
            print(f"\n*Notes: {r['notes']}*")


def parse_args(argv):
    """Parse args supporting both full words and concatenated shorthand.

    Examples: male 3, f peasant, pf3, 3mp, x5, female x3 peasant
    """
    gender = None
    count = 1
    peasant = False

    for arg in argv:
        # Try full words first
        if arg in ("male", "female"):
            gender = arg
            continue
        if arg == "peasant":
            peasant = True
            continue

        # Strip optional x prefix for count (e.g. x3)
        stripped = arg.lstrip("x") if arg.startswith("x") and arg[1:].isdigit() else None
        if stripped and stripped.isdigit():
            count = int(stripped)
            continue

        # Pure number
        if arg.isdigit():
            count = int(arg)
            continue

        # Concatenated shorthand: scan character by character
        i = 0
        while i < len(arg):
            c = arg[i].lower()
            if c == "m":
                gender = "male"
                i += 1
            elif c == "f":
                gender = "female"
                i += 1
            elif c == "p":
                peasant = True
                i += 1
            elif c == "x":
                # x followed by digits
                i += 1
                num = ""
                while i < len(arg) and arg[i].isdigit():
                    num += arg[i]
                    i += 1
                if num:
                    count = int(num)
            elif c.isdigit():
                num = ""
                while i < len(arg) and arg[i].isdigit():
                    num += arg[i]
                    i += 1
                count = int(num)
            else:
                i += 1  # skip unknown chars

    return gender, count, peasant


if __name__ == "__main__":
    gender, count, peasant = parse_args(sys.argv[1:])
    pick(gender, count, peasant=peasant)

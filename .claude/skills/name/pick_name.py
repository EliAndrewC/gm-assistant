#!/usr/bin/env python3
"""Pick names from the pre-generated pool, filtering out names too similar to campaign names.

Usage:
    python3 pick_name.py [male|female] [peasant] [N]

    If gender is omitted, picks randomly.
    If peasant is specified, only picks from peasant-suitable names.
    If N is omitted, picks 1.
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
    for r in results:
        print(json.dumps(r))


if __name__ == "__main__":
    gender = None
    count = 1
    peasant = False

    for arg in sys.argv[1:]:
        if arg in ("male", "female"):
            gender = arg
        elif arg == "peasant":
            peasant = True
        elif arg.isdigit():
            count = int(arg)

    pick(gender, count, peasant=peasant)

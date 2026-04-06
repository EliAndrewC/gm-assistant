#!/usr/bin/env python3
"""Remove names that conflict with campaign names or with each other across both pools.
For each conflicting pair, remove the second one encountered."""

import json
import os
import sys

from similarity import is_too_similar

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))


def load_pool(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def save_pool(path, entries):
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def load_campaign_names():
    path = os.path.join(SKILL_DIR, "campaign-names.txt")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]


def fix():
    campaign_names = load_campaign_names()

    male_path = os.path.join(SKILL_DIR, "pool-male.jsonl")
    female_path = os.path.join(SKILL_DIR, "pool-female.jsonl")
    male_pool = load_pool(male_path)
    female_pool = load_pool(female_path)

    # Process both pools together to catch cross-pool conflicts
    # Male pool is processed first, then female pool checks against both campaign + accepted male names
    accepted_names = list(campaign_names)
    final_male = []
    final_female = []

    for entry in male_pool:
        if is_too_similar(entry["name"], accepted_names):
            print(f"REMOVING male: {entry['name']}")
        else:
            final_male.append(entry)
            accepted_names.append(entry["name"])

    for entry in female_pool:
        if is_too_similar(entry["name"], accepted_names):
            print(f"REMOVING female: {entry['name']}")
        else:
            final_female.append(entry)
            accepted_names.append(entry["name"])

    save_pool(male_path, final_male)
    save_pool(female_path, final_female)

    print(f"\nmale: {len(male_pool)} -> {len(final_male)} ({len(male_pool) - len(final_male)} removed)")
    print(f"female: {len(female_pool)} -> {len(final_female)} ({len(female_pool) - len(final_female)} removed)")
    print("\nDone. Run validate_pool.py to confirm.")


if __name__ == "__main__":
    fix()

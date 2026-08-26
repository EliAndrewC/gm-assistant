#!/usr/bin/env python3
"""Validate the name pools: no duplicates, no similarities to campaign names or to each other."""

import json
import os
import sys

import campaign
from similarity import is_too_similar

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))


def load_pool(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_campaign_names():
    """Given names on the campaign roster, from the campaign cache (feature 200).
    Offline read - the cache is refreshed by pick_name.py / character creation."""
    return campaign.used_names(refresh=False)


def validate():
    campaign_names = load_campaign_names()
    male_pool = load_pool(os.path.join(SKILL_DIR, "pool-male.jsonl"))
    female_pool = load_pool(os.path.join(SKILL_DIR, "pool-female.jsonl"))
    all_pool = male_pool + female_pool
    all_names = [e["name"] for e in all_pool]

    errors = []

    # Check for exact duplicates within the pool
    seen = set()
    for name in all_names:
        if name.lower() in seen:
            errors.append(f"DUPLICATE in pool: {name}")
        seen.add(name.lower())

    # Pool names in use in the campaign are INFORMATIONAL, not errors (GM
    # 2026-08-26): the pool is never depleted by use. pick_name.py and the
    # chargen engine exclude them at pick time (roster cache plus
    # used-names-extra.txt); they stay in the pool for the next campaign.
    in_use = [e for e in all_pool if is_too_similar(e["name"], campaign_names)]
    for entry in in_use:
        print(f"  IN USE (kept, excluded at pick time): {entry['name']} ({entry['gender']})")

    # Check each pool name against all OTHER pool names
    for i, entry in enumerate(all_pool):
        others = [e["name"] for j, e in enumerate(all_pool) if j != i]
        if is_too_similar(entry["name"], others):
            # Find which one it's similar to
            for other in others:
                if entry["name"].lower() == other.lower():
                    continue
                from similarity import edit_distance

                ed = edit_distance(entry["name"], other)
                if (
                    ed <= 1
                    or entry["name"].lower().startswith(other.lower())
                    or other.lower().startswith(entry["name"].lower())
                ):
                    errors.append(
                        f"TOO SIMILAR IN POOL: {entry['name']} <-> {other} (edit_dist={ed}, prefix={entry['name'].lower().startswith(other.lower()) or other.lower().startswith(entry['name'].lower())})"
                    )
                    break

    # Summary
    print(f"Campaign names: {len(campaign_names)}")
    print(f"Male pool: {len(male_pool)}")
    print(f"Female pool: {len(female_pool)}")
    print(f"Total pool: {len(all_pool)}")
    print()

    if errors:
        print(f"ERRORS FOUND: {len(errors)}")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print(
            "ALL CHECKS PASSED - no duplicates, no similarities to campaign names or between pool names."
        )


if __name__ == "__main__":
    validate()

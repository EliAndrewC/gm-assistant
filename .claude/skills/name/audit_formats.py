#!/usr/bin/env python3
"""Report-only audit of explanation-format suitability and balance (GM 2026-08-26).

Some of the 20 formats make a factual claim about the name (two kanji spellings,
a deity, a natural element, two elements); those may only sit on names for which
the claim is true. The rest narrate a Rokugani origin and suit any name, with a
PREFERENCE that constructed names use them. This script reads the pool and prints
(1) entries whose current format violates a hard rule, (2) per-gender global
format counts, and (3) initials where one format dominates. It never writes.
Signals are read from each entry's own ``notes`` (kanji present, "recorded in
kana", an alternate spelling mentioned, a nature word) and ``provenance``.
"""

from __future__ import annotations

import collections
import json
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
KANJI = re.compile(r"[一-鿿々]")
KANA_ONLY = re.compile(
    r"(recorded|written|wrote|register)[^.]{0,60}\b(in )?(hira|kata)?kana\b|kana-only|kana only|in kana|no kanji",
    re.I,
)
ALT = re.compile(
    r"(also written|alternat(e|ive)(ly)? (spelling|kanji|written)|other (common )?(kanji|spellings?)"
    r"|can (also )?be written|variant(s)? (spelling|kanji)|two (different )?kanji"
    r"|\bor [一-鿿々]{1,3}\b|[一-鿿々]{1,4} ?/ ?[一-鿿々]{1,4}|either [一-鿿々])",
    re.I,
)
NATURE = re.compile(
    r"\b(plant|flower|tree|blossom|pine|plum|chrysanthemum|bamboo|willow|cherry|orchid|lotus|grass"
    r"|leaf|leaves|moon|snow|rain|cloud|sea|river|bay|shore|rock|stone|wave|tide|dew|wind|star|sun\b"
    r"|dawn|autumn|winter|summer|bird|crane|warbler|plover|butterfly|carp|shrimp|fish|deer|tiger"
    r"|bear|dragon|fruit|rice|millet|seaweed|silk|cotton|jewel|jade|pearl|silver|gold)\b",
    re.I,
)
ORIGIN = {7, 8, 11, 13, 17, 18, 19, 20}
MEANING = {1, 2, 3, 5, 6, 9, 10, 12, 14, 16}


def signals(entry: dict) -> dict:
    notes = entry.get("notes", "")
    return {
        "prov": entry.get("provenance", "historical"),
        "kana": bool(KANA_ONLY.search(notes)),
        "alt": bool(ALT.search(notes)),
        "nature": bool(NATURE.search(notes)),
        "nk": len(set(KANJI.findall(notes))),
    }


def allowed(entry: dict) -> set[int]:
    """Formats the entry may carry under the hard rules."""
    s = signals(entry)
    ok = set(range(1, 21))
    if not (s["alt"] or s["kana"]):
        ok.discard(4)
    if s["prov"] == "historical" and not s["kana"]:
        ok.discard(8)
    if not s["nature"]:
        ok.discard(15)
    if (s["nk"] < 2 and not s["kana"]) or (s["kana"] and s["prov"] == "historical"):
        ok -= {10, 16}
    return ok


def preferred(entry: dict) -> set[int]:
    s = signals(entry)
    if s["prov"] == "invented":
        return ORIGIN
    if s["prov"] == "historical" and s["kana"]:
        return ORIGIN | {4, 14, 9}
    return MEANING | {15}


def audit(rows: list[dict]) -> dict:
    """Pure report over one gender's entries."""
    violations = [(r["name"], r["format"]) for r in rows if r["format"] not in allowed(r)]
    by_format = collections.Counter(r["format"] for r in rows)
    by_letter: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in rows:
        by_letter[r["name"][0]][r["format"]] += 1
    lopsided = []
    for letter, counts in sorted(by_letter.items()):
        fmt, top = counts.most_common(1)[0]
        n = sum(counts.values())
        if top > max(2, n / 6):
            lopsided.append((letter, fmt, top, n))
    on_pref = sum(r["format"] in preferred(r) for r in rows)
    return {
        "violations": violations,
        "by_format": by_format,
        "lopsided": lopsided,
        "on_preferred": on_pref,
        "n": len(rows),
    }


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> int:
    bad = 0
    for gender in ("male", "female"):
        rows = load(os.path.join(SKILL_DIR, f"pool-{gender}.jsonl"))
        rep = audit(rows)
        print(f"{gender}: {rep['n']} entries, {rep['on_preferred']} on a preferred format")
        print("  formats:", [rep["by_format"][i] for i in range(1, 21)])
        for name, fmt in rep["violations"]:
            print(f"  VIOLATION: {name} on format {fmt} (allowed {sorted(allowed(next(r for r in rows if r['name'] == name)))})")
        for letter, fmt, top, n in rep["lopsided"]:
            print(f"  LOPSIDED: {letter} has {top} of {n} on format {fmt}")
        bad += len(rep["violations"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

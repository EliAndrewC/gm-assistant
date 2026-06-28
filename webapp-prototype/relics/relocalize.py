"""De-localize relic frontmatter:

- Add a `clan` field (slug or "any") based on clan family names in named_entity
- Rewrite `temple_suggestion` (rename → `temple`) to remove specific cities
- Leave prose body unchanged here; prose edits done separately
"""

import re
import sys
from pathlib import Path

POOL = Path("/gm-assistant/.claude/skills/relic/pool")

# Maps clan slug → family/lineage surnames associated with that clan.
# Used to detect clan from named_entity.
CLAN_FAMILIES = {
    "crab":     ["Hida", "Hiruma", "Kuni", "Yasuki", "Toritaka", "Kaiu"],
    "crane":    ["Doji", "Kakita", "Daidoji", "Asahina"],
    "dragon":   ["Mirumoto", "Kitsuki", "Togashi", "Agasha"],
    "fox":      ["Kitsune", "Hokke", "Toke", "Saike", "Nanke"],
    "lion":     ["Akodo", "Matsu", "Ikoma", "Kitsu", "Damasu"],
    "phoenix":  ["Isawa", "Shiba", "Asako"],
    "scorpion": ["Bayushi", "Shosuro", "Soshi", "Yogo", "Michio"],
    "unicorn":  ["Shinjo", "Ide", "Iuchi", "Otaku", "Utaku", "Moto"],
    "mantis":   ["Yoritomo", "Moshi", "Shione"],
    "sparrow":  ["Suzume"],
    "wasp":     ["Tsuruchi"],
    "dragonfly":["Tonbo"],
    "hare":     ["Usagi"],
}

FORTUNES = {
    "benten": "Benten",
    "bishamon": "Bishamon",
    "daikoku": "Daikoku",
    "ebisu": "Ebisu",
    "fukurokujin": "Fukurokujin",
    "hotei": "Hotei",
    "jurojin": "Jurojin",
}


def detect_clans(named_entity: str, prose: str) -> list:
    """Return a list of detected clan slugs from named_entity and prose."""
    hits = []
    haystack = named_entity + "\n" + prose
    for clan, families in CLAN_FAMILIES.items():
        for fam in families:
            # word-boundary match so "Hidaka" doesn't match "Hida"
            if re.search(r"\b" + re.escape(fam) + r"\b", haystack):
                if clan not in hits:
                    hits.append(clan)
                break
    return hits


def temple_field(clan: str, fortune: str) -> str:
    """Generate a generic temple field given clan tag and fortune."""
    fortune_name = FORTUNES[fortune]
    if clan == "any":
        return f"a temple of {fortune_name}, in any city of the Empire"
    clan_title = clan.capitalize()
    return f"a temple of {fortune_name} in {clan_title} lands"


def parse_file(path: Path) -> tuple:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError(f"No frontmatter in {path}")
    fm_raw, body = m.groups()
    return fm_raw, body.lstrip("\n")


def main(dry_run: bool = False):
    changes = []
    for fortune_slug in sorted(FORTUNES.keys()):
        fortune_dir = POOL / fortune_slug
        for f in sorted(fortune_dir.glob("*.md")):
            fm_raw, body = parse_file(f)

            # Parse current frontmatter
            fields = {}
            for line in fm_raw.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    fields[k.strip()] = v.strip()

            # Detect clans
            named = fields.get("named_entity", "")
            clans = detect_clans(named, body)

            if not clans:
                clan_tag = "any"
            elif len(clans) == 1:
                clan_tag = clans[0]
            else:
                # multiple clans - pick the first one mentioned in named_entity
                # if any; else just first detected.
                in_named = [c for c in clans if any(
                    re.search(r"\b" + re.escape(fam) + r"\b", named)
                    for fam in CLAN_FAMILIES[c]
                )]
                clan_tag = in_named[0] if in_named else clans[0]

            new_temple = temple_field(clan_tag, fortune_slug)

            # Build new frontmatter, preserving field order with our additions
            new_lines = []
            seen_clan = False
            seen_temple = False
            for line in fm_raw.splitlines():
                if ":" not in line:
                    new_lines.append(line)
                    continue
                k, _, _ = line.partition(":")
                k = k.strip()
                if k == "fortune":
                    new_lines.append(line)
                    new_lines.append(f"clan: {clan_tag}")
                    seen_clan = True
                elif k == "temple_suggestion":
                    new_lines.append(f"temple: {new_temple}")
                    seen_temple = True
                else:
                    new_lines.append(line)
            if not seen_clan:
                # fortune wasn't in the file? Shouldn't happen but defensive.
                new_lines.append(f"clan: {clan_tag}")
            if not seen_temple:
                new_lines.append(f"temple: {new_temple}")

            new_fm = "\n".join(new_lines)
            new_text = "---\n" + new_fm + "\n---\n\n" + body

            changes.append({
                "path": str(f),
                "name": fields.get("name", "?"),
                "named_entity": named,
                "old_temple": fields.get("temple_suggestion", ""),
                "new_temple": new_temple,
                "clan": clan_tag,
                "detected": clans,
            })

            if not dry_run:
                f.write_text(new_text, encoding="utf-8")

    # Print summary
    by_clan = {}
    for c in changes:
        by_clan.setdefault(c["clan"], []).append(c)

    print(f"\n=== Summary: {len(changes)} relics ===\n")
    for clan in sorted(by_clan.keys()):
        rs = by_clan[clan]
        print(f"\n{clan.upper()} ({len(rs)}):")
        for c in rs:
            print(f"  - {c['name']}")
            print(f"      named_entity: {c['named_entity'][:70]}")
            if len(c['detected']) > 1:
                print(f"      detected:     {c['detected']} → picked '{c['clan']}'")


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    main(dry_run=dry)

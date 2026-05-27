"""Extract the 42 relics from /workspace/.claude/skills/relic/pool/ into a JSON bundle."""

import json
import os
import re
from pathlib import Path

POOL = Path("/workspace/.claude/skills/relic/pool")
OUT = Path(__file__).parent / "relics.json"

FORTUNES = {
    "benten": {"name": "Benten", "domain": "Fortune of romantic love", "kanji": "弁天"},
    "bishamon": {"name": "Bishamon", "domain": "Fortune of strength", "kanji": "毘沙門"},
    "daikoku": {"name": "Daikoku", "domain": "Fortune of wealth", "kanji": "大黒"},
    "ebisu": {"name": "Ebisu", "domain": "Fortune of honest work", "kanji": "恵比寿"},
    "fukurokujin": {"name": "Fukurokujin", "domain": "Fortune of wisdom and mercy", "kanji": "福禄寿"},
    "hotei": {"name": "Hotei", "domain": "Fortune of contentment", "kanji": "布袋"},
    "jurojin": {"name": "Jurojin", "domain": "Fortune of longevity", "kanji": "寿老人"},
}


def parse_relic(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError(f"No frontmatter in {path}")
    frontmatter_raw, body = m.groups()

    fm = {}
    for line in frontmatter_raw.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()

    slug = path.stem
    return {
        "slug": slug,
        "name": fm["name"],
        "japanese_romaji": fm.get("japanese_romaji", ""),
        "japanese_kanji": fm.get("japanese_kanji", ""),
        "fortune": fm["fortune"],
        "clan": fm.get("clan", "any"),
        "temple": fm.get("temple", fm.get("temple_suggestion", "")),
        "named_entity": fm.get("named_entity", ""),
        "relic_type": fm.get("relic_type", ""),
        "description": body.strip(),
    }


def main():
    relics = []
    for fortune_slug in sorted(FORTUNES.keys()):
        fortune_dir = POOL / fortune_slug
        files = sorted(fortune_dir.glob("*.md"))
        for f in files:
            relics.append(parse_relic(f))

    bundle = {
        "fortunes": FORTUNES,
        "relics": relics,
    }

    OUT.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    js_path = OUT.with_suffix(".js")
    js_path.write_text(
        "window.RELICS_BUNDLE = " + json.dumps(bundle, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {len(relics)} relics across {len(FORTUNES)} fortunes")
    print(f"  json: {OUT}")
    print(f"    js: {js_path}")


if __name__ == "__main__":
    main()

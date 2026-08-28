#!/usr/bin/env python3
"""Stage 2/3 of the Obsidian Portal L5R reading project: cache the public pages of the campaigns
the census marked crawlable (opted in, Legend of the Five Rings, not the GM's own), then build
the local index a session uses to summarize and search them.

  ./scripts/op_fetch_campaigns.py                  every crawlable campaign in census-62.json
  ./scripts/op_fetch_campaigns.py --slug hiddenway one campaign (must be on the exempt list)
  ./scripts/op_fetch_campaigns.py --index-only     rebuild opcache/opcrawl/index.{json,md}
  ./scripts/op_fetch_campaigns.py --search 'Scorpion'   grep the cached text

One request per --delay (default 61 s), a resumable manifest per campaign, and the same stop
rules as the census: a Cloudflare challenge or a robots.txt change ends the run. The same
principles apply - see webapp/l7r/opcrawl/__init__.py - and the cache is gitignored.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'webapp'))

from l7r.opcrawl.census import OUT_DIR, L5R_GAME_SYSTEM_ID, ConsentError  # noqa: E402
from l7r.opcrawl.fetch import crawl_campaign  # noqa: E402
from l7r.opcrawl.index import build_index, search  # noqa: E402


def crawlable_slugs(game_system_id: int) -> list[str]:
    path = OUT_DIR / f'census-{game_system_id}.json'
    if not path.exists():
        sys.exit(f'{path} missing - run scripts/op_consent_census.py first')
    census = json.loads(path.read_text())
    return sorted(
        r['slug']
        for r in census['rows']
        if r['game_system_id'] == game_system_id and not r['own'] and r['http_status'] == 200
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    parser.add_argument('--slug', action='append', help='crawl only these campaigns')
    parser.add_argument('--delay', type=float, default=61.0)
    parser.add_argument('--max-pages', type=int, default=None, help='per campaign, this run')
    parser.add_argument('--game-system-id', type=int, default=L5R_GAME_SYSTEM_ID)
    parser.add_argument('--index-only', action='store_true')
    parser.add_argument('--search', metavar='REGEX')
    args = parser.parse_args()
    if args.search:
        for hit in search(args.search):
            print(f'{hit.slug}: {hit.title}\n  {hit.url}\n  ...{hit.context}...')
        return 0
    if not args.index_only:
        slugs = args.slug or crawlable_slugs(args.game_system_id)
        print(f'{len(slugs)} campaign(s) to read at one request per {args.delay:g} s', flush=True)
        for slug in slugs:
            try:
                crawl_campaign(
                    slug,
                    delay=args.delay,
                    max_pages=args.max_pages,
                    progress=lambda s: print(s, flush=True),
                )
            except ConsentError as err:
                print(f'STOPPED: {err}', flush=True)
                break
    entries = build_index()
    print(f'index: {len(entries)} campaign(s) -> {OUT_DIR / "index.md"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

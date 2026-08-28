#!/usr/bin/env python3
"""Stage 2/3 of the Obsidian Portal L5R reading project: cache the public pages of the campaigns
the census marked crawlable (opted in, Legend of the Five Rings, not the GM's own), then build
the local index a session uses to summarize and search them.

  ./scripts/op_fetch_campaigns.py --summaries-only  ONE request each: what every campaign holds
  ./scripts/op_fetch_campaigns.py                   the pages themselves
  ./scripts/op_fetch_campaigns.py --slug hiddenway  one campaign (must be on the exempt list)
  ./scripts/op_fetch_campaigns.py --index-only      rebuild opcache/opcrawl/index.{json,md}
  ./scripts/op_fetch_campaigns.py --search Scorpion grep the cached text

The first request to any campaign is its own `content_summary.json`, which lists every public
wiki page, adventure-log post and character with title and tags. That list IS the crawl list -
nothing outside it is requested, and pages the owner marked GM-only are never asked for. One
request per --delay (default 21 s), a resumable manifest per campaign, and the census's stop
rules: a Cloudflare challenge or a robots.txt change ends the run. The same principles apply -
see webapp/l7r/opcrawl/__init__.py - and everything cached is gitignored.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'webapp'))

from l7r.opcrawl.census import (  # noqa: E402
    OUT_DIR,
    L5R_GAME_SYSTEM_ID,
    ConsentError,
    read_census,
)
from l7r.opcrawl.fetch import crawl_campaign  # noqa: E402
from l7r.opcrawl.index import build_index, search  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    parser.add_argument('--slug', action='append', help='crawl only these campaigns')
    parser.add_argument('--delay', type=float, default=21.0)
    parser.add_argument('--max-pages', type=int, default=None, help='per campaign, this run')
    parser.add_argument('--game-system-id', type=int, default=L5R_GAME_SYSTEM_ID)
    parser.add_argument(
        '--summaries-only',
        action='store_true',
        help="fetch each campaign's content_summary.json and stop - one request per campaign",
    )
    parser.add_argument('--index-only', action='store_true')
    parser.add_argument('--search', metavar='REGEX')
    args = parser.parse_args()

    if args.search:
        for hit in search(args.search):
            print(f'{hit.slug}: {hit.title}\n  {hit.url}\n  ...{hit.context}...')
        return 0

    census = read_census(args.game_system_id)
    names = {r.slug: r.name for r in census.rows} if census else {}
    stopped = False
    if not args.index_only:
        if args.slug:
            slugs = args.slug
        elif census is None:
            sys.exit('no census file - run scripts/op_consent_census.py first')
        else:
            slugs = [r.slug for r in census.crawlable]
        what = 'summary' if args.summaries_only else 'pages'
        print(f'{len(slugs)} campaign(s), {what}, one request per {args.delay:g} s', flush=True)
        for slug in slugs:
            try:
                crawl_campaign(
                    slug,
                    delay=args.delay,
                    max_pages=args.max_pages,
                    summary_only=args.summaries_only,
                    progress=lambda s: print(s, flush=True),
                )
            except (ConsentError, OSError) as err:
                print(f'STOPPED: {err}', flush=True)
                print('Progress is saved - rerun to resume where this left off.', flush=True)
                stopped = True
                break

    entries = build_index(names=names)
    print(f'\nindex: {len(entries)} campaign(s) -> {OUT_DIR / "index.md"}')
    for e in sorted(entries, key=lambda e: -e.total_available):
        published = ', '.join(f'{n} {k}s' for k, n in sorted(e.available.items())) or 'nothing'
        print(f'  {e.slug:40} {e.name[:40]:40} publishes {published}')
    return 1 if stopped else 0


if __name__ == '__main__':
    sys.exit(main())

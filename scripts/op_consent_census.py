#!/usr/bin/env python3
"""Census of Legend of the Five Rings campaigns on Obsidian Portal whose owners allow bots.

Reads robots.txt, the pre-human-check exempt list and the L5R browse listing at one request
per --delay (default 61 s; the floor is robots.txt's 20 s), never any other owner's campaign
pages, and writes the result under the gitignored webapp/opcache/opcrawl/. About 22 minutes.
See webapp/l7r/opcrawl/__init__.py.

  ./scripts/op_consent_census.py                 L5R (game_system_id=62), 61 s between requests
  ./scripts/op_consent_census.py --delay 121     slower still; --delay can never go below 20

Backoff ladder if Cloudflare still challenges (GM 2026-08-27): 61 -> 121 -> 301 -> 601 s, each one
just past a threshold a rate rule plausibly uses (1, 2, 5, 10 minutes). A challenge at 601 s
means the site is effectively blocking everything and the endeavor is scrapped, not slowed further.

Why the ladder only ever goes UP, and why a challenge is never solved or routed around: this tool
exists to comply rigorously with Obsidian Portal's documented wishes (robots.txt) and its apparent
ones (a challenge is a "no"), and with the wishes of the humans who host their campaigns there
(only owners who turned on "allow bots" are ever read). We aim to be responsible internet
denizens and to be above board in appearance as well as conduct - this code is public, and
anyone at Obsidian Portal reading it should find nothing to object to. The full statement is in
webapp/l7r/opcrawl/__init__.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'webapp'))

from l7r.opcrawl.census import L5R_GAME_SYSTEM_ID, run_census, summarize, write_census  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    parser.add_argument('--game-system-id', type=int, default=L5R_GAME_SYSTEM_ID)
    parser.add_argument(
        '--delay',
        type=float,
        default=61.0,
        help='seconds between requests; never below the robots.txt Crawl-delay (default 61)',
    )
    args = parser.parse_args()
    census = run_census(
        game_system_id=args.game_system_id,
        delay=args.delay,
        progress=lambda s: print(s, flush=True),
    )
    print(summarize(census, write_census(census)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
